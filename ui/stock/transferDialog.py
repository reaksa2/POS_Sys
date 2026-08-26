from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox, QDoubleSpinBox,
    QLineEdit, QMessageBox, QHeaderView, QTabWidget, QFrame, QDialog, QFormLayout
)
from PySide6.QtCore import Qt
from utils.dialog import none_selected_warning, save_success_message
from utils.style import BTN_ADD, BTN_CANCEL, INPUT_STYLE


class StockTransferDialog(QDialog):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._all_products = self.app.pro.get_all_products()

        self.setWindowTitle("ផ្ទេរស្តុក")
        self.setFixedSize(420, 420)
        self.setStyleSheet("background-color: #2A2A2A; color: white;")
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowCloseButtonHint
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("🔄 ផ្ទេរស្តុករវាងម៉ាក")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        # --- Category filter ---
        category_row = QHBoxLayout()
        category_row.addWidget(QLabel("ប្រភេទ:"))
        self.category_filter_combo = QComboBox()
        self.category_filter_combo.setStyleSheet(INPUT_STYLE)
        self.category_filter_combo.addItem("គ្រប់ប្រភេទ", None)
        for c in self.app.cate.get_all_category():
            self.category_filter_combo.addItem(c['name'], c['id'])
        self.category_filter_combo.currentIndexChanged.connect(self.filter_products_by_category)
        category_row.addWidget(self.category_filter_combo)

        # --- Searchable product combo ---
        self.product_combo = QComboBox()
        self.product_combo.setEditable(True)
        self.product_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.product_combo.setStyleSheet(INPUT_STYLE)
        self.product_combo.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        self.product_combo.completer().setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.load_product_combo()

        self.from_brand_combo = QComboBox()
        self.from_brand_combo.setStyleSheet(INPUT_STYLE)
        for b in self.app.brand.get_brands():
            self.from_brand_combo.addItem(b["name"], b["id"])

        self.to_brand_combo = QComboBox()
        self.to_brand_combo.setStyleSheet(INPUT_STYLE)
        for b in self.app.brand.get_brands():
            self.to_brand_combo.addItem(b["name"], b["id"])

        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setRange(0.01, 1000000)
        self.quantity_input.setValue(1)
        self.quantity_input.setStyleSheet(INPUT_STYLE)

        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText("ឧ. ផ្ទេរពី PP ទៅ SRP...")
        self.note_input.setStyleSheet(INPUT_STYLE)

        form.addRow("ប្រភេទ:", category_row)
        form.addRow("ផលិតផល:", self.product_combo)
        form.addRow("ពីម៉ាក:", self.from_brand_combo)
        form.addRow("ទៅម៉ាក:", self.to_brand_combo)
        form.addRow("ចំនួន:", self.quantity_input)
        form.addRow("កំណត់សម្គាល់:", self.note_input)
        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("បោះបង់")
        cancel_btn.setStyleSheet(BTN_CANCEL)
        cancel_btn.clicked.connect(self.reject)

        confirm_btn = QPushButton("✅ ផ្ទេរ")
        confirm_btn.setStyleSheet(BTN_ADD)
        confirm_btn.clicked.connect(self.confirm_transfer)

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

    def confirm_transfer(self):
        product_id = self.product_combo.currentData()
        from_brand_id = self.from_brand_combo.currentData()
        to_brand_id = self.to_brand_combo.currentData()
        quantity = self.quantity_input.value()
        note = self.note_input.text().strip()

        if not product_id or not from_brand_id or not to_brand_id:
            none_selected_warning(self, message="សូមជ្រើសរើសផលិតផល និងម៉ាក", win_title="មានកំហុស")
            return
        if from_brand_id == to_brand_id:
            none_selected_warning(self, message="ម៉ាកដើម និងម៉ាកគោលដៅ មិនអាចដូចគ្នាបានទេ", win_title="មានកំហុស")
            return

        try:
            user_id = self.app.user.get("id") if hasattr(self.app, "user") else None
            self.app.stock.transfer_stock(
                product_id=product_id,
                from_brand_id=from_brand_id,
                to_brand_id=to_brand_id,
                quantity=quantity,
                note=note,
                transferred_by=user_id
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))