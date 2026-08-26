from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFormLayout, QMessageBox,QHBoxLayout,QCheckBox
)
from PySide6.QtCore import Qt, Signal,QSettings
from PySide6.QtGui import QPixmap

from utils.utils import (resource_path)
from utils.style import BTN_SAVE,PAGE_TITLE_STYLE,INPUT_STYLE

class LoginWindow(QWidget):
    login_success = Signal(dict)

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.settings = QSettings("ChickenPOS", "LoginPrefs")   # persistent local storage
        # Hidden default menu of window popup 
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        self.setWindowTitle("ចូលប្រើប្រាស់ប្រព័ន្ធ")
        self.setFixedSize(500, 640)   # slightly taller for the checkbox
        self.setStyleSheet("background-color: #8B5A2B;")
        self.center_on_screen() 
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(30)
        layout.setContentsMargins(20, 20, 20, 20)

        # ==================== LOGO ====================
        logo_label = QLabel()
        logo_path = resource_path("logo.png")
        pixmap = QPixmap(str(logo_path))
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                140, 140,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            logo_label.setPixmap(scaled_pixmap)
        else:
            logo_label.setText("Logo Not Found")
            logo_label.setStyleSheet("color: #ffcc00; font-size: 20px;")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)
        
        # ==================== TITLE ====================
        title = QLabel(self.app.settings.get("business_name","POS"))
        title.setStyleSheet(PAGE_TITLE_STYLE)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # ==================== FORM ====================
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form_layout.setSpacing(18)

        input_style = """
            QLineEdit {
                padding: 14px;
                font-size: 17px;
                border-radius: 10px;
                background-color: transparent;
                color: white;
                border: 1px solid #ffffff;
            }
        """

        # Username
        username_layout = QHBoxLayout()
        username_label = QLabel("👤 ឈ្មោះអ្នកប្រើប្រាស់:")
        username_label.setStyleSheet("color: white; font-size: 16px;")
        self.username = QLineEdit()   # ← no hardcoded default
        self.username.setPlaceholderText("Enter username")
        self.username.setFixedWidth(250)
        self.username.setStyleSheet(input_style)
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username)
        form_layout.addLayout(username_layout)

        # Password
        password_layout = QHBoxLayout()
        password_label = QLabel("🔒 លេខសម្ងាត់:")
        password_label.setStyleSheet("color: white; font-size: 16px;")
        self.password = QLineEdit()   # ← no hardcoded default
        self.password.setPlaceholderText("Enter password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setFixedWidth(250)
        self.password.setStyleSheet(input_style)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password)
        form_layout.addLayout(password_layout)

        # Remember Me checkbox
        self.remember_checkbox = QCheckBox("ចងចាំការប្រើប្រាស់")
        self.remember_checkbox.setStyleSheet("""
            QCheckBox {
                color: white;
                font-size: 14px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        remember_layout = QHBoxLayout()
        remember_layout.addStretch()
        remember_layout.addWidget(self.remember_checkbox)
        remember_layout.addStretch()
        form_layout.addLayout(remember_layout)

        layout.addWidget(form_container)

        # ==================== LOGIN BUTTON ====================
        login_btn = QPushButton("ចូលប្រើប្រាស់")
        login_btn.setStyleSheet(BTN_SAVE)
        login_btn.clicked.connect(self.attempt_login)
        layout.addWidget(login_btn)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #ffdd88; font-size: 15px;")
        layout.addWidget(self.status_label)

        # Enter key submits the form
        self.username.returnPressed.connect(self.attempt_login)
        self.password.returnPressed.connect(self.attempt_login)

        # Load saved username if "remember me" was previously checked
        self.load_remembered_username()



    def center_on_screen(self):
        screen = self.screen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    
    def load_remembered_username(self):
        remembered = self.settings.value("remembered_username", "")
        if remembered:
            self.username.setText(remembered)
            self.remember_checkbox.setChecked(True)
            self.password.setFocus()   # username already filled, jump to password
        else:
            self.username.setFocus()

    def attempt_login(self):
        username = self.username.text().strip()
        password = self.password.text()

        if not username or not password:
            self.status_label.setText("⚠️ សូមបញ្ចូលឈ្មោះនិងពាក្យសម្ងាត់")
            return

        try:
            conn = self.app.db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE username = ? AND password = ? AND active = 1",
                (username, password)
            )
            user = cursor.fetchone()
            conn.close()

            if user:
                # Save or clear remembered username based on checkbox
                if self.remember_checkbox.isChecked():
                    self.settings.setValue("remembered_username", username)
                else:
                    self.settings.remove("remembered_username")

                self.login_success.emit(dict(user))
            else:
                self.status_label.setText("❌ ឈ្មោះឬពាក្យសម្ងាត់មិនត្រឹមត្រូវ! ឬគណនីត្រូវបានផ្អាក")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))