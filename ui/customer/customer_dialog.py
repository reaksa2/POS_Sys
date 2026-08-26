from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QFormLayout, QLineEdit, QComboBox, QDialogButtonBox
from utils.style import BTN_SAVE,BTN_CANCEL,INPUT_STYLE
class CustomerDialog(QDialog):
    def __init__(self, parent=None, title="Add New Customer", data=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(440, 520)
        self.setStyleSheet("background-color: #2A2A2A; color: white;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title_label)

        form = QFormLayout()
        form.setSpacing(15)

        self.name = QLineEdit()
        self.name.setStyleSheet(INPUT_STYLE)
        self.phone = QLineEdit()
        self.phone.setStyleSheet(INPUT_STYLE)
        self.address = QLineEdit()
        self.address.setStyleSheet(INPUT_STYLE)
        self.facebook = QLineEdit()
        self.facebook.setStyleSheet(INPUT_STYLE)
        self.telegram = QLineEdit()
        self.telegram.setStyleSheet(INPUT_STYLE)
        self.type = QComboBox()
        self.type.setStyleSheet(INPUT_STYLE)
        self.type.addItems(["New", "Regular", "VIP"])

        form.addRow("ឈ្មោះ *:", self.name)
        form.addRow("លេខទូរស័ព្ទ *:", self.phone)
        form.addRow("អាសយដ្ឋាន:", self.address)
        form.addRow("ហ្វេសប៊ុក:", self.facebook)
        form.addRow("តេឡេក្រាម:", self.telegram)
        form.addRow("ប្រភេទ:", self.type)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        # Style OK and Cancel buttons
        ok_btn = buttons.button(QDialogButtonBox.Ok)
       
        cancel_btn = buttons.button(QDialogButtonBox.Cancel)
     

        if ok_btn:
            ok_btn.setText("💾 រក្សាទុក")
            ok_btn.setStyleSheet(BTN_SAVE)

        if cancel_btn:
            cancel_btn.setText("ចាកចេញ")
            cancel_btn.setStyleSheet(BTN_CANCEL)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Load existing data if editing
        if data:
            self.name.setText(data.get("name", ""))
            self.phone.setText(data.get("phone", ""))
            self.address.setText(data.get("address", ""))
            self.facebook.setText(data.get("facebook", ""))
            self.telegram.setText(data.get("telegram", ""))
            self.type.setCurrentText(data.get("type", "New"))

    def get_data(self):
        return {
            "name": self.name.text().strip(),
            "phone": self.phone.text().strip(),
            "address": self.address.text().strip(),
            "facebook": self.facebook.text().strip(),
            "telegram": self.telegram.text().strip(),
            "type": self.type.currentText()
        }