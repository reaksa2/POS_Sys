# Cloud backup with Supabase (free plan)

The POS keeps using its local database (works offline). Supabase holds an online
copy that updates automatically, so a broken or stolen PC doesn't lose your sales.

## One-time setup (~5 minutes)
1. Sign up at https://supabase.com → **New project** (Free plan). Choose the region
   closest to you (e.g. Singapore).
2. In the POS: **Settings → ☁️ Cloud → 📋 Copy SQL**.
   In Supabase: **SQL Editor → New query → paste → Run**. (Same SQL as `schema.sql`; safe to run again.)
3. In Supabase: **Project Settings → API Keys**. Copy:
   - **Project URL** — `https://xxxxxxxx.supabase.co`
   - **Secret key** — `sb_secret_…` (or the legacy `service_role` key)
4. In the POS: paste both → **💾 Save** → **🔌 Test connection** → **☁️⬆️ Sync now**.
5. Tick **auto sync every … minutes** (15 is a good default) and Save.

You can browse your data any time in Supabase → **Table Editor**.

## Restoring (new PC / crash)
Install the POS, log in with the default admin (`admin` / `admin123`), go to
Settings → ☁️ Cloud, enter the same URL + key → **☁️⬇️ Download from Cloud**.
A file `pos_backup_cloud_….db` appears in **💾 Backup**; double-click it to restore,
then restart the app. Your users and passwords come back too.

## Good to know
- **Keep the secret key private.** It gives full access to the cloud copy. It is stored
  only in this PC's database and is never uploaded. If it leaks, create a new secret key
  in Supabase, delete the old one, and paste the new one here.
- Row Level Security is enabled with no policies, so the public (publishable/anon) key
  can't read anything.
- Free plan: 500 MB database (years of orders for one shop), 2 projects. Supabase
  **pauses free projects after about a week of no activity**; regular auto-sync keeps it
  active, but if the PC is off for a long holiday you may need to click "Restore project"
  in the Supabase dashboard. Free projects have no automatic Supabase backups — keep the
  local daily backup turned on as well.
- One POS computer per Supabase project. (Two shops pushing to the same project would
  overwrite each other's rows, because ids come from each local database.)
