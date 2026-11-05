from PySide6.QtCore import QThread, Signal


class SyncWorker(QThread):
    """Google Sheets sync (legacy, currently disabled in main.py)."""
    sync_finished = Signal(dict)
    sync_failed = Signal(str)

    def __init__(self, db, credentials_path, sheet_id):
        super().__init__()
        self.db = db
        self.credentials_path = credentials_path
        self.sheet_id = sheet_id

    def run(self):
        from utils.sheet_sync import SheetsSync, has_internet   # gspread only imported when actually used
        if not has_internet():
            self.sync_failed.emit("No internet connection")
            return
        try:
            syncer = SheetsSync(self.credentials_path, self.sheet_id)
            results = syncer.sync_all_tables(self.db)
            self.sync_finished.emit(results)
        except Exception as e:
            self.sync_failed.emit(str(e))


class SupabaseSyncWorker(QThread):
    """Runs a Supabase operation off the UI thread.

    mode: "push"     → mirror local DB to the cloud
          "test"     → check URL/key/tables
          "download" → pull the cloud copy into `out_path` (a new .db file)
    """
    progress = Signal(int, int, str)     # index, total, table name
    sync_finished = Signal(dict)
    sync_failed = Signal(str)

    def __init__(self, db, url, key, mode="push", out_path=None):
        super().__init__()
        self.db = db
        self.url = url
        self.key = key
        self.mode = mode
        self.out_path = out_path

    def run(self):
        try:
            from utils.supabase_sync import SupabaseSync
            client = SupabaseSync(self.url, self.key)
            if self.mode == "test":
                client.test_connection()
                self.sync_finished.emit({"ok": True})
            elif self.mode == "download":
                counts = client.download_to_sqlite(self.db, self.out_path)
                counts["_path"] = self.out_path
                self.sync_finished.emit(counts)
            else:
                results = client.push_all(self.db, progress=lambda i, n, t: self.progress.emit(i, n, t))
                self.sync_finished.emit(results)
        except Exception as e:
            self.sync_failed.emit(str(e))
