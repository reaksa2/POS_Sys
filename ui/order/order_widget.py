from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox, QLineEdit,
    QMessageBox, QHeaderView, QDoubleSpinBox,QDialog,QTabWidget, QFrame,QDateTimeEdit
)

from PySide6.QtPrintSupport import QPrinter, QPrintPreviewDialog,QPrinterInfo
from PySide6.QtGui import QTextDocument, QPageSize, QPageLayout, QFont,QColor,QKeySequence
from PySide6.QtCore import QMarginsF, Qt,QSizeF,QDateTime

from utils.utils import (to_float)
from ..customer.customer_dialog import CustomerDialog
from .order_detail_dialog import OrderDetailDialog
from .invoice_preview_dialog import InvoicePreviewDialog
from .invoice_template import build_receipt_html
from utils.style import (INPUT_STYLE, TABLE_STYLE,TAB_STYLE,BTN_ADD,BTN_CANCEL,BTN_EDIT,BTN_SAVE,BTN_SEARCH_STYLE,PAGE_TITLE_STYLE)
from utils.dialog import confirm_delete,save_success_message,none_selected_warning

class OrderWidget(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.editing_order_id = None          # ← Add this
        self.current_items = []

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(TAB_STYLE)

        # Tab 1: Ordering
        self.tab_ordering = QWidget()
        self.tab_ordering_setup()
        self.tabs.addTab(self.tab_ordering, "🛍️ ការកម្មង់")

        # Tab 2: Active orders
        self.tab_active = QWidget()
        self.active_orders_table = self.build_orders_table()
        QVBoxLayout(self.tab_active).addWidget(self.active_orders_table)
        self.tabs.addTab(self.tab_active, "🟡 រងចាំ")

        # Tab 3: History
        self.tab_history = QWidget()
        self.history_orders_table = self.build_orders_table()
        col_history = QVBoxLayout(self.tab_history)

        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)

        filter_layout.addWidget(QLabel("ចាប់ពី:"))
        self.start_date_filter = QDateTimeEdit(QDateTime.currentDateTime().addDays(-7))
        self.start_date_filter.setCalendarPopup(True)
        self.start_date_filter.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.start_date_filter.setStyleSheet(self._spinbox_style())
        self.start_date_filter.dateTimeChanged.connect(self.load_history)
        self.start_date_filter.setMinimumWidth(150)
        self.start_date_filter.setStyleSheet("border: 1px solid #444;border-radius:8px;background-color:#1F1F1F")
        filter_layout.addWidget(self.start_date_filter)

        filter_layout.addWidget(QLabel("ដល់:"))
        self.end_date_filter = QDateTimeEdit(QDateTime.currentDateTime())
        self.end_date_filter.setCalendarPopup(True)
        self.end_date_filter.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.end_date_filter.setStyleSheet(self._spinbox_style())
        self.end_date_filter.dateTimeChanged.connect(self.load_history)
        self.end_date_filter.setMinimumWidth(150)
        self.end_date_filter.setStyleSheet("border: 1px solid #444;border-radius:8px;background-color:#1F1F1F")
       
        filter_layout.addWidget(self.end_date_filter)

        filter_layout.addStretch()

        # Summary stats, same row
        self.history_summary_label = QLabel("ចំនួនកម្មង់: 0  |  ចំណូលសរុប: $0.00")
        self.history_summary_label.setStyleSheet("color: #22C55E; font-size: 12px; font-weight: bold;")
        filter_layout.addWidget(self.history_summary_label)

        col_history.addLayout(filter_layout)
        col_history.addWidget(self.history_orders_table)

        self.tabs.addTab(self.tab_history, "📜 ប្រវត្តិកម្មង់")

        main_layout.addWidget(self.tabs)

        self.load_products()
        self.load_category_filter()
        self.load_tastes()
        self.load_customers()
        self.load_order_lists()   # ← populate Active/History tables on startup too
        self.load_defaults()

        

    def refresh(self):
        self.load_products()
        self.load_category_filter()
        self.load_tastes()
        self.refresh_order_table()
        self.load_order_lists()
        self.load_history()
        self.load_customers()
        self.load_defaults()
        self._cached_default_brand_id = None   # ← confirm this line exists, resets cache on every page revisit
    def load_order_lists(self):
        active = self.app.order.get_orders("pending")
        self.populate_orders_table(self.active_orders_table, active)
    def tab_ordering_setup(self):
        tab_ordering = QHBoxLayout(self.tab_ordering)
        table_font = QFont()
        table_font.setPointSize(9)
        # ==================== LEFT: Products ====================
        left_card = QFrame()
        left_card.setStyleSheet("background-color: #2A2A2A; border-radius: 12px;")
        left = QVBoxLayout(left_card)
       
        left.setSpacing(12)

       
        left_title = QLabel("🛍️ ទំនិញ")
        left_title.setStyleSheet(PAGE_TITLE_STYLE)
        left.addWidget(left_title)

        # Search + Category filter row
        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 ស្វេងរកទំនិញ...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #1F1F1F; color: white; padding: 8px 10px;
                border-radius: 8px; border: 1px solid #444; font-size: 14px;
            }
            QLineEdit:focus { border: 1px solid #8B5A2B; }
        """)
        self.search_input.textChanged.connect(self.filter_products)
        filter_row.addWidget(self.search_input, stretch=2)

        self.category_filter_combo = QComboBox()
        self.category_filter_combo.setStyleSheet("""
            QComboBox {
                background-color: #1F1F1F; color: white; padding: 8px 10px;
                border-radius: 8px; border: 1px solid #444; font-size: 14px;
            }
        """)
        self.category_filter_combo.currentIndexChanged.connect(self.filter_products)
        filter_row.addWidget(self.category_filter_combo, stretch=1)

        left.addLayout(filter_row)

        self.product_table = QTableWidget()
        self.product_table.setFont(table_font)
        self.product_table.setColumnCount(4)
        self.product_table.setHorizontalHeaderLabels(["ID", "ទំនិញ", "ឯកតា", "តម្លៃ"])
        self.product_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.product_table.setFont(QFont(self.app.default_font_family, 10))
        self.product_table.setAlternatingRowColors(True)
        self.product_table.doubleClicked.connect(self.add_selected_product)

        self.product_table.setStyleSheet(TABLE_STYLE)
        

        pro_header = self.product_table.horizontalHeader()
        pro_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        pro_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        pro_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        left.addWidget(self.product_table)

        hint = QLabel("💡 ចុចពីរដងដើម្បីដាក់ទៅបញ្ចីកម្មង់")
        hint.setStyleSheet("color: #777; font-size: 12px;")
        left.addWidget(hint)

        tab_ordering.addWidget(left_card, stretch=1)

        # ==================== RIGHT: Current Order ====================
        right_card = QFrame()
        right_card.setStyleSheet("background-color: #2A2A2A; border-radius: 12px;")
        right = QVBoxLayout(right_card)
        

        right_title = QLabel("📋 បញ្ចីកម្មង់")
        right_title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        right.addWidget(right_title)

        # Customer row
        cl = QHBoxLayout()
        cl.setSpacing(10)
        self.customer_combo = QComboBox()
        self.customer_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 10px; background-color: #1F1F1F; color: white;
                border: 1px solid #444; border-radius: 8px; font-size: 14px;
            }
        """)
        cl.addWidget(self.customer_combo, stretch=1)

        add_customer = QPushButton("＋ បន្ថែមអតិថិជនថ្មី")
        add_customer.setStyleSheet(BTN_ADD)
        add_customer.clicked.connect(self.add_new_customer)
        cl.addWidget(add_customer)
        right.addLayout(cl)

        # Order table
        self.order_table = QTableWidget()
        self.order_table.setFont(table_font)
        self.order_table.setColumnCount(8)
        self.order_table.setHorizontalHeaderLabels(
            ["product_id", "ទំនិញ", "រសជាតិ", "ឯកតា", "ចំនួន", "តម្លៃរាយ($)", "តម្លៃសរុប($)",""]
        )
        self.order_table.itemChanged.connect(self.on_order_item_changed)
        self.order_table.setFont(QFont(self.app.default_font_family, 10))
        header = self.order_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self.order_table.setColumnWidth(2, 150)
        self.order_table.setColumnWidth(5, 100)
        self.order_table.setColumnWidth(6, 100)
        self.order_table.setColumnWidth(7, 40)
        self.order_table.keyPressEvent = self.order_table_key_press
        self.order_table.setStyleSheet(TABLE_STYLE)
        right.addWidget(self.order_table, stretch=1)

        # Delivery / Discount row
        dl = QHBoxLayout()
        dl.setSpacing(20)

        delivery_col = QVBoxLayout()
        delivery_col.setSpacing(4)
        delivery_label = QLabel("🚚 ថ្លៃដឹក")
        delivery_label.setStyleSheet("color: #999; font-size: 12px;")
        delivery_col.addWidget(delivery_label)
        self.delivery_input = QDoubleSpinBox()
        self.delivery_input.setRange(0, 1000000)
        self.delivery_input.setSuffix(" $")
        self.delivery_input.setSingleStep(1)
        self.delivery_input.setStyleSheet(self._spinbox_style())
        self.delivery_input.setFixedWidth(200)
        self.delivery_input.setValue(float(self.app.settings.get("default_delivery", 0) or 0))
        self.delivery_input.valueChanged.connect(self.update_total)
        delivery_col.addWidget(self.delivery_input)
        dl.addLayout(delivery_col)


        discount_col = QVBoxLayout()
        discount_col.setSpacing(4)
        discount_label = QLabel("🏷️ បញ្ចុះតម្លៃ")
        discount_label.setStyleSheet("color: #999; font-size: 12px;")
        discount_col.addWidget(discount_label)


        self.discount = QDoubleSpinBox()
        self.discount.setRange(0, 100)          # ← was (0, 1000000)
        self.discount.setSuffix(" %")           # ← was " $"
        self.discount.setSingleStep(1)
        self.discount.setStyleSheet(self._spinbox_style())
        self.discount.valueChanged.connect(self.update_total)
        self.discount.setFixedWidth(200)
        self.discount.setValue(float(self.app.settings.get("default_discount", 0) or 0))

        discount_col.addWidget(self.discount)
        dl.addLayout(discount_col)

        pickup_col = QVBoxLayout()
        pickup_col.setSpacing(4)
        pickup_label = QLabel("🕒 ម៉ោងទទួល")
        pickup_label.setStyleSheet("color: #999; font-size: 12px;")
        pickup_col.addWidget(pickup_label)
        self.pickup_time_input = QDateTimeEdit()
        self.pickup_time_input.setDateTime(QDateTime.currentDateTime())
        self.pickup_time_input.setCalendarPopup(True)
        self.pickup_time_input.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.pickup_time_input.setStyleSheet("""
            QDateTimeEdit {
                padding: 4px 5px; background-color: #1F1F1F; color: white;
                border: 1px solid #444; border-radius: 8px; font-size: 14px;
            }
        """)
        self.pickup_time_input.setFixedWidth(200)
        pickup_col.addWidget(self.pickup_time_input)
        dl.addLayout(pickup_col)




        dl.addStretch()
        right.addLayout(dl)



        # Payment & Pickup row
        pp = QHBoxLayout()
        pp.setSpacing(20)

        payment_col = QVBoxLayout()
        payment_col.setSpacing(4)
        payment_label = QLabel("💳 វិធីបង់ប្រាក់")
        payment_label.setStyleSheet("color: #999; font-size: 12px;")
        payment_col.addWidget(payment_label)
        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItems(["Cash", "ABA", "ACLEDA", "Wing", "TrueMoney"])
        self.payment_method_combo.setStyleSheet("""
            QComboBox {
                padding: 4px 5px; background-color: #1F1F1F; color: white;
                border: 1px solid #444; border-radius: 8px; font-size: 14px;
            }
        """)
        self.payment_method_combo.setFixedWidth(200)
        payment_col.addWidget(self.payment_method_combo)
        pp.addLayout(payment_col)

        status_col = QVBoxLayout()
        status_col.setSpacing(4)
        status_label = QLabel("💰 ស្ថានភាពបង់ប្រាក់")
        status_label.setStyleSheet("color: #999; font-size: 12px;")
        status_col.addWidget(status_label)
        self.payment_status_combo = QComboBox()
        self.payment_status_combo.addItems(["unpaid", "deposit", "paid"])
        self.payment_status_combo.setStyleSheet("""
            QComboBox {
                padding: 4px 5px; background-color: #1F1F1F; color: white;
                border: 1px solid #444; border-radius: 8px; font-size: 14px;
            }
        """)
        self.payment_status_combo.setFixedWidth(200)
        self.payment_status_combo.currentTextChanged.connect(self.on_payment_status_changed)
        status_col.addWidget(self.payment_status_combo)
        pp.addLayout(status_col)

        paid_col = QVBoxLayout()
        paid_col.setSpacing(4)
        paid_label = QLabel("💵 ចំនួនបានបង់")
        paid_label.setStyleSheet("color: #999; font-size: 12px;")
        paid_col.addWidget(paid_label)
        self.paid_amount_input = QDoubleSpinBox()
        self.paid_amount_input.setRange(0, 1000000)
        self.paid_amount_input.setSuffix(" $")
        self.paid_amount_input.setEnabled(False)   # only editable when status = deposit
        self.paid_amount_input.setStyleSheet(self._spinbox_style())
        self.paid_amount_input.setFixedWidth(200)
        self.paid_amount_input.valueChanged.connect(self.update_total)
        paid_col.addWidget(self.paid_amount_input)
        pp.addLayout(paid_col)

        
        pp.addStretch()
        right.addLayout(pp)
        # Total
        self.total_label = QLabel("Total: $0.00")
        self.total_label.setTextFormat(Qt.TextFormat.RichText)   # ← add this
        self.total_label.setStyleSheet("font-size: 12px;")        # base size, spans override where needed
        right.addWidget(self.total_label)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        clear_btn = QPushButton("🗑️ សម្អាត")
        clear_btn.setStyleSheet(self._button_style("#4B5563", "#6B7280"))
        clear_btn.clicked.connect(self.clear_order)

        place_save_btn = QPushButton("💾 រក្សាទុក")
        place_save_btn.setStyleSheet(self._button_style("#3B82F6", "#2563EB"))
        place_save_btn.clicked.connect(self.place_order_pending)

        place_btn = QPushButton("✅ កម្មង់")
        place_btn.setStyleSheet(self._button_style("#22C55E", "#16A34A"))
        place_btn.clicked.connect(self.place_order_completed)

        btn_layout.addWidget(clear_btn)
        btn_layout.addWidget(place_save_btn)
        btn_layout.addWidget(place_btn, stretch=1)
        right.addLayout(btn_layout)

        tab_ordering.addWidget(right_card, stretch=2)
