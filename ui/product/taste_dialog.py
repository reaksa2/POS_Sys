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


class TasteDialog(QDialog):
    def __init__(self, parent=None, taste_data=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.taste_data = taste_data or {}
        self.is_edit = bool(taste_data)

        self.setWindowTitle("បន្ថែមរសជាតិថ្មី" if not self.is_edit else "កែប្រែរសជាតិ")
        self.setFixedSize(500, 460)
        self.setStyleSheet("background-color: #2A2A2A; color: white;")

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("រសជាតិ")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(15)

        self.taste_name = QLineEdit(self.taste_data.get("taste_name",""))
        self.taste_name.setPlaceholderText("ឈ្នោះរសជាតិ...")
        self.taste_name.setStyleSheet(INPUT_STYLE)
        self.taste_des = QTextEdit()
        self.taste_des.setMaximumHeight(100)
        self.taste_des.setPlaceholderText("ព័ត៌មានបន្ថែម...")
        self.taste_des.setStyleSheet(INPUT_STYLE)
        if self.taste_data.get("taste_des"):
                    self.taste_des.setPlainText(self.taste_data.get("taste_des"))
        

        form.addRow("ឈ្នោះរសជាតិ *:", self.taste_name)
        form.addRow("ព័ត៌មានបន្ថែម :", self.taste_des)
       

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
        if not self.taste_name.text().strip():
            none_selected_warning(self, "សូមបញ្ចូលឈ្នោះរសជាតិ")
            return

        
        
        data = {
            "taste_name":self.taste_name.text().strip(),
            "taste_des":self.taste_des.toPlainText().strip(),
        }

        self.accept()
        return data