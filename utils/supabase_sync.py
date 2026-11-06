"""Cloud backup / mirror to a (free) Supabase project.

How it works
------------
* The local SQLite database stays the "source of truth" — the POS keeps working
  offline exactly as before.
* `push_all()` copies every table to Supabase (Postgres) through its REST API:
  new/changed rows are upserted by `id`, and rows that were deleted locally are
  deleted in the cloud too, so the cloud is an exact mirror.
* `download_to_sqlite()` pulls everything back into a NEW .db file inside the
  backups folder. It then shows up in Settings → Backup and can be restored with
  the existing "double-click to restore" flow (e.g. after a PC crash).

Only the `requests` package is needed (already in requirements.txt).

Security
--------
Use the project's *secret* key (Dashboard → Project Settings → API Keys →
"sb_secret_..."), or the legacy `service_role` key. It is stored only in the
local database (settings table) and is never uploaded. Row Level Security is
enabled on every cloud table with no policies, so the public/publishable key
can read nothing. Never share the secret key or put it in the source code.
Passwords are uploaded only as salted hashes (see utils/auth.py).
"""
import sqlite3
from datetime import datetime

import requests

# ---------------------------------------------------------------------------
# Cloud schema — single source of truth for both the SQL file and the sync.
# Order matters only for readability (the cloud schema has no foreign keys,
# it is a mirror; integrity is enforced by the local SQLite database).
# ---------------------------------------------------------------------------
TEXT, INT, REAL, TS = "text", "bigint", "double precision", "timestamp"

TABLES = {
    "brands": {"id": INT, "name": TEXT, "phone": TEXT, "telegram": TEXT, "facebook": TEXT,
               "address": TEXT, "is_active": INT, "created_at": TS},
    "users": {"id": INT, "username": TEXT, "password": TEXT, "role": TEXT, "name": TEXT,
              "brand_id": INT, "active": INT, "created_at": TS},
    "customers": {"id": INT, "name": TEXT, "phone": TEXT, "address": TEXT, "facebook": TEXT,
                  "telegram": TEXT, "type": TEXT, "is_active": INT, "created_at": TS},
    "categories": {"id": INT, "name": TEXT, "description": TEXT, "is_active": INT, "created_at": TS},
    "taste": {"id": INT, "name": TEXT, "description": TEXT, "is_active": INT, "created_at": TS},
    "units": {"id": INT, "name": TEXT, "description": TEXT, "is_active": INT, "created_at": TS},
    "products": {"id": INT, "code": TEXT, "name": TEXT, "category_id": INT, "units_id": INT,
                 "price": REAL, "created_by": INT, "description": TEXT, "is_active": INT, "created_at": TS},
    "orders": {"id": INT, "order_number": TEXT, "customer_id": INT, "order_by": INT, "brand_id": INT,
               "total_amount": REAL, "delivery_fee": REAL, "discount": REAL, "status": TEXT,
               "payment_method": TEXT, "payment_status": TEXT, "paid_amount": REAL,
               "pickup_time": TEXT, "note": TEXT, "created_at": TS},
    "order_items": {"id": INT, "order_id": INT, "product_id": INT, "product_name": TEXT, "taste": TEXT,
                    "unit": TEXT, "quantity": REAL, "weight": REAL, "unit_price": REAL, "subtotal": REAL},
    "stock": {"id": INT, "product_id": INT, "brand_id": INT, "quantity": REAL, "updated_at": TS},
    "stock_movements": {"id": INT, "product_id": INT, "brand_id": INT, "movement_type": TEXT,
                        "quantity": REAL, "reason": TEXT, "reference_order_id": INT,
                        "created_by": INT, "created_at": TS},
    "stock_transfers": {"id": INT, "product_id": INT, "from_brand_id": INT, "to_brand_id": INT,
                        "quantity": REAL, "note": TEXT, "transferred_by": INT, "transferred_at": TS},
    "settings": {"id": INT, "key": TEXT, "value": TEXT, "updated_at": TS},
}