# ======================= Load category_filter_combo ===============================
    def load_category_filter(self):
        try:
            categories = self.app.cate.get_all_category()
            self.category_filter_combo.blockSignals(True)   # prevent triggering filter_products during population
            self.category_filter_combo.clear()
            self.category_filter_combo.addItem("គ្រប់ប្រភេទ", None)   # "All Categories"
            for c in categories:
                self.category_filter_combo.addItem(c['name'], c['id'])
            self.category_filter_combo.blockSignals(False)
        except Exception as e:
            print("Load category filter error:", e)

    
    # def filter_products(self, text):
    #     """Hide rows that don't match the search text (searches Product and Taste columns)"""
    #     text = text.lower().strip()
    #     for row in range(self.product_table.rowCount()):
    #         match = False
    #         for col in (1, 2):  # search "ទំនិញ" (Product) and "រសជាតិ" (Taste) columns
    #             item = self.product_table.item(row, col)
    #             if item and text in item.text().lower():
    #                 match = True
    #                 break
    #         self.product_table.setRowHidden(row, not match)
    def filter_products(self, *args):
        text = self.search_input.text().lower().strip()
        selected_category_id = self.category_filter_combo.currentData()

        for row in range(self.product_table.rowCount()):
            # Text match (searches product name column)
            name_item = self.product_table.item(row, 1)
            text_match = (not text) or (name_item and text in name_item.text().lower())

            # Category match
            id_item = self.product_table.item(row, 0)
            row_category_id = id_item.data(Qt.UserRole + 1) if id_item else None
            category_match = (selected_category_id is None) or (row_category_id == selected_category_id)

            self.product_table.setRowHidden(row, not (text_match and category_match))

    def _spinbox_style(self):
        return """
            QDoubleSpinBox {
                padding: 4px 5px; background-color: #1F1F1F; color: white;
                border: 1px solid #444; border-radius: 8px; font-size: 14px;
            }
        """

    def _button_style(self, bg, hover):
        return f"""
            QPushButton {{
                background-color: {bg}; color: white; padding: 12px 20px;
                border: none; border-radius: 8px; font-size: 15px; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {hover}; }}
        """
