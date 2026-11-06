from PySide6.QtWidgets import (
    QDialog, QTextEdit, QVBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QPushButton, QHBoxLayout, QLabel, QMessageBox, QDialogButtonBox,QDoubleSpinBox
)
from PySide6.QtCore import Qt
import random
from utils.style import BTN_ADD,BTN_SAVE,TABLE_STYLE,BTN_CANCEL,INPUT_STYLE
from utils.dialog import save_success_message,none_selected_warning
class ProductDialog(QDialog):
    def __init__(self, parent=None, product_data=None, duplicate=False):
        super().__init__(parent)
        self.parent_widget = parent
        self.product_data = product_data or {}
        # duplicate=True: form is pre-filled from an existing product, but saving creates a NEW product
        self.is_duplicate = bool(duplicate)
        self.is_edit = bool(product_data) and not self.is_duplicate
        self.is_prefilled = bool(product_data)

        if self.is_duplicate:
            self.setWindowTitle("ចម្លងទំនិញ")
        else:
            self.setWindowTitle("កែប្រែព័ត៌មាន" if self.is_edit else "បញ្ចូលទំនិញថ្មី")
        self.setFixedSize(520, 520)
        self.setStyleSheet("background-color: #2A2A2A; color: white;")

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        if self.is_duplicate:
            title_text = "📄 ចម្លងទំនិញ — កែឈ្មោះ និងតម្លៃ"
        else:
            title_text = "📦 ព័ត៌មានទំនិញ" if self.is_edit else "➕ បញ្ចូលទំនិញថ្មី"
        title = QLabel(title_text)
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(15)

        self.name_input = QLineEdit(self.product_data.get("name", ""))
        self.name_input.setStyleSheet(INPUT_STYLE)
        self.category_combo = QComboBox()
        self.category_combo.setStyleSheet(INPUT_STYLE)
        self.unit_combo = QComboBox()
        self.unit_combo.setStyleSheet(INPUT_STYLE)
        self.price_input = QDoubleSpinBox()
        self.price_input.setStyleSheet(INPUT_STYLE)
        self.price_input.setPrefix("$ ")
        self.price_input.setSuffix(" USD")
        self.price_input.setDecimals(2)
        self.price_input.setRange(0.00, 9999999.99)
        self.price_input.setSingleStep(5)
        self.price_input.setValue(self.product_data.get('price', 0))




        self.description_input = QTextEdit(self.product_data.get("description", ""))   # ← Multi-line Textarea
        self.description_input.setFixedHeight(100)
        self.description_input.setPlaceholderText("លម្អិត...")
        self.description_input.setStyleSheet(INPUT_STYLE)
        form.addRow("ឈ្មោះទំនិញ *:", self.name_input)
        form.addRow("ប្រភេទ:", self.category_combo)
        form.addRow("ឯកតា:", self.unit_combo)
        form.addRow("តម្លៃ*:", self.price_input)
        form.addRow("លម្អិត:", self.description_input)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        # Style OK and Cancel buttons
        ok_btn = buttons.button(QDialogButtonBox.Ok)
        cancel_btn = buttons.button(QDialogButtonBox.Cancel)

        if ok_btn:
            ok_btn.setText("💾 បន្ថែម" if not self.is_edit else "💾 រក្សាទុក")
            ok_btn.setStyleSheet(BTN_SAVE)

        if cancel_btn:
            cancel_btn.setText("❌ បោះបង់")
            cancel_btn.setStyleSheet(BTN_CANCEL)

        buttons.accepted.connect(self.save_product)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.load_categories()
        self.load_unit()

        if self.is_duplicate:
            # highlight the name so the user can type the new one straight away
            self.name_input.setFocus()
            self.name_input.selectAll()


    def get_user_id(self):
        if hasattr(self.parent_widget,"app") and hasattr(self.parent_widget.app,"user"):
            user = self.parent_widget.app.user
            if user and isinstance(user,dict):
                return user.get("id")
        return None


    def load_categories(self):
        """Load categories with ID"""
        try:
            if hasattr(self.parent_widget, 'app') and hasattr(self.parent_widget.app, 'cate'):
                db = self.parent_widget.app.cate
            else:
                db = None

            if db:
                categories = db.get_all_category()

                self.category_combo.clear()
                self.category_combo.addItem("ជ្រើសរើស ប្រភេទទំនិញ", None)

                for cat in categories:
                    self.category_combo.addItem(cat['name'], cat['id'])   # Store ID as userData
            else:
                raise Exception("No DB")
        except Exception as e:
            print("Error loading categories:", e)
            self.category_combo.addItems(["Select Category", "Duck", "Pork", "Chicken", "Others"])

        # Set current category when editing
        if self.is_prefilled and self.product_data.get("category"):
            category_name = self.product_data.get("category")
            index = self.category_combo.findText(category_name)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)

    def load_unit(self):
        """Load Unit with ID"""
        try:
            if hasattr(self.parent_widget, 'app') and hasattr(self.parent_widget.app, 'unit'):
                db = self.parent_widget.app.unit
            else:
                db = None

            if db:
                units = db.get_all_unit()

                self.unit_combo.clear()
                self.unit_combo.addItem("ជ្រើសរើស ឯកតា", None)

                for unit in units:
                    self.unit_combo.addItem(unit['name'], unit['id'])   # Store ID as userData
            else:
                raise Exception("No DB")
        except Exception as e:
            print("Error loading categories:", e)
            # self.category_combo.addItems(["Select Category", "Duck", "Pork", "Chicken", "Others"])

        # Set current category when editing
        if self.is_prefilled and self.product_data.get("unit"):
            unit_name = self.product_data.get("unit")
            index = self.unit_combo.findText(unit_name)
            if index >= 0:
                self.unit_combo.setCurrentIndex(index)
                

    def save_product(self):
        name = self.name_input.text().strip()
        category_id = self.category_combo.currentData()
        unit_id = self.unit_combo.currentData()
        price = self.price_input.value()
        user_id = self.get_user_id()
        description = self.description_input.toPlainText().strip()  # Get text from QTextEdit
        

        if not name:
            
            none_selected_warning(self,message="សូមបញ្ចូលឈ្នោះទំនិញ!",win_title="កំហុស")
            return

        if not category_id:
           
            none_selected_warning(self,message="សូមជ្រើសរើសប្រភេទទំនិញ!",win_title="កំហុស")
            return

        if not unit_id:
            
            none_selected_warning(self,message="សូមជ្រើសរើសឯកតា!",win_title="កំហុស")
            return

        if self.is_duplicate:
            app = getattr(self.parent_widget, "app", None)
            if app is not None and app.pro.name_exists(name):
                none_selected_warning(
                    self, win_title="ឈ្មោះដូចគ្នា", auto_close_ms=None,
                    message=f"មានទំនិញឈ្មោះ «{name}» រួចហើយ។\nសូមប្តូរឈ្មោះ (ឧ. បន្ថែមទម្ងន់ 4.5kg)។")
                self.name_input.setFocus()
                self.name_input.selectAll()
                return


        data = {
            "code": random.randint(100000, 999999),  # Generate a random code for the product
            "name": name,
            "category_id": category_id,          # ← Important: Send ID
            "unit_id":unit_id,
            "price": price,
            "created_by":user_id,
            "description": description
        }

        self.accept()
        return data