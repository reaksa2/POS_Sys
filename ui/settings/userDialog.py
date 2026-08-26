import os
import json
from PySide6.QtWidgets import (
     QVBoxLayout, QLabel,
    QLineEdit,  QFormLayout, QComboBox,
    QDialog, QDialogButtonBox)

from utils.style import BTN_SAVE,BTN_CANCEL, INPUT_STYLE, TABLE_STYLE,BTN_NEUTRAL,BTN_PRINT
from utils.dialog import save_success_message,none_selected_warning,confirm_delete


class UserDialog(QDialog):
    def __init__(self, parent=None, app=None, data=None):
        super().__init__(parent)
        self.app = app
        self.is_edit = bool(data)
        self.setWindowTitle("កែប្រែអ្នកប្រើប្រាស់" if self.is_edit else "បន្ថែមអ្នកប្រើថ្មី")
        self.setFixedSize(400, 380)
        self.setStyleSheet("background-color: #2A2A2A; color: white;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        title = QLabel("👤 " + ("កែប្រែអ្នកប្រើប្រាស់" if self.is_edit else "អ្នកប្រើថ្មី"))
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)

        self.name_input = QLineEdit(data.get("name", "") if data else "")
        self.name_input.setPlaceholderText("ឈ្មោះប្រើប្រាស់")
        self.name_input.setStyleSheet(INPUT_STYLE)

        self.username_input = QLineEdit(data.get("username", "") if data else "")
        self.username_input.setPlaceholderText("ឈ្មោះអ្នកប្រើប្រាស់")
        self.username_input.setStyleSheet(INPUT_STYLE)
        if self.is_edit:
            self.username_input.setReadOnly(True)   # don't allow changing username once created

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("ពាក្យសម្ងាត់" + (" (ទុកទទេប្រសិនបើមិនប្តូរ)" if self.is_edit else ""))
        self.password_input.setStyleSheet(INPUT_STYLE)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.role_combo = QComboBox()
        self.role_combo.addItems(["Cashier", "Manager", "Admin", "Owner"])
        self.role_combo.setStyleSheet(INPUT_STYLE)
        if data and data.get("role"):
            idx = self.role_combo.findText(data["role"])
            if idx >= 0:
                self.role_combo.setCurrentIndex(idx)

        self.brand_combo = QComboBox()
        self.brand_combo.setStyleSheet(INPUT_STYLE)
        self.brand_combo.addItem("គ្មានម៉ាក (Admin/Owner)", None)
        if self.app:
            for b in self.app.brand.get_brands():
                self.brand_combo.addItem(b['name'], b['id'])
        if data and data.get('brand_id'):
            idx = self.brand_combo.findData(data['brand_id'])
            if idx >= 0:
                self.brand_combo.setCurrentIndex(idx)

        form.addRow("ឈ្មោះ *:", self.name_input)
        form.addRow("ឈ្មោះប្រើប្រាស់ *:", self.username_input)
        form.addRow("ពាក្យសម្ងាត់" + (" :" if self.is_edit else " *:"), self.password_input)
        form.addRow("តួនាទី:", self.role_combo)
        form.addRow("ម៉ាកយីហោ:", self.brand_combo)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        ok_btn = buttons.button(QDialogButtonBox.Ok)
        ok_btn.setText("💾 រក្សាទុក")
        ok_btn.setStyleSheet(BTN_SAVE)

        cancel_btn = buttons.button(QDialogButtonBox.Cancel)
        cancel_btn.setText("❌ បោះបង់")
        cancel_btn.setStyleSheet(BTN_CANCEL)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        name = self.name_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not name or not username or (not self.is_edit and not password):
            none_selected_warning(self, message="ឈ្មោះអ្នកប្រើប្រាស់ ជាមួយនិងលេខសម្ងាត់ត្រូវបានទាមទារ", win_title="កំហុស")
            return None

        result = {
            "name": name,
            "username": username,
            "role": self.role_combo.currentText(),
            "brand_id": self.brand_combo.currentData(),
        }
        if password:   # only include password if user actually typed one (relevant for edit mode)
            result["password"] = password
        return result