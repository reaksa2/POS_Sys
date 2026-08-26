from PySide6.QtWidgets import (
    QFrame, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QDateEdit, QTabWidget, QHeaderView
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont
from utils.style import INPUT_STYLE, PAGE_TITLE_STYLE, TAB_STYLE, TABLE_STYLE

class ReportWidget(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(TAB_STYLE)

        self.tab_daily = QWidget()
        self.setup_daily_tab()
        self.tabs.addTab(self.tab_daily, "📅 ប្រចាំថ្ងៃ")

        self.tab_monthly = QWidget()
        self.setup_monthly_tab()
        self.tabs.addTab(self.tab_monthly, "🗓️ ប្រចាំខែ")

        layout.addWidget(self.tabs)

    def refresh(self):
        self.load_daily_report()
        self.load_monthly_report()

    # ==================== DAILY TAB ====================
    def setup_daily_tab(self):
        layout = QVBoxLayout(self.tab_daily)
        controls = QHBoxLayout()
        controls.addWidget(QLabel("កាលបរិច្ឆេទ:"))
        self.daily_date = QDateEdit(QDate.currentDate())
        self.daily_date.setCalendarPopup(True)
        self.daily_date.dateChanged.connect(self.load_daily_report)
        self.daily_date.setMinimumWidth(100)
        self.daily_date.setStyleSheet(INPUT_STYLE)
        controls.addWidget(self.daily_date)
        controls.addStretch()
        layout.addLayout(controls)

        self.daily_summary_label = QLabel("សរុប: $0.00  |  ការកម្មង់: 0")
        self.daily_summary_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #22C55E;")
        layout.addWidget(self.daily_summary_label)

        row_layout = QHBoxLayout()
        frame_order = QFrame()
        frame_order.setStyleSheet("background-color: #2A2A2A; border-radius: 12px;")
        order_col = QVBoxLayout(frame_order)
        self.daily_orders_table = self.build_orders_table()
        order_col.addWidget(QLabel("ការកម្មង់"))
        order_col.addWidget(self.daily_orders_table)
        # order_col.addStretch()  ← removed

        frame_top_products = QFrame()
        frame_top_products.setStyleSheet("background-color: #2A2A2A;border-radius: 12px;")
        top_products_col = QVBoxLayout(frame_top_products)
        self.daily_top_products_table = self.build_top_products_table()
        top_products_col.addWidget(QLabel("ផលិតផលដែលបានលក់ច្រើនជាងគេ"))
        top_products_col.addWidget(self.daily_top_products_table)
        # top_products_col.addStretch()  ← removed

        row_layout.addWidget(frame_order, stretch=3)
        row_layout.addWidget(frame_top_products, stretch=2)
        layout.addLayout(row_layout)

        self.load_daily_report()

    def load_daily_report(self):
        date_str = self.daily_date.date().toString("yyyy-MM-dd")

        orders = self.app.order.get_daily_sales(date_str)
        self.populate_orders_table(self.daily_orders_table, orders)

        summary = self.app.order.get_sales_summary(date_str, date_str)
        self.daily_summary_label.setText(
            f"សរុប: ${summary['total_revenue']:,.2f}  |  ការកម្មង់: {summary['order_count']}"
        )

        top_products = self.app.order.get_top_products(date_str, date_str)
        self.populate_top_products_table(self.daily_top_products_table, top_products)

    # ==================== MONTHLY TAB ====================
    def setup_monthly_tab(self):
        layout = QVBoxLayout(self.tab_monthly)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("ខែ:"))
        self.monthly_date = QDateEdit(QDate.currentDate())
        self.monthly_date.setDisplayFormat("yyyy-MM")
        self.monthly_date.setCalendarPopup(True)
        self.monthly_date.setMinimumWidth(100)
        self.monthly_date.dateChanged.connect(self.load_monthly_report)
        self.monthly_date.setStyleSheet(INPUT_STYLE)
        controls.addWidget(self.monthly_date)
        controls.addStretch()
        layout.addLayout(controls)

        self.monthly_summary_label = QLabel("សរុប: $0.00  |  ការកម្មង់: 0")
        self.monthly_summary_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #22C55E;")
        layout.addWidget(self.monthly_summary_label)

        wrap_row = QHBoxLayout()
        frame_orders = QFrame()
        frame_orders.setStyleSheet("background-color: #2A2A2A; border-radius: 12px;")
        col_orders = QVBoxLayout(frame_orders)
        self.monthly_orders_table = self.build_orders_table()
        col_orders.addWidget(QLabel("ការកម្មង់"))
        col_orders.addWidget(self.monthly_orders_table)

        frame_top_products = QFrame()
        frame_top_products.setStyleSheet("background-color: #2A2A2A; border-radius: 12px;")
        col_top_products = QVBoxLayout(frame_top_products)
        self.monthly_top_products_table = self.build_top_products_table()
        col_top_products.addWidget(QLabel("ផលិតផលដែលបានលក់ច្រើនជាងគេ"))
        col_top_products.addWidget(self.monthly_top_products_table)
        wrap_row.addWidget(frame_orders, stretch=3)
        wrap_row.addWidget(frame_top_products, stretch=2)

        layout.addLayout(wrap_row)

        self.load_monthly_report()

    def load_monthly_report(self):
        year_month = self.monthly_date.date().toString("yyyy-MM")

        orders = self.app.order.get_monthly_sales(year_month)
        self.populate_orders_table(self.monthly_orders_table, orders)

        first_day = f"{year_month}-01"
        last_day = QDate.fromString(first_day, "yyyy-MM-dd").addMonths(1).addDays(-1).toString("yyyy-MM-dd")
        summary = self.app.order.get_sales_summary(first_day, last_day)
        self.monthly_summary_label.setText(
            f"សរុប: ${summary['total_revenue']:,.2f}  |  ការកម្មង់: {summary['order_count']}"
        )

        top_products = self.app.order.get_top_products(first_day, last_day)
        self.populate_top_products_table(self.monthly_top_products_table, top_products)

    # ==================== SHARED TABLE HELPERS ====================
    def build_orders_table(self):
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["លេខវិក្កយប័ត្រ #", "សរុប", "ថ្លៃដឹក", "បញ្ចុះតម្លៃ", "កាលបរិច្ឆេទ"])
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        header = table.horizontalHeader()
        header.setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1,QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2,QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3,QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4,QHeaderView.ResizeMode.ResizeToContents)
        header.resizeSection(1, 100)
        header.resizeSection(2, 60)
        header.resizeSection(3, 100)
        table.setStyleSheet(TABLE_STYLE)
        table.setFont(QFont(self.app.default_font_family, 10))
        table.setAlternatingRowColors(True)
        
        return table

    def populate_orders_table(self, table, orders):
        table.setSortingEnabled(False)
        table.setRowCount(len(orders))
        for row, o in enumerate(orders):
            table.setItem(row, 0, QTableWidgetItem(o['order_number'] or ""))
            table.setItem(row, 1, QTableWidgetItem(f"{o['total_amount']:,.2f} $"))
            table.setItem(row, 2, QTableWidgetItem(f"{o['delivery_fee']:,.2f} $"))
            table.setItem(row, 3, QTableWidgetItem(f"{o['discount']:,.2f} $"))
            table.setItem(row, 4, QTableWidgetItem(str(o['created_at'])))
        table.setSortingEnabled(True)

    def build_top_products_table(self):
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["ផលិតផល", "រសជាតិ", "ចំនួន", "ចំណូល"])
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        header = table.horizontalHeader()
        header.setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1,QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2,QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3,QHeaderView.ResizeMode.Fixed)
        header.resizeSection(1, 100)
        header.resizeSection(2, 60)
        header.resizeSection(3, 80)
        table.setAlternatingRowColors(True)
        table.setStyleSheet(TABLE_STYLE)
        table.setFont(QFont(self.app.default_font_family, 10))

        return table

    def populate_top_products_table(self, table, products):
        table.setSortingEnabled(False)
        table.setRowCount(len(products))
        for row, p in enumerate(products):
            table.setItem(row, 0, QTableWidgetItem(p['product_name'] or ""))
            table.setItem(row, 1, QTableWidgetItem(p['taste'] or ""))
            table.setItem(row, 2, QTableWidgetItem(f"{p['total_qty']:,.2f}"))
            table.setItem(row, 3, QTableWidgetItem(f"{p['total_revenue']:,.2f} $"))
        table.setSortingEnabled(True)