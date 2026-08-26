from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTableWidget, 
    QTableWidgetItem, QHBoxLayout, QLineEdit, QMessageBox,QDialog,QHeaderView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from .customer_dialog import CustomerDialog
from utils.style import BTN_SEARCH_STYLE,TABLE_STYLE,BTN_ADD,BTN_CANCEL,PAGE_TITLE_STYLE
from utils.dialog import confirm_delete,none_selected_warning,save_success_message

class CustomerWidget(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)


        # Search Bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 ស្វែងរកអតិថិជន...")
        self.search_input.setStyleSheet(BTN_SEARCH_STYLE)
        self.search_input.textChanged.connect(self.filter_table)
        layout.addWidget(self.search_input)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "អតិថិជន", "លេខទូរស័ព្ទ", "ហ្វេសប៊ុក", "តេឡេក្រាម", "ប្រភេទ", "អាសយដ្ឋាន"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self.edit_customer)
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.setFont(QFont(self.app.default_font_family, 10))
        head_table = self.table.horizontalHeader()
        head_table.setSectionResizeMode(1,QHeaderView.ResizeMode.ResizeToContents)
        head_table.setSectionResizeMode(2,QHeaderView.ResizeMode.ResizeToContents)
        head_table.setSectionResizeMode(3,QHeaderView.ResizeMode.ResizeToContents)
        head_table.setSectionResizeMode(4,QHeaderView.ResizeMode.ResizeToContents)
        head_table.setSectionResizeMode(5,QHeaderView.ResizeMode.ResizeToContents)
        head_table.setSectionResizeMode(6,QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        # Bottom Buttons
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("➕ បន្ថែមអតិថិជនថ្មី")
        add_btn.setStyleSheet(BTN_ADD)
        add_btn.clicked.connect(self.add_new_customer)
        
        delete_btn = QPushButton("🗑 លុបចេញ")
        delete_btn.setStyleSheet(BTN_CANCEL)
        delete_btn.clicked.connect(self.delete_selected)

        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.load_customers_from_db()

    def load_customers_from_db(self):
        """Load real data from database"""
        try:
            customers = self.app.cust.get_all_customers()
            self.table.setRowCount(len(customers))
            
            for row, customer in enumerate(customers):
                user_id = QTableWidgetItem(str(customer['id']))
                user_id.setData(Qt.UserRole,customer['id'])
                self.table.setItem(row, 0, user_id)
                self.table.setItem(row, 1, QTableWidgetItem(customer['name']))
                self.table.setItem(row, 2, QTableWidgetItem(customer['phone'] or ""))
                self.table.setItem(row, 3, QTableWidgetItem(customer['facebook'] or ""))
                self.table.setItem(row, 4, QTableWidgetItem(customer['telegram'] or ""))
                self.table.setItem(row, 5, QTableWidgetItem(customer['type'] or "New"))
                self.table.setItem(row, 6, QTableWidgetItem(customer['address']))
            self.table.setColumnHidden(0,True)
        except Exception as e:
            # QMessageBox.warning(self, "Database Error", f"Could not load customers:\n{str(e)}")
            none_selected_warning(self,message=f"មិនមានបញ្ជីអតិថិជន:\n{str(e)}",win_title="ឃ្លាំងផ្ទុកទិន្នន័យមានបញ្ហា")

    def load_sample_data(self):
        sample = [
            ["1", "សុី មករា", "0123456789", "ភ្នំពេញ", "facebook.com/si", "t.me/si", "New"],
            ["2", "ហេង សុភា", "0987654321", "សៀមរាប", "facebook.com/heng", "", "Regular"],
        ]
        self.table.setRowCount(len(sample))
        for row, data in enumerate(sample):
            for col, value in enumerate(data):
                self.table.setItem(row, col, QTableWidgetItem(value))

    def add_new_customer(self):
        dialog = CustomerDialog(self, title="អតិថិជនថ្មី")
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data["name"] and data["phone"]:
                try:
                    self.app.cust.add_customer(data)
                    self.load_customers_from_db()
                    
                    save_success_message(self,message="អតិថិជនថ្មីត្រូវបានបន្ថែម")
                except Exception as e:
                    
                    none_selected_warning(self,message="ការបន្ថែមមានបញ្ហា \n{str(e)}")
            else:
                
                none_selected_warning(self,message="ឈ្មោះអតិថិជន និងលេខទូរស័ព្ទ ត្រូវបានទាមទារ",win_title="មានកំហុសឆ្គង")
    def edit_customer(self, index):
        row = index.row()
        customer_id = int(self.table.item(row, 0).text())

        data = {
            "name": self.table.item(row, 1).text(),
            "phone": self.table.item(row, 2).text(),
            "address": self.table.item(row, 3).text(),
            "facebook": self.table.item(row, 4).text(),
            "telegram": self.table.item(row, 5).text(),
            "type": self.table.item(row, 6).text(),
        }

        dialog = CustomerDialog(self, "Edit Customer", data)
        if dialog.exec() == QDialog.Accepted:
            new_data = dialog.get_data()
            if new_data["name"] and new_data["phone"]:
                try:
                    self.app.cust.update_customer(customer_id, new_data)
                    self.load_customers_from_db()
                    save_success_message(self,message="ព័ត៌មានអតិថិជនត្រូវបានកែប្រែ")
                except Exception as e:
                    QMessageBox.warning(self, "Error", str(e))

    def delete_selected(self):
        selected = self.table.selectedItems()
        if not selected:
            none_selected_warning(self, message="សូមជ្រើសរើសទិន្នន័យដើម្បីលុប")
            return

        row = selected[0].row()
        id_item = self.table.item(row, 0)
        customer_id = id_item.data(Qt.UserRole) if id_item else None

        if customer_id is None:
            QMessageBox.critical(self, "Error", "Could not determine selected customer.")
            return

        customer_name_item = self.table.item(row, 1)   # adjust column index to wherever the name actually is
        customer_name = customer_name_item.text() if customer_name_item else ""

        if not confirm_delete(self, message=f"តើអ្នកពិតជាចង់លុបអតិថិជន '{customer_name}' មែនទេ?"):
            return

        try:
            self.app.cust.delete_customer(customer_id)
            self.load_customers_from_db()
            save_success_message(self,message="អតិថិជនត្រូវបានលុបចេញ")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete customer: {e}")

    def filter_table(self, text):
        """Simple search filter"""
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)