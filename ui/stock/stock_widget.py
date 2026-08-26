# ui/stock/stock_widget.py\
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox, QDoubleSpinBox,
    QLineEdit, QMessageBox, QHeaderView, QTabWidget, QFrame, QDialog, QFormLayout,QDateTimeEdit
)
from PySide6.QtCore import Qt,QDateTime
from PySide6.QtGui import QFont
from utils.style import TABLE_STYLE, TAB_STYLE, BTN_ADD, PAGE_TITLE_STYLE, BTN_SEARCH_STYLE,BTN_CANCEL,BTN_COMPLETE,BTN_SAVE,INPUT_STYLE
from utils.dialog import save_success_message, none_selected_warning
from .transferDialog import StockTransferDialog
from .stockAdjustDialog import StockAdjustDialog


class StockWidget(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(TAB_STYLE)

        self.tab_current = QWidget()
        self.setup_current_stock_tab()
        self.tabs.addTab(self.tab_current, "📦 ស្តុកបច្ចុប្បន្ន")

        self.tab_movement = QWidget()
        self.setup_movement_tab()
        self.tabs.addTab(self.tab_movement, "📜 ប្រវត្តិចូល/ចេញ")

        layout.addWidget(self.tabs)

    def refresh(self):
        self.load_brand_filter()
        self.load_stock()
        self.load_movements()

    # ==================== CURRENT STOCK TAB ====================
    def setup_current_stock_tab(self):
        layout = QVBoxLayout(self.tab_current)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Filter + action row
        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("សាខា:"))

        self.brand_filter_combo = QComboBox()
        self.brand_filter_combo.setStyleSheet(INPUT_STYLE)
        self.brand_filter_combo.setMinimumWidth(130)
        self.brand_filter_combo.currentIndexChanged.connect(self.load_stock)
        top_row.addWidget(self.brand_filter_combo)
        top_row.addStretch()

        stock_in_btn = QPushButton("📥 បញ្ចូលស្តុក")
        stock_in_btn.setStyleSheet(BTN_ADD)
        stock_in_btn.clicked.connect(lambda: self.open_stock_dialog('in'))
        top_row.addWidget(stock_in_btn)

        stock_out_btn = QPushButton("📤 ដកស្តុក")
        stock_out_btn.setStyleSheet(BTN_CANCEL)
        stock_out_btn.clicked.connect(lambda: self.open_stock_dialog('out'))


        transfer_btn = QPushButton("🔄 ផ្ទេរស្តុក")
        transfer_btn.setStyleSheet(BTN_SAVE)
        transfer_btn.clicked.connect(self.open_transfer_dialog)
        
        top_row.addWidget(stock_out_btn)
        top_row.addWidget(transfer_btn)
        layout.addLayout(top_row)

        # Stock table
        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(6)
        self.stock_table.setHorizontalHeaderLabels(["ID", "ផលិតផល", "សាខា","ចំនួនមុនបន្ថែម", "ចំនួនស្តុក","ឯកតា"])
        self.stock_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.stock_table.setAlternatingRowColors(True)
        self.stock_table.setStyleSheet(TABLE_STYLE)
        header = self.stock_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)

        self.stock_table.setColumnWidth(2,100)
        self.stock_table.setColumnWidth(3,100)
        self.stock_table.setColumnWidth(4,100)
        self.stock_table.setColumnWidth(5,100)
        
        layout.addWidget(self.stock_table)

        self.load_brand_filter()
        self.load_stock()


    def open_transfer_dialog(self):
        dialog = StockTransferDialog(self, self.app)
        if dialog.exec() == QDialog.Accepted:
            self.load_stock()
            self.load_movements()
            save_success_message(self, message="ផ្ទេរស្តុកជោគជ័យ")
            
    def load_brand_filter(self):
        current = self.brand_filter_combo.currentData() if self.brand_filter_combo.count() > 0 else None
        try:
            brands = self.app.brand.get_brands() or []
            
            self.brand_filter_combo.blockSignals(True)
            self.brand_filter_combo.clear()
            self.brand_filter_combo.addItem("គ្រប់សាខា", None)   # All brands

            for b in brands:
                # Store the real brand id as data
                self.brand_filter_combo.addItem(
                    b.get("name", ""), 
                    b.get("id")
                )

            # Restore previous selection if possible
            if current is not None:
                idx = self.brand_filter_combo.findData(current)
                if idx >= 0:
                    self.brand_filter_combo.setCurrentIndex(idx)

        except Exception as e:
            print("Load brand filter error:", e)
        finally:
            self.brand_filter_combo.blockSignals(False)

    def load_stock(self):
        
        
        try:
            brand_id = self.brand_filter_combo.currentData()
            stock_rows = self.app.stock.get_all_stock(brand_id)

            self.stock_table.setRowCount(len(stock_rows))

            for row, s in enumerate(stock_rows):
                # Column 0: ID (hidden)
                id_item = QTableWidgetItem(str(s['id']))
                id_item.setData(Qt.UserRole, s['product_id'])
                id_item.setData(Qt.UserRole + 1, s['brand_id'])
                self.stock_table.setItem(row, 0, id_item)

                # Column 1: Product name
                self.stock_table.setItem(row, 1, QTableWidgetItem(s['product_name']))

                # Column 2: Brand / Branch
                self.stock_table.setItem(row, 2, QTableWidgetItem(s['brand_name']))

                # Column 3: ចំនួនមុនបន្ថែម
                # Note: Current stock table normally doesn't have "previous quantity".
                # If you really need it, we can leave it empty or show "-" for now.
                prev_item = QTableWidgetItem("-")
                prev_item.setTextAlignment(Qt.AlignCenter)
                self.stock_table.setItem(row, 3, prev_item)

                # Column 4: Current quantity
                qty = s['quantity'] if s['quantity'] is not None else 0
                qty_item = QTableWidgetItem(f"{qty:,.0f}")
                qty_item.setTextAlignment(Qt.AlignCenter)
                if qty <= 0:
                    qty_item.setForeground(Qt.GlobalColor.red)
                elif qty <= 10:
                    qty_item.setForeground(Qt.GlobalColor.yellow)
                self.stock_table.setItem(row, 4, qty_item)  

                # Column 5: Unit
               
                unit_item = QTableWidgetItem(f"{s['unit_name']}")
                unit_item.setTextAlignment(Qt.AlignCenter)
                self.stock_table.setItem(row, 5, unit_item)

            self.stock_table.setColumnHidden(0, True)

        except Exception as e:
            print("Load stock error:", e)

    def open_stock_dialog(self, movement_type):
        dialog = StockAdjustDialog(self, self.app, movement_type)
        if dialog.exec() == QDialog.Accepted:
            self.load_stock()
            self.load_movements()
            save_success_message(self, message="ស្តុកត្រូវបានកែសម្រួល")

    # ==================== MOVEMENT HISTORY TAB ====================
    def setup_movement_tab(self):
        layout = QVBoxLayout(self.tab_movement)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # ========== Filter Row ==========
        filter_row = QHBoxLayout()

        filter_row.addWidget(QLabel("សាខា:"))
        self.movement_brand_combo = QComboBox()
        self.movement_brand_combo.setMinimumWidth(130)
        self.movement_brand_combo.setStyleSheet(INPUT_STYLE)
        self.movement_brand_combo.currentIndexChanged.connect(self.load_movements)
        filter_row.addWidget(self.movement_brand_combo)

        filter_row.addWidget(QLabel("ផលិតផល:"))
        self.movement_product_search = QLineEdit()
        self.movement_product_search.setPlaceholderText("ស្វែងរក...")
        self.movement_product_search.setMinimumWidth(140)
        self.movement_product_search.setStyleSheet(self._input_style())
        self.movement_product_search.textChanged.connect(self.load_movements)
        filter_row.addWidget(self.movement_product_search)

        filter_row.addWidget(QLabel("រយៈពេល:"))
        self.period_combo = QComboBox()
        self.period_combo.addItem("សព្វថ្ងៃ", "today")
        self.period_combo.addItem("សប្តាហ៍នេះ", "week")
        self.period_combo.addItem("ខែនេះ", "month")
        self.period_combo.addItem("ឆ្នាំនេះ", "year")
        self.period_combo.addItem("រយៈពេលផ្ទាល់ខ្លួន", "custom")
        self.period_combo.setStyleSheet(self._combo_style())
        self.period_combo.currentIndexChanged.connect(self.on_period_changed)
        filter_row.addWidget(self.period_combo)

        self.date_from = QDateTimeEdit(QDateTime.currentDateTime().addDays(-7))
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.date_from.setStyleSheet(self._input_style())
        self.date_from.dateTimeChanged.connect(self.load_movements)
        self.date_from.hide()
        filter_row.addWidget(self.date_from)

        self.date_to = QDateTimeEdit(QDateTime.currentDateTime())
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.date_to.setStyleSheet(self._input_style())
        self.date_to.dateTimeChanged.connect(self.load_movements)
        self.date_to.hide()
        filter_row.addWidget(self.date_to)

        filter_row.addWidget(QLabel("តម្រៀប:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItem("ថ្ងៃថ្មីបំផុត", "date_desc")
        self.sort_combo.addItem("ថ្ងៃចាស់បំផុត", "date_asc")
        self.sort_combo.addItem("ឈ្មោះផលិតផល", "product")
        self.sort_combo.setStyleSheet(self._combo_style())
        self.sort_combo.currentIndexChanged.connect(self.load_movements)
        filter_row.addWidget(self.sort_combo)

        filter_row.addStretch()
        layout.addLayout(filter_row)

        # ========== Table ==========
        self.movement_table = QTableWidget()
        self.movement_table.setColumnCount(7)
        self.movement_table.setHorizontalHeaderLabels(
            ["ប្រភេទ", "ផលិតផល", "សាខា", "ចំនួន", "មូលហេតុ", "ដំណើរការដោយ", "កាលបរិច្ឆេទ"]
        )
        self.movement_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.movement_table.setAlternatingRowColors(True)
        self.movement_table.setStyleSheet(TABLE_STYLE)
        self.movement_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.movement_table)

        self.load_movement_brand_filter()
        self.load_movements()

    def _combo_style(self):
        return """
            QComboBox {
                padding: 7px 10px; background-color: #1F1F1F; color: white;
                border: 1px solid #444; border-radius: 8px;
            }
        """

    def _input_style(self):
        return """
            QLineEdit {
                padding: 7px 10px; background-color: #1F1F1F; color: white;
                border: 1px solid #444; border-radius: 8px;
            }
        """

    def on_period_changed(self):
        
        is_custom = (self.period_combo.currentData() == "custom")
        self.date_from.setVisible(is_custom)
        self.date_to.setVisible(is_custom)
        self.load_movements()

    def load_movement_brand_filter(self):
        try:
            self.movement_brand_combo.blockSignals(True)
            self.movement_brand_combo.clear()
            self.movement_brand_combo.addItem("គ្រប់សាខា", None)

            brands = self.app.brand.get_brands() or []
            for b in brands:
                self.movement_brand_combo.addItem(b["name"], b["id"])
        except Exception as e:
            print("Load movement brand filter error:", e)
        finally:
            self.movement_brand_combo.blockSignals(False)
    
    def load_movements(self):
        
        
        try:
            brand_id = self.movement_brand_combo.currentData()
            product_search = self.movement_product_search.text().strip()
            period = self.period_combo.currentData()
            sort_by = self.sort_combo.currentData()

            date_from = None
            date_to = None
            if period == "custom":
                date_from = self.date_from.dateTime().toString("yyyy-MM-dd HH:mm:ss")
                date_to = self.date_to.dateTime().toString("yyyy-MM-dd HH:mm:ss")

            movements = self.app.stock.get_movements(
                brand_id=brand_id,
                product_search=product_search if product_search else None,
                period=period,
                date_from=date_from,
                date_to=date_to,
                sort_by=sort_by,
                limit=500
            )

            self.movement_table.setSortingEnabled(False)
            self.movement_table.setRowCount(len(movements))
            for row, m in enumerate(movements):
                type_label = "ចូល ⬆️" if m['movement_type'] == 'in' else "ចេញ ⬇️"
                type_item = QTableWidgetItem(type_label)
                type_item.setForeground(Qt.GlobalColor.green if m['movement_type'] == 'in' else Qt.GlobalColor.red)
                self.movement_table.setItem(row, 0, type_item)
                self.movement_table.setItem(row, 1, QTableWidgetItem(m['product_name']))
                self.movement_table.setItem(row, 2, QTableWidgetItem(m['brand_name']))
                self.movement_table.setItem(row, 3, QTableWidgetItem(f"{m['quantity']:,.2f}"))
                self.movement_table.setItem(row, 4, QTableWidgetItem(m['reason'] or ""))
                self.movement_table.setItem(row, 5, QTableWidgetItem(m['created_by_name']))
                self.movement_table.setItem(row, 6, QTableWidgetItem(str(m['created_at'])))
            self.movement_table.setSortingEnabled(True)
        except Exception as e:
            print("Load movements error:", e)


    def confirm_adjustment(self):
        brand_id = self.brand_combo.currentData()
        product_id = self.product_combo.currentData()
        quantity = self.quantity_input.value()
        reason = self.reason_input.text().strip()

        if not brand_id or not product_id:
            QMessageBox.warning(self, "Error", "សូមជ្រើសរើសសាខា និងផលិតផល")
            return
        if quantity <= 0:
            QMessageBox.warning(self, "Error", "ចំនួនត្រូវតែធំជាងសូន្យ")
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