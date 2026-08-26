from PySide6.QtWidgets import (
    QHBoxLayout, QDialog, QVBoxLayout, QLabel, QFormLayout,
    QComboBox, QDoubleSpinBox, QLineEdit, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt
from utils.dialog import save_success_message, none_selected_warning
from utils.style import BTN_ADD, BTN_CANCEL, INPUT_STYLE


class StockAdjustDialog(QDialog):
    def __init__(self, parent, app, movement_type):
        super().__init__(parent)
        self.app = app
        self._all_products = self.app.pro.get_all_products()
        self.movement_type = movement_type

        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowCloseButtonHint
        )

        title_text = "បញ្ចូលស្តុក" if movement_type == 'in' else "ដកស្តុក"
        self.setWindowTitle(title_text)
        self.setFixedSize(400, 380)
        self.setStyleSheet("background-color: #2A2A2A; color: white;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel(f"{'📥' if movement_type == 'in' else '📤'} {title_text}")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        self.brand_combo = QComboBox()
        self.brand_combo.setStyleSheet(INPUT_STYLE)
        for b in self.app.brand.get_brands():
            self.brand_combo.addItem(b['name'], b['id'])

        self.category_filter_combo = QComboBox()
        self.category_filter_combo.setStyleSheet(INPUT_STYLE)
        self.category_filter_combo.addItem("គ្រប់ប្រភេទ", None)
        for c in self.app.cate.get_all_category():
            self.category_filter_combo.addItem(c['name'], c['id'])
        self.category_filter_combo.currentIndexChanged.connect(self.filter_products_by_category)

        self.product_combo = QComboBox()
        self.product_combo.setEditable(True)
        self.product_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.product_combo.setStyleSheet(INPUT_STYLE)
        self.product_combo.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        self.product_combo.completer().setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.load_product_combo()

        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setRange(0.01, 1000000)
        self.quantity_input.setValue(1)
        self.quantity_input.setStyleSheet(INPUT_STYLE)

        self.reason_input = QLineEdit()
        self.reason_input.setPlaceholderText("ឧ. ទិញចូល, ខូចខាត, កែតម្រូវ...")
        self.reason_input.setStyleSheet(INPUT_STYLE)

        form.addRow("សាខា:", self.brand_combo)
        form.addRow("ប្រភេទ:", self.category_filter_combo)
        form.addRow("ផលិតផល:", self.product_combo)
        form.addRow("ចំនួន:", self.quantity_input)
        form.addRow("មូលហេតុ:", self.reason_input)
        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("បោះបង់")
        cancel_btn.setStyleSheet(BTN_CANCEL)
        cancel_btn.clicked.connect(self.reject)

        confirm_btn = QPushButton("✅ បញ្ជាក់")
        confirm_btn.setStyleSheet(BTN_ADD)
        confirm_btn.clicked.connect(self.confirm_adjustment)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(confirm_btn)
        layout.addLayout(btn_layout)

    def load_product_combo(self, category_id=None):
        self.product_combo.clear()
        for p in self._all_products:
            if category_id is None or p['category_id'] == category_id:
                self.product_combo.addItem(p['name'], p['id'])

    def filter_products_by_category(self):
        category_id = self.category_filter_combo.currentData()
        self.load_product_combo(category_id)

    def confirm_adjustment(self):
        brand_id = self.brand_combo.currentData()
        product_id = self.product_combo.currentData()
        quantity = self.quantity_input.value()
        reason = self.reason_input.text().strip()

        if not brand_id or not product_id:
            none_selected_warning(self, message="សូមជ្រើសរើសសាខា និងផលិតផល", win_title="មានកំហុស")
            return
        if quantity <= 0:
            none_selected_warning(self, message="ចំនួនត្រូវតែធំជាងសូន្យ", win_title="មានកំហុស")
            return

        try:
            user_id = self.app.user.get('id') if hasattr(self.app, 'user') else None
            self.app.stock.adjust_stock(
                product_id=product_id, brand_id=brand_id,
                movement_type=self.movement_type, quantity=quantity,
                reason=reason or ("បញ្ចូលស្តុក" if self.movement_type == 'in' else "ដកស្តុក"),
                created_by=user_id
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to adjust stock: {e}")