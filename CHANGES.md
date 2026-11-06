# V1.6.1 — Duplicate products

- **Products → 📄 ចម្លង (Duplicate)**: select a product and click 📄 ចម្លង (or right-click it). The form opens pre-filled
  with the same name, category, unit, price and description; change the name and price (e.g. ជ្រូកខ្វៃ 3.5kg → 4.5kg, $95 → $115)
  and click 💾 បន្ថែម to create a new product. Saving with a name that already exists is blocked. Stock is not copied.
- Right-click on any product row: ✏️ Edit / 📄 Duplicate / 🗑 Delete.

---

# V1.6.0 — bug fixes + Supabase cloud backup

No new Python packages are needed (cloud sync uses `requests`, already in requirements.txt).
The existing `database/pos.db` is upgraded automatically on first start; nothing to do by hand.

## Bugs fixed

### Data-corrupting / blocking
| Where | Problem | Fix |
|---|---|---|
| Customers → edit (double-click) | Read the wrong table columns, so **saving an edit scrambled the customer**: address←Facebook, Facebook←Telegram, Telegram←type, type←address. | Edit form now loads the customer from the database by id. |
| Orders → edit, then 🗑️ Clear | `editing_order_id` was not reset, so the **next new order silently overwrote the old pending order**. | Clearing the cart leaves edit mode. |
| Settings → Business → Save (twice) | New brands had no id until reload, so a second save **inserted duplicate brands**. Saving with no brand deactivated all brands (nothing sellable). | Brands reload after save; at least one brand is required. |
| Settings → Business | `business_address` was saved but never loaded, so **the next save erased it**. | Address is loaded. |
| Stock in/out/transfer dialogs | Product box is searchable; typing a name without picking it from the list **adjusted the previously selected product**. | Product is resolved from the visible text. |
| Stock out | Could take stock below zero. | Blocked with a message showing available qty. |
| Products → Others → delete category / unit / taste | **Always crashed** (`(id)` is not a tuple). | Fixed; a category/unit still used by products shows a clear "in use" message instead of an error. |
| Stock history "today / this week" | Movements were stored in **UTC** (7 h behind Cambodia) while filters use local time — anything before 7 am showed on the wrong day. | Stored in local time; existing rows converted once (flag `migration_local_time_v1`). |

### Other bugs
- **Update checker never found updates**: `"V1.5.2"` parsed as `(5, 2)`, which beats any `1.x` release. Leading `v/V` now stripped.
- **Order history**: changing the "to" date was immediately reset to *now*; the history tab also showed *all* orders (ignoring the date filter) after placing an order, with a stale summary.
- Order screen: selected customer and delivery/discount were wiped when switching pages mid-order; "paid" amount didn't follow later changes to the total; quantities ≥ 1,000 (shown as `1,000.00`) couldn't be edited; editing an order whose product was deleted failed with a FOREIGN KEY error.
- Receipts: brand info had disappeared (read an old setting that is no longer written) — now uses the order's brand from the `brands` table. Customer names containing `&` or `<` no longer break the receipt HTML.
- Settings → Printer → paper size (A5 / A4 / 80 mm) was saved but ignored — all prints were A5. Now applied everywhere (new `utils/printing.py`).
- App crashed at start if the Khmer font failed to load; window title used syntax that only works on Python 3.12+; "About" menu button never highlighted; closing the app during the update check could crash on exit.
- Database path depended on the folder the .exe was *started from* (a shortcut with another "Start in" folder opened an empty database). Now always next to `POS.exe`; an existing DB at the old location is still used.
- Backups use SQLite's online-backup API (consistent copy even while writing).
- Stock history filter didn't show newly added brands until restart.

### Security
- Passwords were stored and compared in **plain text**. Now salted PBKDF2 hashes (`utils/auth.py`). Existing passwords are converted automatically on first start and keep working.

## New: ☁️ Cloud backup to Supabase (free)
Settings → **☁️ Cloud**. See `supabase/README.md` for the 5-minute setup.
- Mirrors all 13 tables to Supabase (upsert + mirrored deletes), manually or automatically every N minutes, in a background thread (the till never freezes, and it keeps working offline).
- **Download from Cloud** creates a new file in the Backup list that you restore with the normal double-click (new PC / disk failure).
- Secret key stays on this PC and is never uploaded; passwords go up only as hashes; RLS blocks the public key.

Files: `utils/supabase_sync.py`, `utils/sync_worker.py`, `supabase/schema.sql`, `ui/settings/settings_widget.py` (Cloud tab), `main.py` (timer).
