from PySide6.QtCore import QThread, Signal
from utils.sheet_sync import SheetsSync, has_internet


class SyncWorker(QThread):
    sync_finished = Signal(dict)
    sync_failed = Signal(str)

    def __init__(self, db, credentials_path, sheet_id):
        super().__init__()
        self.db = db
        self.credentials_path = credentials_path
        self.sheet_id = sheet_id

    def run(self):
        if not has_internet():
            self.sync_failed.emit("No internet connection")
            return
        try:
            syncer = SheetsSync(self.credentials_path, self.sheet_id)
            results = syncer.sync_all_tables(self.db)
            self.sync_finished.emit(results)
        except Exception as e:
            self.sync_failed.emit(str(e))