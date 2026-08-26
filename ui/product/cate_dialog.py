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


class CategoryDialog(QDialog):
    def __init__(self, parent=None, cate_data=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.cate_data = cate_data or {}
        self.is_edit = bool(cate_data)

        self.setWindowTitle("បន្ថែមប្រភេទទំនិញ" if not self.is_edit else "កែប្រែប្រភេទទំនិញ")
        self.setFixedSize(500, 460)
        self.setStyleSheet("background-color: #2A2A2A; color: white;")

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("ប្រភេទទំនិញ")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(15)

        self.category_name = QLineEdit(self.cate_data.get("cate_name",""))
        self.category_name.setPlaceholderText("ឈ្នោះប្រភេទទំនិញ...")
        self.category_name.setStyleSheet(INPUT_STYLE)

        self.category_des = QTextEdit()
        self.category_des.setFixedHeight(100)
        self.category_des.setStyleSheet(INPUT_STYLE)
        self.category_des.setPlaceholderText("ព័ត៌មានបន្ថែម...")
        if self.cate_data.get("cate_des"):
                    self.category_des.setPlainText(self.cate_data.get("cate_des"))
        

        form.addRow("ឈ្នោះប្រភេទទំនិញ *:", self.category_name)
        form.addRow("ព័ត៌មានបន្ថែម :", self.category_des)
       

        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 រក្សាទុក")
        save_btn.setStyleSheet(BTN_ADD)
        cancel_btn = QPushButton("❌ បោះបង់")
        cancel_btn.setStyleSheet(BTN_CANCEL)

        save_btn.clicked.connect(self.save_cate)
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

       
    

    def save_cate(self):
        if not self.category_name.text().strip():
            none_selected_warning(self, "សូមបញ្ចូលឈ្នោះប្រភេទទំនិញ")
            return

        
        
        data = {
            "cate_name":self.category_name.text().strip(),
            "cate_des":self.category_des.toPlainText().strip(),
        }

        self.accept()
        return data