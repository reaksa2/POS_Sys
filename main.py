import os
os.environ["QT_LOGGING_RULES"] = "qt.text.font.db=false"
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase, QFont,QDesktopServices
from PySide6.QtCore import QTimer,QUrl

from ui.splash import SplashScreen
from ui.login.login_window import LoginWindow
from ui.main_window import MainWindow
from database.db_manager import DatabaseManager
from database.models.category_model import CategoryModel
from database.models.taste_model import TasteModel
from database.models.unit_model import UnitModel
from database.models.products_model import ProductModel
from database.models.customer_model import CustomerModel
from database.models.orders_model import OrderModel
from database.models.SettingsModel import SettingsModel
from database.models.UserModel import UserModel
from database.models.stock_model import StockModel
from database.models.BrandModel import BrandModel
from utils.utils import resource_path
from utils.style import get_app_global_style
from utils.backup import backup_database
from utils.dialog import save_success_message, none_selected_warning, confirm_delete
class POS(QApplication):
    def __init__(self, argv):
        
        super().__init__(argv)
        self.load_custom_fonts()
        self.setStyleSheet(get_app_global_style(self.default_font_family))   # ← only this one, remove the other

        self.db = DatabaseManager()
        self.cate = CategoryModel()
        self.taste = TasteModel()
        self.unit = UnitModel()
        self.pro = ProductModel()
        self.cust = CustomerModel()
        self.order = OrderModel(self.db)
        self.settings = SettingsModel(self.db)
        self.users = UserModel(self.db)
        self.stock = StockModel(self.db)
        self.brand = BrandModel(self.db)
        self.splash = None
        self.login = None
        self.main_window = None

        self.check_and_run_daily_backup()
        # self._sync_worker = None 

        # self.setup_auto_sync()

# ================ Sync ================= 
    # def setup_auto_sync(self):
    #     self.sync_timer = QTimer()
    #     self.sync_timer.timeout.connect(self.run_auto_sync)
    #     self.sync_timer.start(30 * 60 * 1000)   # every 30 minutes

    # def run_auto_sync(self):
    #     credentials_path = self.settings.get("sheets_credentials_path", "")
    #     sheet_id = self.settings.get("sheets_id", "")

    #     if not credentials_path or not sheet_id:
    #         return   # not configured, skip silently

    #     if self._sync_worker and self._sync_worker.isRunning():
    #         return   # previous sync still running, skip this cycle

    #     from utils.sync_worker import SyncWorker
    #     self._sync_worker = SyncWorker(self.db, credentials_path, sheet_id)
    #     self._sync_worker.sync_finished.connect(self.on_sync_finished)
    #     self._sync_worker.sync_failed.connect(self.on_sync_failed)
    #     self._sync_worker.start()

    # def on_sync_finished(self, results):
    #     synced_at = results.pop('_synced_at', '')
    #     self.settings.set("last_sync_at", synced_at)
    #     print(f"Auto-sync completed at {synced_at}: {results}")

    # def on_sync_failed(self, error_msg):
    #     print(f"Auto-sync skipped/failed: {error_msg}")
    # =============== Sync =================

    
    def start(self):
        self.splash = SplashScreen()
        self.splash.finished.connect(self.show_login)
        self.splash.show()

    def show_login(self):
        self.login = LoginWindow(self)
        self.login.login_success.connect(self.on_login_success)
        self.login.show()

    def on_login_success(self, user):
        if self.login:
            self.login.close()
        self.user = user
        self.main_window = MainWindow(self, user)
        self.main_window.show()
        self.check_for_updates(silent=True) 

    def load_custom_fonts(self):
        font_path = str(resource_path("fonts/Khmer OS Siemreap Regular.ttf"))
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                self.default_font_family = families[0]
                self.setFont(QFont(self.default_font_family, 10))
        # silently fall back to system default if font fails to load — no need to alarm the user

    def check_and_run_daily_backup(self):
        
        import datetime as dt

        auto_enabled = self.settings.get("auto_backup_enabled", "0") == "1"
        if not auto_enabled:
            return

        last_backup = self.settings.get("last_backup_at", "")
        today_str = dt.date.today().isoformat()

        if last_backup and last_backup.startswith(today_str):
            return

        try:
            db_path = str(self.db.db_path)
            backup_folder = str(self.db.db_path.parent / "backups")
            backup_database(db_path, backup_folder, keep_last=10)
            self.settings.set("last_backup_at", dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            print("Daily auto-backup completed.")
        except Exception as e:
            print(f"Auto-backup failed: {e}")

    def check_for_updates(self, silent=True):
        from utils.update_checker import UpdateCheckWorker
        self._update_worker = UpdateCheckWorker()
        self._update_worker.update_available.connect(
            lambda v, url, notes: self.on_update_available(v, url, notes)
        )
        if not silent:
            self._update_worker.no_update.connect(self.on_no_update)
            self._update_worker.check_failed.connect(self.on_update_check_failed)
        self._update_worker.start()

    def on_update_available(self, version, url, notes):

        should_download = confirm_delete(
            self.main_window,   # ← actual QWidget parent
            message=f"កំណែថ្មី {version} អាចប្រើប្រាស់បាន។\n\n{notes[:300]}",
            confirm_text="ទាញយកឥឡូវនេះ",
            cancel_text="ពេលក្រោយ",
            win_title="មានកំណែថ្មី!"
        )

        if should_download and url:
            QDesktopServices.openUrl(QUrl(url))

    def on_no_update(self):
        save_success_message(self.main_window, message="អ្នកកំពុងប្រើកំណែចុងក្រោយបំផុតរួចហើយ។", win_title="កំណែថ្មីៗ", auto_close_ms=None)

    def on_update_check_failed(self, error):
        none_selected_warning(self.main_window, message=f"មិនអាចពិនិត្យកំណែថ្មីបានទេ:\n{error}", win_title="បរាជ័យ",auto_close_ms=None)


if __name__ == "__main__":
    app = POS(sys.argv)
    app.start()
    sys.exit(app.exec())