# ========================================== Group Taste function ===================================================
    def load_tastes(self):
        try:
            self.available_tastes = [t['name'] for t in self.app.taste.get_all_taste()]
        except Exception as e:
            self.available_tastes = []
    def on_taste_text_changed(self, row, text):
        """Live update as user types/selects — keeps current_items in sync without saving new taste yet"""
        if row >= len(self.current_items):
            return
        self.current_items[row]['taste'] = text

    def on_taste_confirmed(self, row, combo):
        """Fires when user finishes typing (Enter/focus-out) — if it's a brand-new taste, save it to DB"""
        text = combo.currentText().strip()
        if not text:
            return
        if text not in self.available_tastes:
            try:
                self.app.taste.add_taste({"taste_name": text, "taste_des": ""})
                self.available_tastes.append(text)
            except Exception as e:
                
                none_selected_warning(self,message=f"មិនអាចរក្សាទុក រសជាតិថ្មី \n {e}",win_title="មានកំហុស")
        if row < len(self.current_items):
            self.current_items[row]['taste'] = text

    # ========================================== End Group Taste function ===================================================
   
    # def load_products(self):
    #     products = self.app.pro.get_all_products()
    #     self.product_table.setRowCount(len(products))
    #     for row, p in enumerate(products):
    #         pp_id = QTableWidgetItem(str(p['id']))
    #         pp_id.setData(Qt.UserRole, p['id'])
    #         pp_id.setData(Qt.UserRole + 1, p['category_id'])
    #         self.product_table.setItem(row, 0, pp_id)
    #         self.product_table.setItem(row, 1, QTableWidgetItem(p['name'] or ""))
    #         self.product_table.setItem(row, 2, QTableWidgetItem(p['unit'] or ""))
    #         self.product_table.setItem(row, 3, QTableWidgetItem(f"{p['price']:,.2f} $"))
    #     self.product_table.setColumnHidden(0, True)
    def load_products(self):
        brand_id = self.app.user.get('brand_id') if hasattr(self.app, 'user') else None
        if not brand_id:
            brand_id = self.get_default_brand_id()

        if not brand_id:
            # No brand available at all — nothing can be sold under strict stock rules
            self.product_table.setRowCount(0)
            return

        try:
            products = self.app.stock.get_available_products_for_brand(brand_id)
        except Exception as e:
            print("Load products error:", e)
            products = []

        self.product_table.setSortingEnabled(False)
        self.product_table.setRowCount(len(products))

        LOW_STOCK_THRESHOLD = 2

        for row, p in enumerate(products):
            pp_id = QTableWidgetItem(str(p['id']))
            pp_id.setData(Qt.UserRole, p['id'])
            pp_id.setData(Qt.UserRole + 1, p['category_id'])
            self.product_table.setItem(row, 0, pp_id)

            name_item = QTableWidgetItem(p['name'] or "")
            stock_qty = p['stock_qty']
            if 0 < stock_qty <= LOW_STOCK_THRESHOLD:
                name_item.setForeground(QColor("#F59E0B"))
                name_item.setToolTip(f"នៅសល់ត្រឹមតែ {stock_qty:,.0f} ប៉ុណ្ណោះ")
            self.product_table.setItem(row, 1, name_item)

            self.product_table.setItem(row, 2, QTableWidgetItem(p['unit'] or ""))
            self.product_table.setItem(row, 3, QTableWidgetItem(f"{p['price']:,.2f} $"))

        self.product_table.setColumnHidden(0, True)
        self.product_table.resizeColumnsToContents()
        if self.product_table.columnWidth(2) > 100:
            self.product_table.setColumnWidth(2, 100)
        self.product_table.resizeRowsToContents()
        self.product_table.setSortingEnabled(True)


    def load_customers(self):
        try:
            customers = self.app.cust.get_customer_name()
            self.customer_combo.clear()
            self.customer_combo.addItem("អតិថិជន", None)
            for c in customers:
                self.customer_combo.addItem(c['name'], c['id'])
        except Exception as e:
            print("DB Error", e)
            self.customer_combo.addItem("Walk-in Customer", None)

    def add_selected_product(self):
        row = self.product_table.currentRow()
        if row < 0:
            return

        id_item = self.product_table.item(row, 0)
        name_item = self.product_table.item(row, 1)
        unit_item = self.product_table.item(row, 2)
        price_item = self.product_table.item(row, 3)

        if not all([id_item, name_item, unit_item, price_item]):
            none_selected_warning(self, message="មិនអាចជ្រើសរើសទំនិញបាន")
            return

        p_id = id_item.data(Qt.UserRole)
        name = name_item.text()
        unit = unit_item.text()
        price_text = price_item.text().replace("$", "").replace(",", "").strip()
        price = to_float(price_text)

        # --- Stock check ---
        available_stock = self.get_available_stock(p_id)
        if available_stock is not None:
            already_in_cart = sum(i['quantity'] for i in self.current_items if i['price_id'] == p_id)
            if already_in_cart + 1 > available_stock:
                none_selected_warning(
                    self,
                    message=f"ស្តុកមិនគ្រប់គ្រាន់! នៅសល់ត្រឹមតែ {available_stock:,.0f} ប៉ុណ្ណោះ\n"
                            f"(មានក្នុងកន្ត្រកចំនួន {already_in_cart:,.0f} រួចហើយ)",
                    win_title="ស្តុកមិនគ្រប់គ្រាន់"
                )
                return

        self.current_items.append({
            "price_id": p_id,
            "name": name,
            "taste": "",
            "unit": unit,
            "quantity": 1.0,
            "price": price
        })
        self.refresh_order_table()

    def get_available_stock(self, product_id):
        """Returns the tracked stock quantity for this product under the current brand, or None if untracked."""
        brand_id = self.app.user.get('brand_id') if hasattr(self.app, 'user') else None
        if not brand_id:
            brand_id = self.get_default_brand_id()
        if not brand_id:
            return None
        try:
            return self.app.stock.get_stock(product_id, brand_id)
        except Exception as e:
            print("Get available stock error:", e)
            return None

    def refresh_order_table(self):
        self.order_table.blockSignals(True)
        self.order_table.setRowCount(len(self.current_items))
        for row, item in enumerate(self.current_items):
            id_item = QTableWidgetItem(str(item['price_id']))
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
            self.order_table.setItem(row, 0, id_item)

            name_item = QTableWidgetItem(item['name'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.order_table.setItem(row, 1, name_item)

            # --- Taste: searchable, editable combobox ---
            taste_combo = QComboBox()
            taste_combo.setEditable(True)
            taste_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)  # don't auto-insert on Enter; we handle it manually
            taste_combo.addItem("")  # empty = not selected
            for t in self.available_tastes:
                taste_combo.addItem(t)
            if item.get('taste'):
                idx = taste_combo.findText(item['taste'])
                if idx >= 0:
                    taste_combo.setCurrentIndex(idx)
                else:
                    taste_combo.setCurrentText(item['taste'])
            taste_combo.setStyleSheet("""
                QComboBox {
                    background-color: #1F1F1F; color: white;
                    border: 1px solid #444; border-radius: 4px; padding: 2px 6px;
                }
            """)
            taste_combo.currentTextChanged.connect(
                lambda text, r=row: self.on_taste_text_changed(r, text)
            )
            taste_combo.lineEdit().editingFinished.connect(
                lambda r=row, combo=taste_combo: self.on_taste_confirmed(r, combo)
            )
            self.order_table.setCellWidget(row, 2, taste_combo)

            unit_item = QTableWidgetItem(str(item['unit']))
            unit_item.setFlags(unit_item.flags() & ~Qt.ItemIsEditable)
            self.order_table.setItem(row, 3, unit_item)

            qty_item = QTableWidgetItem(str(f"{item['quantity']:,.2f}"))
            qty_item.setFlags(qty_item.flags() | Qt.ItemIsEditable)
            self.order_table.setItem(row, 4, qty_item)

            price_item = QTableWidgetItem(str(f"{item['price']:,.2f}"))
            price_item.setFlags(price_item.flags() | Qt.ItemIsEditable)
            self.order_table.setItem(row, 5, price_item)

            subtotal = item['price'] * item['quantity']
            subtotal_item = QTableWidgetItem(f"{subtotal:,.2f}")
            subtotal_item.setFlags(subtotal_item.flags() & ~Qt.ItemIsEditable)
            self.order_table.setItem(row, 6, subtotal_item)
            # --- Remove button ---
            remove_btn = QPushButton("✖")
            remove_btn.setFixedWidth(30)
            remove_btn.setStyleSheet("""
                QPushButton {
                    background-color: #EF4444; color: white;
                    border: none; border-radius: 4px; font-weight: bold;
                }
                QPushButton:hover { background-color: #DC2626; }
            """)
            remove_btn.clicked.connect(lambda checked, r=row: self.remove_order_item(r))
            self.order_table.setCellWidget(row, 7, remove_btn)

        self.order_table.setColumnHidden(0, True)
        self.order_table.blockSignals(False)
        self.update_total()

    def update_total(self):
        if not hasattr(self, 'total_label'):
            return

        items_total = sum(item['price'] * item['quantity'] for item in self.current_items)
        discount_percent = self.discount.value()
        delivery_fee = self.delivery_input.value()

        discount_amount = items_total * (discount_percent / 100)
        discounted_total = max(items_total - discount_amount, 0)
        total = discounted_total + delivery_fee

        # Value color, label stays muted/white
        v = "#FCD34D"   # amber/gold for key numbers
        label_color = "#CCCCCC"

        line1 = (
            f"<span style='color:{label_color};'>ក្រោយបញ្ចុះតម្លៃនិងបូកថ្លៃដឹក:</span> "
            f"<span style='color:#22C55E; font-weight:bold; font-size:16px;'>{total:,.2f} $</span> "
            f"<span style='color:{label_color};'>"
            f"(សរុប <span style='color:{v};'>{items_total:,.2f}</span> − "
            f"<span style='color:{v};'>{discount_percent:.0f}%</span> បញ្ចុះតម្លៃ = "
            f"<span style='color:#EF4444;'>-{discount_amount:,.2f}</span> + "
            f"ថ្លៃដឹក <span style='color:{v};'>{delivery_fee:,.2f}</span>)"
            f"</span>"
        )

        # Optional: show remaining balance if payment_status widget exists and is "deposit"
        if hasattr(self, 'payment_status_combo') and self.payment_status_combo.currentText() == "deposit":
            paid = self.paid_amount_input.value()
            remaining = max(total - paid, 0)
            line2 = (
                f"<br><span style='color:{label_color};'>បានបង់:</span> "
                f"<span style='color:#3B82F6; font-weight:bold;'>-{paid:,.2f} $</span>"
                f"<span style='color:{label_color};'> | នៅសល់:</span> "
                f"<span style='color:#F59E0B; font-weight:bold;'>{remaining:,.2f} $</span>"
            )
            line1 += line2

        self.total_label.setText(line1)

    def on_order_item_changed(self, item):
        row = item.row()
        col = item.column()
        if row >= len(self.current_items):
            return

        if col == 4:  # Qty
            try:
                new_qty = float(item.text())
                if new_qty <= 0:
                    raise ValueError

                price_id = self.current_items[row]['price_id']
                available_stock = self.get_available_stock(price_id)
                if available_stock is not None:
                    # Check against OTHER rows of the same product too (in case of multiple taste rows)
                    other_rows_qty = sum(
                        i['quantity'] for idx, i in enumerate(self.current_items)
                        if idx != row and i['price_id'] == price_id
                    )
                    if other_rows_qty + new_qty > available_stock:
                        none_selected_warning(
                            self,
                            message=f"ស្តុកមិនគ្រប់គ្រាន់! អាចដាក់បានត្រឹមតែ {available_stock - other_rows_qty:,.0f} ប៉ុណ្ណោះ",
                            win_title="ស្តុកមិនគ្រប់គ្រាន់"
                        )
                        self.refresh_order_table()   # revert to previous value
                        return

                self.current_items[row]['quantity'] = new_qty
            except ValueError:
                none_selected_warning(self, message="បរិមាណត្រូវតែជាលេខហើយធំជាងមួយ")

        elif col == 5:  # Price
            try:
                new_price = float(item.text().replace(',', ''))
                if new_price < 0:
                    raise ValueError
                self.current_items[row]['price'] = new_price
            except ValueError:
                none_selected_warning(self, message="តម្លៃត្រូវតែបញ្ចូលហើយជាលេខ")

        self.refresh_order_table()

    def remove_order_item(self, row):
        if row < 0 or row >= len(self.current_items):
            return
        item_name = self.current_items[row]['name']
        confirm = confirm_delete(self,f"តើអ្នកចង់លុប '{item_name}' ចេញពីបញ្ជីកម្មង់មែនទេ?")
        if confirm:
            del self.current_items[row]
            self.refresh_order_table()

    def order_table_key_press(self, event):
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            row = self.order_table.currentRow()
            if row >= 0:
                self.remove_order_item(row)
        else:
            QTableWidget.keyPressEvent(self.order_table, event)
    # ================== 
    # SAVE Product 
    # ===================

    def place_order_pending(self):
        """Save button — goes to Active tab as pending"""
        self._submit_order(status='pending', success_msg="ការកម្មង់ត្រូវបានរក្សាទុកបណ្ដោះអាសន្ន!")

    def place_order_completed(self):
        customer_id = self.customer_combo.currentData()
        if not self.current_items:
            none_selected_warning(self,message="មិនមានទំនិញ")
            return
        if customer_id is None:
            none_selected_warning(self,message="សូមជ្រើសរើសឈ្មោះអតិថិជន")
            return

        # Fetch full customer info instead of hardcoding blanks
        try:
            customer = self.app.cust.get_customer_by_id(customer_id)
            customer = dict(customer) if customer else {}
        except Exception as e:
            print("Failed to load customer info:", e)
            customer = {}

        missing_taste = [i['name'] for i in self.current_items if not i.get('taste')]

        if missing_taste:
            none_selected_warning(self,message="សូមជ្រើសរើសរសជាតិសម្រាប់ទំនិញ:\n" + "\n".join(missing_taste),win_title="សូមជ្រើសរើសរសជាតិ",auto_close_ms=None)
           
            return

        # Build a preview HTML using current cart data (order not saved yet)
        preview_order = {
            "order_number": "PREVIEW",
            "customer_name": self.customer_combo.currentText(),
            "created_at": "",
            "delivery_fee": self.delivery_input.value(),
            "discount": sum(i['price'] * i['quantity'] for i in self.current_items) * (self.discount.value() / 100),
            "total_amount": self._calc_total(),
            "phone": customer.get("phone", ""),
            "telegram": customer.get("telegram", ""),
            "facebook": customer.get("facebook", ""),
            "address": customer.get("address", ""),
            "payment_method": self.payment_method_combo.currentText(),
            "payment_status": self.payment_status_combo.currentText(),
            "paid_amount": self.paid_amount_input.value(),
            "pickup_time": self.pickup_time_input.dateTime().toString("yyyy-MM-dd HH:mm"),
        }
        preview_items = [
            {"product_name": i['name'], "taste": i['taste'], "unit": i['unit'],
                "quantity": i['quantity'], "unit_price": i['price'], "subtotal": i['price'] * i['quantity']}
            for i in self.current_items
        ]
        html = build_receipt_html(self.app, preview_order, preview_items)

        dialog = InvoicePreviewDialog(self, html)
        if dialog.exec() != QDialog.Accepted:
            return

        order_id = self._submit_order(status='completed', success_msg="ការកម្មង់ជោគជ័យ")
        if order_id:
            self.auto_print_order(order_id)

    def _calc_total(self):
        items_total = sum(i['price'] * i['quantity'] for i in self.current_items)
        # discount_amount = items_total * (self.discount.value() / 100)
        return max(items_total , 0)

    

    def _submit_order(self, status, success_msg):
        customer_id = self.customer_combo.currentData()
        if not self.current_items:
            none_selected_warning(self, message="មិនមានទំនិញក្នុងបញ្ជី")
            return None
        if customer_id is None:
            none_selected_warning(self, message="សូមជ្រើសរើសអតិថិជន")
            return None
        missing_taste = [i['name'] for i in self.current_items if not i.get('taste')]
        if missing_taste:
            none_selected_warning(
                self, message="សូមជ្រើសរើសរសជាតិសម្រាប់ទំនិញ:\n" + "\n".join(missing_taste),
                win_title="សូមជ្រើសរើសរសជាតិ", auto_close_ms=None
            )
            return None

        items_total = sum(item['price'] * item['quantity'] for item in self.current_items)
        delivery_fee = self.delivery_input.value()
        discount_percent = self.discount.value()
        discount_amount = items_total * (discount_percent / 100)
        order_by = self.app.user.get('id') if hasattr(self.app, 'user') else None

        # Determine brand_id: use user's own brand, or fall back to the first active brand
        brand_id = self.app.user.get('brand_id') if hasattr(self.app, 'user') else None
        if not brand_id:
            brand_id = self.get_default_brand_id()

        # --- Final stock check before committing (only for completed orders) ---
        if status == 'completed':
            stock_errors = []
            product_totals = {}
            for i in self.current_items:
                if i.get('price_id'):
                    product_totals[i['price_id']] = product_totals.get(i['price_id'], 0) + i['quantity']

            for price_id, total_qty in product_totals.items():
                available = self.get_available_stock(price_id)
                if available is not None and total_qty > available:
                    item_name = next((i['name'] for i in self.current_items if i['price_id'] == price_id), "?")
                    stock_errors.append(f"{item_name}: ត្រូវការ {total_qty:,.0f}, នៅសល់ {available:,.0f}")

            if stock_errors:
                none_selected_warning(
                    self,
                    message="ស្តុកមិនគ្រប់គ្រាន់សម្រាប់ទំនិញខាងក្រោម:\n" + "\n".join(stock_errors),
                    win_title="ស្តុកមិនគ្រប់គ្រាន់", auto_close_ms=None
                )
                return None

        payment_method = self.payment_method_combo.currentText()
        payment_status = self.payment_status_combo.currentText()
        paid_amount = self.paid_amount_input.value()
        pickup_time = self.pickup_time_input.dateTime().toString("yyyy-MM-dd HH:mm")

        try:
            if self.editing_order_id:
                order_id = self.editing_order_id
                self.app.order.update_order(
                    order_id=order_id, customer_id=customer_id, items=self.current_items,
                    delivery_fee=delivery_fee, discount=discount_amount, status=status,
                    payment_method=payment_method, payment_status=payment_status,
                    paid_amount=paid_amount, pickup_time=pickup_time,
                    brand_id=brand_id, updated_by=order_by
                )
                save_success_message(self, message="ការធ្វើបច្ចុប្បន្នភាពជោគជ័យ")
                self.editing_order_id = None
            else:
                order_id = self.app.order.place_order(
                    customer_id, self.current_items, delivery_fee, discount_amount, order_by,
                    status=status, payment_method=payment_method, payment_status=payment_status,
                    paid_amount=paid_amount, pickup_time=pickup_time,
                    brand_id=brand_id
                )
                save_success_message(self, message=success_msg)

            self.clear_order()
            self.load_products()
            self.load_order_lists()
            self.tabs.setCurrentIndex(0)
            return order_id

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save order: {e}")
            return None

    def get_default_brand_id(self):
        if hasattr(self, '_cached_default_brand_id') and self._cached_default_brand_id:
            return self._cached_default_brand_id
        try:
            brands = self.app.brand.get_brands()
            if brands:
                self._cached_default_brand_id = brands[0]['id']
                return self._cached_default_brand_id
        except Exception as e:
            print("Get default brand error:", e)
        return None


    
    def load_defaults(self):
        try:
            delivery = float(self.app.settings.get("default_delivery", 0) or 0)
            discount = float(self.app.settings.get("default_discount", 0) or 0)
            self.delivery_input.setValue(delivery)
            self.discount.setValue(discount)
        except Exception as e:
            print("Load defaults error:", e)

    def clear_order(self):
        self.current_items.clear()
        self.load_defaults()   # resets delivery + discount to saved settings
        self.payment_method_combo.setCurrentIndex(0)
        self.payment_status_combo.setCurrentIndex(0)
        self.paid_amount_input.setValue(0)
        self.pickup_time_input.setDateTime(QDateTime.currentDateTime())
        self.refresh_order_table()

    def load_defaults(self):
        try:
            delivery = float(self.app.settings.get("default_delivery", 0) or 0)
            discount = float(self.app.settings.get("default_discount", 0) or 0)
            self.delivery_input.setValue(delivery)
            self.discount.setValue(discount)
        except Exception as e:
            print("Load defaults error:", e)

    def on_payment_status_changed(self, status):
        self.paid_amount_input.setEnabled(status == "deposit")
        if status == "paid":
            items_total = sum(i['price'] * i['quantity'] for i in self.current_items)
            discount_amount = items_total * (self.discount.value() / 100)
            self.paid_amount_input.setValue(self._calc_total() + self.delivery_input.value()- discount_amount)
        elif status == "unpaid":
            self.paid_amount_input.setValue(0)
            
    def build_orders_table(self):
        table = QTableWidget()
        table.setFont(QFont(self.app.default_font_family, 10))
        table.setColumnCount(10)
        table.setHorizontalHeaderLabels(
            ["ID","ស្ថានភាព","លេខវិក្កយបត្រ #", "អតិថិជន", "តម្លៃសរុប","បានបង់","បញ្ចុះតម្លៃ", "ថ្លៃដឹក","តម្លៃចុងក្រោយ","កាលបរិច្ឆេទទទួល"]
        )
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        activ_order = table.horizontalHeader()
        activ_order.setSectionResizeMode(1,QHeaderView.ResizeMode.Fixed)
        activ_order.setSectionResizeMode(2,QHeaderView.ResizeMode.Stretch)
        activ_order.setSectionResizeMode(3,QHeaderView.ResizeMode.Stretch)
        activ_order.setSectionResizeMode(4,QHeaderView.ResizeMode.Fixed)
        activ_order.setSectionResizeMode(5,QHeaderView.ResizeMode.Fixed)
        activ_order.setSectionResizeMode(6,QHeaderView.ResizeMode.Fixed)
        activ_order.setSectionResizeMode(7,QHeaderView.ResizeMode.Fixed)
        activ_order.setSectionResizeMode(8,QHeaderView.ResizeMode.Fixed)
        activ_order.setSectionResizeMode(9,QHeaderView.ResizeMode.ResizeToContents)

        table.setColumnWidth(1,100)
        table.setColumnWidth(4,100)
        table.setColumnWidth(5,100)
        table.setColumnWidth(6,100)
        table.setColumnWidth(7,100)
        table.setColumnWidth(8,100)
        
        table.setAlternatingRowColors(True)
        table.setStyleSheet(TABLE_STYLE)
        table.doubleClicked.connect(lambda idx, t=table: self.open_order_detail(t, idx))
        return table

    def load_order_lists(self):
        active = self.app.order.get_orders("pending")
        history = self.app.order.get_orders_history()
        self.populate_orders_table(self.active_orders_table, active)
        self.populate_orders_table(self.history_orders_table, history)

    def populate_orders_table(self, table, orders):
        table.setSortingEnabled(False)
        table.setRowCount(len(orders))
        for row, o in enumerate(orders):
            id_item = QTableWidgetItem(str(o['id']))
            id_item.setData(Qt.UserRole, o['id'])
            last_total = to_float(self._last_total(o['total_amount'],o['paid_amount'],o['discount'],o['delivery_fee']))
            status_item = QTableWidgetItem(o['status'].capitalize())
            total_item = QTableWidgetItem(f"{last_total:,.2f} $")
            
            status_colors = {
                'pending': QColor("#F59E0B"),     # amber
                'completed': QColor("#22C55E"),   # green
                'cancelled': QColor("#EF4444"),   # red
            }
            status_item.setForeground(status_colors.get(o['status'], QColor("#CCCCCC")))
            total_item.setForeground(QColor("#22C55E"))  # amber/gold for key numbers

            table.setItem(row, 0, id_item)
            table.setItem(row, 1, status_item)
            table.setItem(row, 2, QTableWidgetItem(o['order_number'] or ""))
            table.setItem(row, 3, QTableWidgetItem(o['customer_name'] or ""))
            table.setItem(row, 4, QTableWidgetItem(f"{o['total_amount']:,.2f} $"))
            table.setItem(row, 5, QTableWidgetItem(f"{o['paid_amount']:,.2f} $"))
            table.setItem(row, 6, QTableWidgetItem(f"{o['discount']:,.2f} $"))
            table.setItem(row, 7, QTableWidgetItem(f"{str(o['delivery_fee'])} $"))
            table.setItem(row, 8, total_item)
            table.setItem(row, 9, QTableWidgetItem(str(o['pickup_time'])))
        table.setColumnHidden(0, True)
        table.setSortingEnabled(True)


    def _last_total(self,total=0,deposit = 0, discount = 0, delivery = 0):

        return total - (deposit + discount) + delivery

    def open_order_detail(self, table, index):
        row = index.row()
        order_id = table.item(row, 0).data(Qt.UserRole)
        dialog = OrderDetailDialog(self, self.app, order_id)
        dialog.exec()
        print(f"DEBUG after exec: dialog.status_changed = {dialog.status_changed}")   # ← temp
        if dialog.status_changed:
            self.load_products() 
            self.load_order_lists()
            self.load_history()
        else:
            print("DEBUG: status_changed was False, skipping refresh")   # ← temp

    def add_new_customer(self):
        dialog = CustomerDialog(self)
        if dialog.exec() == QDialog.Accepted and dialog.get_data():
            try:
                new_id = self.app.cust.add_customer(dialog.get_data())
                self.load_customers()
                index = self.customer_combo.findData(new_id)
                if index >= 0:
                    self.customer_combo.setCurrentIndex(index)
               
                save_success_message(self,message="អតិថិជនបានបញ្ចូលនិងជ្រើសរើស")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add customer: {e}")



    def load_order_for_edit(self, order_id):
        try:
            order = self.app.order.get_order_by_id(order_id)
            items = self.app.order.get_order_items(order_id)

            # Convert to normal dict so we can use .get() safely
            order = dict(order)

            self.editing_order_id = order_id
            self.current_items = []

            for it in items:
                item = dict(it)   # convert Row → dict

                self.current_items.append({
                    "price_id": item.get('product_id') or item.get('id') or 0,
                    "name": item.get('product_name') or item.get('name') or "",
                    "taste": item.get('taste') or "",
                    "unit": item.get('unit') or "",
                    "quantity": float(item.get('quantity') or 1),
                    "price": float(item.get('unit_price') or item.get('price') or 0),
                    "weight": item.get('weight')
                })

            # Set customer
            index = self.customer_combo.findData(order.get('customer_id'))
            if index >= 0:
                self.customer_combo.setCurrentIndex(index)

            # Set delivery
            self.delivery_input.setValue(float(order.get('delivery_fee') or 0))

            # Convert discount amount → percent
            items_total = sum(i['price'] * i['quantity'] for i in self.current_items)
            if items_total > 0:
                discount_amount = float(order.get('discount') or 0)
                discount_percent = (discount_amount / items_total) * 100
                self.discount.setValue(round(discount_percent, 1))
            else:
                self.discount.setValue(0)

            index_payment = self.payment_method_combo.findText(order.get('payment_method', 'Cash'))
            if index_payment >= 0:
                self.payment_method_combo.setCurrentIndex(index_payment)

            index_status = self.payment_status_combo.findText(order.get('payment_status', 'unpaid'))
            if index_status >= 0:
                self.payment_status_combo.setCurrentIndex(index_status)

            self.paid_amount_input.setValue(float(order.get('paid_amount') or 0))

            pickup_str = order.get('pickup_time')
            if pickup_str:
                dt = QDateTime.fromString(pickup_str, "yyyy-MM-dd HH:mm")
                if dt.isValid():
                    self.pickup_time_input.setDateTime(dt)
            else:
                self.pickup_time_input.setDateTime(QDateTime.currentDateTime())

            self.refresh_order_table()
            self.tabs.setCurrentIndex(0)


        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load order for edit:\n{e}")

    def auto_print_order(self, order_id):
        try:
            order = self.app.order.get_order_by_id(order_id)
            items = self.app.order.get_order_items(order_id)
            html = build_receipt_html(self.app, order, items)

            doc = QTextDocument()
            doc.setDefaultFont(QFont("Consolas", 11))
            doc.setHtml(html)

            printer = QPrinter(QPrinter.HighResolution)

            saved_printer_name = self.app.settings.get("receipt_printer", "")
            available_printers = QPrinterInfo.availablePrinterNames()

            target_printer_name = None
            if saved_printer_name and saved_printer_name in available_printers:
                target_printer_name = saved_printer_name
            elif printer.printerName() and printer.printerName() in available_printers:
                target_printer_name = printer.printerName()

            if not target_printer_name:
                # QMessageBox.warning(
                #     self, "គ្មានម៉ាស៊ីនបោះពុម្ព",
                #     "មិនមានម៉ាស៊ីនបោះពុម្ពសម្រាប់វិក្កយបត្រទេ។\n\n"
                #     "ការកម្មង់បានរក្សាទុកដោយជោគជ័យ ប៉ុន្តែមិនអាចបោះពុម្ពបាន។\n"
                #     "សូមកំណត់ម៉ាស៊ីនបោះពុម្ពនៅ Settings → Printer ។"
                # )
                none_selected_warning(
                    self,
                    message=f"មិនមានម៉ាស៊ីនបោះពុម្ពសម្រាប់វិក្កយបត្រទេ។\n\n"
                            "ការកម្មង់បានរក្សាទុកដោយជោគជ័យ ប៉ុន្តែមិនអាចបោះពុម្ពបាន។\n"
                            "សូមកំណត់ម៉ាស៊ីនបោះពុម្ពនៅ Settings → Printer ។",
                    win_title="គ្មានម៉ាស៊ីនបោះពុម្ព"
                    )
                return

            printer.setPrinterName(target_printer_name)

            a5_size = QPageSize(QSizeF(148, 210), QPageSize.Millimeter, "A5 Custom")
            printer.setPageSize(a5_size)
            printer.setPageOrientation(QPageLayout.Portrait)
            printer.setPageMargins(QMarginsF(8, 8, 8, 8), QPageLayout.Millimeter)
            doc.setPageSize(printer.pageRect(QPrinter.Point).size())

            success = doc.print_(printer)
            if not success:
                # QMessageBox.warning(
                #     self, "បរាជ័យក្នុងការបោះពុម្ព",
                #     f"ការកម្មង់បានរក្សាទុកដោយជោគជ័យ ប៉ុន្តែបរាជ័យក្នុងការបោះពុម្ពទៅកាន់ '{target_printer_name}'។\n"
                #     "សូមពិនិត្យមើលថាតើម៉ាស៊ីនបោះពុម្ពនោះកំពុងដំណើរការឬអត់។"
                # )

                none_selected_warning(
                    self,
                    message=f"ការកម្មង់បានរក្សាទុកដោយជោគជ័យ ប៉ុន្តែបរាជ័យក្នុងការបោះពុម្ពទៅកាន់ '{target_printer_name}'។\n"
                    "សូមពិនិត្យមើលថាតើម៉ាស៊ីនបោះពុម្ពនោះកំពុងដំណើរការឬអត់។"
                )

        except Exception as e:
            # QMessageBox.warning(self, "Print Error", f"ការកម្មង់បានរក្សាទុកដោយជោគជ័យ ប៉ុន្តែបរាជ័យក្នុងការបោះពុម្ព:\n{e}")
            none_selected_warning(
                self,
                message=f"ការកម្មង់បានរក្សាទុកដោយជោគជ័យ ប៉ុន្តែបរាជ័យក្នុងការបោះពុម្ព:\n{e}"
            )


    def print_order_receipt(self, order_id):
        try:
            order = self.app.order.get_order_by_id(order_id)
            items = self.app.order.get_order_items(order_id)
            html = build_receipt_html(self.app, order, items)

            doc = QTextDocument()
            font = QFont("Consolas", 11)
            doc.setDefaultFont(font)
            doc.setHtml(html)

            printer = QPrinter(QPrinter.HighResolution)
            a5_size = QPageSize(QSizeF(148, 210), QPageSize.Millimeter, "A5 Custom")
            printer.setPageSize(a5_size)
            printer.setPageOrientation(QPageLayout.Portrait)
            printer.setPageMargins(QMarginsF(8, 8, 8, 8), QPageLayout.Millimeter)

            page_rect = printer.pageRect(QPrinter.Point)
            doc.setPageSize(page_rect.size())

            preview = QPrintPreviewDialog(printer, self)

            def paint(p):
                p.setPageSize(a5_size)
                p.setPageOrientation(QPageLayout.Portrait)
                doc.setPageSize(p.pageRect(QPrinter.Point).size())
                doc.print_(p)

            preview.paintRequested.connect(paint)
            preview.exec()
        except Exception as e:
            QMessageBox.critical(self, "Print Error", f"Failed to print receipt: {e}")

    def load_history(self):
        # Keep end date current unless user has manually changed it
        if not getattr(self, '_end_date_manually_set', False):
            self.end_date_filter.blockSignals(True)
            self.end_date_filter.setDateTime(QDateTime.currentDateTime())
            self.end_date_filter.blockSignals(False)

        start_str = self.start_date_filter.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        end_str = self.end_date_filter.dateTime().toString("yyyy-MM-dd HH:mm:ss")

        orders = self.app.order.get_orders_history_by_range(start_str, end_str)
        self.populate_orders_table(self.history_orders_table, orders)

        summary = self.app.order.get_history_summary_by_range(start_str, end_str)
        self.history_summary_label.setText(
            f"ចំនួនកម្មង់: {summary['order_count']}  |  "
            f"ចំណូលសរុប: ${summary['total_revenue']:,.2f}"
            + (f"  |  លុបចោល: {summary['cancelled_count']}" if summary['cancelled_count'] > 0 else "")
        )