# Settings that must never leave this computer (credentials, sync bookkeeping).
PRIVATE_SETTING_PREFIXES = ("cloud_", "supabase_", "sheets_", "last_sync")

BATCH_SIZE = 500
PAGE_SIZE = 1000
TIMEOUT = 30


def schema_sql():
    """SQL to paste once into Supabase → SQL Editor → Run."""
    out = ["-- POS cloud mirror schema (generated from utils/supabase_sync.py)",
           "-- Safe to run more than once.", ""]
    for table, cols in TABLES.items():
        col_lines = []
        for col, typ in cols.items():
            col_lines.append(f'    "{col}" {typ}' + (" primary key" if col == "id" else ""))
        out.append(f'create table if not exists public."{table}" (\n' + ",\n".join(col_lines) + "\n);")
        out.append(f'alter table public."{table}" enable row level security;')
        out.append("")
    out.append("-- RLS is ON with no policies: the publishable/anon key can read nothing.")
    out.append("-- The secret (service_role) key used by the POS bypasses RLS but still needs table grants:")
    out.append("grant usage on schema public to service_role;")
    out.append("grant select, insert, update, delete on all tables in schema public to service_role;")
    out.append("")
    out.append("create index if not exists orders_created_at_idx on public.orders (created_at);")
    out.append("create index if not exists order_items_order_id_idx on public.order_items (order_id);")
    out.append("create index if not exists stock_movements_created_at_idx on public.stock_movements (created_at);")
    return "\n".join(out) + "\n"


class CloudSyncError(Exception):
    pass


# One Supabase project = one POS computer. A marker row in the cloud `settings`
# table (negative id, never used locally) records which installation owns it.
OWNER_ROW_ID = -100
OWNER_KEY = "__pos_owner"
OWNER_MESSAGE = ("This Supabase project is already used by ANOTHER POS computer, so syncing from here "
                 "would overwrite or delete its data. Sync was stopped - nothing was changed. "
                 "If this PC replaces the old one: use 'Download from Cloud' and restore that backup first. "
                 "If it is a separate shop/PC: create a new Supabase project for it.")


def local_install_id(db):
    """Random id of this POS installation (private setting, created once)."""
    import uuid
    conn = db.get_connection()
    try:
        row = conn.execute("SELECT value FROM settings WHERE key = 'cloud_install_id'").fetchone()
        if row and row[0]:
            return row[0]
        new_id = uuid.uuid4().hex
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('cloud_install_id', ?)", (new_id,))
        conn.commit()
        return new_id
    finally:
        conn.close()


PUBLIC_KEY_MESSAGE = "This is the PUBLIC key (publishable / anon) — it cannot upload. In Supabase: Project Settings > API Keys > Secret keys > copy the key starting with sb_secret_ (or Legacy API keys > service_role)."


def _jwt_role(key):
    """Role claim of a legacy JWT key ("anon" / "service_role"), or None."""
    import base64, json
    try:
        payload = key.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload)).get("role")
    except Exception:
        return None


def check_key_type(key):
    """Reject the public keys up front — they can read nothing and write nothing here."""
    key = (key or "").strip()
    if key.startswith("sb_publishable_") or (key.startswith("eyJ") and _jwt_role(key) == "anon"):
        raise CloudSyncError(PUBLIC_KEY_MESSAGE)


def _coerce(value, typ):
    """Convert a SQLite value to something Postgres accepts for the column type."""
    if value is None:
        return None
    if typ == TEXT:
        return str(value)
    if typ == INT:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
    if typ == REAL:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    if typ == TS:
        s = str(value).strip()
        if not s:
            return None
        try:
            return datetime.fromisoformat(s.replace("T", " ")).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None
    return value


