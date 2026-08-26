from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QHBoxLayout, QLabel, QMessageBox,
    QTextEdit
)
from PySide6.QtCore import Qt
from utils.style import BTN_ADD, BTN_CANCEL,INPUT_STYLE
from utils.dialog import none_selected_warning

def to_float(text, default=0.0):
    if not text:
        return default
    try:
        return float(str(text).replace(",", "").strip())
    except ValueError:
        return default


class UnitDialog(QDialog):
    def __init__(self, parent=None, unit_data=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.unit_data = unit_data or {}
        self.is_edit = bool(unit_data)

        self.setWindowTitle("បន្ថែមប្រភេទឯកតា" if not self.is_edit else "កែប្រែឯកតា")
        self.setFixedSize(500, 460)
        self.setStyleSheet("background-color: #2A2A2A; color: white;")

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("ឯកតា")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(15)

        self.unit_name = QLineEdit(self.unit_data.get("unit_name",""))
        self.unit_name.setPlaceholderText("ឈ្នោះឯកតា...")
        self.unit_name.setStyleSheet(INPUT_STYLE)
        self.unit_des = QTextEdit()
        self.unit_des.setMaximumHeight(100)
        self.unit_des.setPlaceholderText("ព័ត៌មានបន្ថែម...")
        self.unit_des.setStyleSheet(INPUT_STYLE)
        if self.unit_data.get("unit_des"):
                    self.unit_des.setPlainText(self.unit_data.get("unit_des"))
        

        form.addRow("ឈ្នោះឯកតា *:", self.unit_name)
        form.addRow("ព័ត៌មានបន្ថែម :", self.unit_des)
       

        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 រក្សាទុក")
        save_btn.setStyleSheet(BTN_ADD)
        cancel_btn = QPushButton("❌ បោះបង់")
        cancel_btn.setStyleSheet(BTN_CANCEL)

        save_btn.clicked.connect(self.save_data)
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

       
    

    def save_data(self):
        if not self.unit_name.text().strip():
            none_selected_warning(self, "សូមបញ្ចូលឈ្នោះឯកតា")
            return

        
        
        data = {
            "unit_name":self.unit_name.text().strip(),
            "unit_des":self.unit_des.toPlainText().strip(),
        }

        self.accept()
        return data