class SupabaseSync:
    def __init__(self, url, key):
        url = (url or "").strip().rstrip("/")
        key = (key or "").strip()
        if not url or not key:
            raise CloudSyncError("Supabase URL and key are required")
        if not url.startswith("https://"):
            raise CloudSyncError("Supabase URL must start with https://")
        check_key_type(key)
        self.base = url + "/rest/v1"
        self.session = requests.Session()
        headers = {"apikey": key, "Content-Type": "application/json", "User-Agent": "POS-Desktop-Sync/1.0"}
        # New secret keys (sb_secret_...) go ONLY in the apikey header.
        # Legacy service_role keys are JWTs ("eyJ...") and also need Authorization.
        if key.startswith("eyJ"):
            headers["Authorization"] = f"Bearer {key}"
        self.session.headers.update(headers)

    # ------------------------------------------------------------- helpers
    def _raise_for(self, resp, table=""):
        if resp.status_code < 300:
            return
        try:
            body = resp.json()
            msg = body.get("message") or body.get("hint") or str(body)
            code = body.get("code", "")
        except ValueError:
            msg, code = resp.text[:300], ""
        if code == "42501" or "row-level security" in msg:
            # write refused by RLS => the request ran as the public role
            raise CloudSyncError(PUBLIC_KEY_MESSAGE)
        if resp.status_code in (401, 403):
            raise CloudSyncError(f"Key rejected by Supabase ({resp.status_code}). Use the secret / service_role key. {msg}")
        if code in ("PGRST205", "42P01") or "Could not find the table" in msg:
            raise CloudSyncError(f"Table '{table}' not found in Supabase — run supabase/schema.sql in the SQL Editor first.")
        raise CloudSyncError(f"{table}: HTTP {resp.status_code} {msg}")

    def _request(self, method, path, table="", **kw):
        try:
            resp = self.session.request(method, f"{self.base}/{path}", timeout=TIMEOUT, **kw)
        except requests.RequestException as e:
            raise CloudSyncError(f"Network error: {e}") from e
        self._raise_for(resp, table)
        return resp

    def _fetch_all(self, table, select):
        rows, offset = [], 0
        while True:
            resp = self._request("GET", table, table, params={
                "select": select, "order": "id.asc", "limit": PAGE_SIZE, "offset": offset})
            page = resp.json()
            rows.extend(page)
            if len(page) < PAGE_SIZE:
                return rows
            offset += PAGE_SIZE

    # ------------------------------------------------------------- public API
    def test_connection(self):
        """Raises CloudSyncError with a readable message if something is wrong."""
        for table in TABLES:
            self._request("GET", table, table, params={"select": "id", "limit": 1})
        # Reading alone is not enough (the public key can "read" an empty result):
        # prove we can WRITE by inserting and removing a throw-away settings row.
        probe = {"id": -1, "key": "__pos_write_test", "value": "1", "updated_at": None}
        self._request("POST", "settings", "settings", params={"on_conflict": "id"},
                      headers={"Prefer": "resolution=merge-duplicates,return=minimal"}, json=[probe])
        self._request("DELETE", "settings", "settings", params={"id": "eq.-1"},
                      headers={"Prefer": "return=minimal"})
        return True

    @staticmethod
    def _local_rows(conn, table, cols):
        existing = {r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')}
        use = [c for c in cols if c in existing]
        if "id" not in use:
            return []
        cur = conn.execute(f'SELECT {", ".join(chr(34) + c + chr(34) for c in use)} FROM "{table}"')
        out = []
        for raw in cur.fetchall():
            rec = {c: _coerce(raw[i], cols[c]) for i, c in enumerate(use)}
            for c in cols:                       # keep every object's keys identical (PostgREST requirement)
                rec.setdefault(c, None)
            out.append(rec)
        if table == "settings":
            out = [r for r in out if not str(r.get("key") or "").startswith(PRIVATE_SETTING_PREFIXES)]
        if table == "users":
            from utils.auth import is_hashed
            for r in out:                        # never upload a plain-text password
                if r.get("password") and not is_hashed(r["password"]):
                    r["password"] = None
        return out

    def cloud_owner(self):
        rows = self._request("GET", "settings", "settings",
                             params={"select": "value", "id": f"eq.{OWNER_ROW_ID}"}).json()
        return rows[0]["value"] if rows else None

    def claim_owner(self, install_id):
        self._request("POST", "settings", "settings", params={"on_conflict": "id"},
                      headers={"Prefer": "resolution=merge-duplicates,return=minimal"},
                      json=[{"id": OWNER_ROW_ID, "key": OWNER_KEY, "value": install_id, "updated_at": None}])

    def push_all(self, db, progress=None):
        """Mirror every local table to Supabase. Returns {table: rows_synced}."""
        # Safety: never mirror into a project that belongs to another POS computer
        # (two PCs would overwrite each other; an empty new PC would wipe the cloud copy).
        my_id = local_install_id(db)
        owner = self.cloud_owner()
        if owner and owner != my_id:
            raise CloudSyncError(OWNER_MESSAGE)
        if not owner:
            self.claim_owner(my_id)

        conn = db.get_connection()
        try:
            local = {t: self._local_rows(conn, t, cols) for t, cols in TABLES.items()}
        finally:
            conn.close()

        results = {}
        for i, (table, rows) in enumerate(local.items()):
            if progress:
                progress(i, len(TABLES), table)
            # 1) upsert in batches
            for start in range(0, len(rows), BATCH_SIZE):
                self._request("POST", table, table,
                              params={"on_conflict": "id"},
                              headers={"Prefer": "resolution=merge-duplicates,return=minimal"},
                              json=rows[start:start + BATCH_SIZE])
            # 2) delete rows that no longer exist locally (e.g. order items replaced on edit)
            local_ids = {r["id"] for r in rows}
            remote_ids = {r["id"] for r in self._fetch_all(table, "id")}
            stale = sorted(i for i in remote_ids - local_ids if i is not None and i >= 0)   # keep marker rows
            for start in range(0, len(stale), 200):
                chunk = ",".join(str(x) for x in stale[start:start + 200])
                self._request("DELETE", table, table, params={"id": f"in.({chunk})"},
                              headers={"Prefer": "return=minimal"})
            results[table] = len(rows)
        results["_synced_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return results

    @staticmethod
    def _to_sqlite(value, typ):
        # Postgres returns "2026-11-05T10:55:22"; the app compares "YYYY-MM-DD HH:MM:SS" strings
        if typ == TS and isinstance(value, str):
            return value.replace("T", " ")[:19]
        return value

    def download_to_sqlite(self, db, out_path):
        """Download the cloud copy into a NEW SQLite file (never touches the live DB).
        The schema is copied from the current local database so the file is a
        drop-in replacement that the normal Restore button can use."""
        cloud = {t: self._fetch_all(t, ",".join(cols)) for t, cols in TABLES.items()}

        src = db.get_connection()
        try:
            ddl = [r["sql"] for r in src.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND sql IS NOT NULL")]
            # keep this computer's private settings (cloud credentials etc.) in the restored file
            private = [dict(r) for r in src.execute("SELECT key, value FROM settings")
                       if str(r["key"]).startswith(PRIVATE_SETTING_PREFIXES)]
        finally:
            src.close()

        dst = sqlite3.connect(out_path)
        try:
            for stmt in ddl:
                dst.execute(stmt)
            counts = {}
            for table, rows in cloud.items():
                rows = [r for r in rows if (r.get("id") or 0) >= 0]   # skip cloud-only marker rows
                existing = {r[1] for r in dst.execute(f'PRAGMA table_info("{table}")')}
                cols = [c for c in TABLES[table] if c in existing]
                if not cols:
                    continue
                placeholders = ",".join("?" * len(cols))
                col_sql = ",".join(f'"{c}"' for c in cols)
                dst.executemany(f'INSERT OR REPLACE INTO "{table}" ({col_sql}) VALUES ({placeholders})',
                                [tuple(self._to_sqlite(r.get(c), TABLES[table][c]) for c in cols) for r in rows])
                counts[table] = len(rows)
            for p in private:
                dst.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (p["key"], p["value"]))
            # Restoring this file makes this PC the owner of the cloud copy (e.g. replacing a broken PC)
            owner = next((r.get("value") for r in cloud.get("settings", []) if r.get("id") == OWNER_ROW_ID), None)
            if owner:
                dst.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('cloud_install_id', ?)", (owner,))
            dst.commit()
        finally:
            dst.close()
        return counts
