from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTableWidget, 
    QTableWidgetItem, QHBoxLayout, QLineEdit, QTabWidget,QDialog, QMessageBox,
    QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from utils.utils import (to_float)
from .product_dialog import ProductDialog
from .cate_dialog import CategoryDialog
from .unit_dialog import UnitDialog
from .taste_dialog import TasteDialog
from utils.style import TAB_STYLE,TABLE_STYLE,BTN_ADD,BTN_SAVE,BTN_SEARCH_STYLE,BTN_CANCEL,PAGE_TITLE_STYLE
from utils.dialog import confirm_delete, none_selected_warning,save_success_message

class ProductWidget(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.cat = self.app.cate.get_all_category()  # Load categories once for the widget
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(TAB_STYLE)

        # Tab 1: Products
        self.tab_products = QWidget()
        self.setup_products_tab()
        self.tabs.addTab(self.tab_products, "🛍️ បញ្ជីទំនិញ")

        # Tab 2: Product Prices
        self.add_on = QWidget()
        self.setup_addon_tab()
        self.tabs.addTab(self.add_on, "ផ្សេងៗ")

        layout.addWidget(self.tabs)


        self.load_category()
        self.load_unit()
        self.load_taste()

    def setup_products_tab(self):
        layout = QVBoxLayout(self.tab_products)

        # Search Bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ស្វែងរក...")
        self.search_input.setStyleSheet(BTN_SEARCH_STYLE)
        self.search_input.textChanged.connect(self.filter_products)
        layout.addWidget(self.search_input)

        self.product_table = QTableWidget()
        self.product_table.setColumnCount(6)
        self.product_table.setHorizontalHeaderLabels([ "ID", "ឈ្មោះទំនិញ","តម្លៃ","ឯកតា","ប្រភេទ", "ព័ត៌មានបន្ថែម" ])
        self.product_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.product_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.product_table.setFont(QFont(self.app.default_font_family, 10))
        self.product_table.verticalHeader().setVisible(True)
        self.product_table.setAlternatingRowColors(True)
        self.product_table.doubleClicked.connect(self.edit_product)
        self.product_table.setStyleSheet(TABLE_STYLE)
        head_pro_tab = self.product_table.horizontalHeader()
        head_pro_tab.setSectionResizeMode(1,QHeaderView.ResizeMode.Fixed)
        head_pro_tab.setSectionResizeMode(2,QHeaderView.ResizeMode.Fixed)
        head_pro_tab.setSectionResizeMode(3,QHeaderView.ResizeMode.Fixed)
        head_pro_tab.setSectionResizeMode(4,QHeaderView.ResizeMode.Fixed)
        head_pro_tab.setSectionResizeMode(5,QHeaderView.ResizeMode.Stretch)

        self.product_table.setColumnWidth(1,200)
        self.product_table.setColumnWidth(2,60)
        self.product_table.setColumnWidth(3,60)
        self.product_table.setColumnWidth(4,100)
       

        layout.addWidget(self.product_table)
        toolbar = QHBoxLayout()
        add_btn = QPushButton("➕ បន្ថែមមុខទំនិញថ្មី")
        add_btn.setStyleSheet(BTN_ADD)
        add_btn.clicked.connect(self.add_product)


        delete_btn = QPushButton("🗑 លុបចេញ")
        delete_btn.setStyleSheet(BTN_CANCEL)
        delete_btn.clicked.connect(self.delete_selected)


        toolbar.addWidget(add_btn)
        toolbar.addWidget(delete_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)


        self.load_products()

    

    # ==================== PRODUCTS TAB ====================
    def load_products(self):
        try:
            products = self.app.pro.get_all_products()
            self.product_table.setSortingEnabled(False)
            self.product_table.setRowCount(len(products))
            for row, product in enumerate(products):
                item_id = QTableWidgetItem(str(product['id']))
                item_id.setData(Qt.UserRole, product['id'])   # Hidden ID
                self.product_table.setItem(row, 0, item_id)
                self.product_table.setItem(row, 1, QTableWidgetItem(product['name']))
                self.product_table.setItem(row, 2, QTableWidgetItem(str(product['price'])))
                self.product_table.setItem(row, 3, QTableWidgetItem(product['unit'] or ""))
                self.product_table.setItem(row, 4, QTableWidgetItem(product['category'] or ""))
                self.product_table.setItem(row, 5, QTableWidgetItem(product['description'] or ""))
            # Hide ID column
            self.product_table.setColumnHidden(0, True)
            self.product_table.setSortingEnabled(True)
        except Exception as e:  

            print("Error loading products:", e)

    def add_product(self):
        dialog = ProductDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.save_product()
            if data:
                try:
                    self.app.pro.add_product(data)
                    self.load_products()
                    save_success_message(self,message="ទំនិញថ្មីត្រូវបានបន្ថែមដោយជោគជ័យ")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to add product: {e}")
            self.load_products()

    def edit_product(self, index):
        row = index.row() 
        product_id = self.product_table.item(row, 0).data(Qt.UserRole)
        price = to_float(self.product_table.item(row,2).text())
        data = {
            "name": self.product_table.item(row, 1).text(),
            "price": price,
            "unit": self.product_table.item(row, 3).text(),
            "category": self.product_table.item(row, 4).text(),
            "description": self.product_table.item(row, 5).text()
        }
        dialog = ProductDialog(self, product_data=data)
        if dialog.exec() == QDialog.Accepted:
            updated_data = dialog.save_product()
            if updated_data:
                try:
                    self.app.pro.update_product(product_id, updated_data)
                    self.load_products()
                    
                    save_success_message(self,message="ការកែប្រែជោគជ័យ")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to update product: {e}")

    def delete_selected(self):
        selected_rows = set(index.row() for index in self.product_table.selectedIndexes())
        if not selected_rows:
            
            none_selected_warning(self,message="សូមធ្វើការជ្រើសរើសទំនិញដើម្បីលុប")
            return

        
        confirm = confirm_delete(self,message="តើអ្នកពិតជាចង់លុបមែនទេ?")

        if confirm :
            try:
                for row in sorted(selected_rows, reverse=True):
                    product_id = self.product_table.item(row, 0).data(Qt.UserRole)
                    self.app.pro.delete_product(product_id)
                    self.product_table.removeRow(row)
                
                save_success_message(self,message="ទំនិញត្រូវបានលុបចេញ")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete products: {e}")


    def filter_products(self, text):
        """Simple search filter for products"""
        for row in range(self.product_table.rowCount()):
            match = False
            for col in range(self.product_table.columnCount()):
                item = self.product_table.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.product_table.setRowHidden(row, not match)
   



    def setup_addon_tab(self):

        cate_widget = QVBoxLayout(self.add_on)

        cols_widget = QHBoxLayout()


        # Category 
        cate_ver = QVBoxLayout()
        cate_ver.addWidget(QLabel("ប្រភេទទំនិញ"))
        self.cate_table = QTableWidget()
        self.cate_table.setColumnCount(3)
        self.cate_table.setHorizontalHeaderLabels(["ID","ឈ្មោះប្រភេទ","សម្អិត"])
        self.cate_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.cate_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.cate_table.setAlternatingRowColors(True)
        self.cate_table.setStyleSheet(TABLE_STYLE)
        self.cate_table.setFont(QFont(self.app.default_font_family, 10))
        self.cate_table.doubleClicked.connect(self.edit_cate)

        wrap_btn_cat = QHBoxLayout()

        self.btn_add_cate = QPushButton("បញ្ចូលប្រភេទថ្មី")
        self.btn_add_cate.setStyleSheet(BTN_ADD)
        self.btn_add_cate.clicked.connect(self.add_new_cate)

        self.btn_delelte_cate = QPushButton("លុបចេញ")
        self.btn_delelte_cate.setStyleSheet(BTN_CANCEL)
        self.btn_delelte_cate.clicked.connect(self.delete_selected_cate)

        cate_ver.addWidget(self.cate_table)
        wrap_btn_cat.addWidget(self.btn_add_cate)
        wrap_btn_cat.addWidget(self.btn_delelte_cate)
        wrap_btn_cat.addStretch()
        cate_ver.addLayout(wrap_btn_cat)
        cols_widget.addLayout(cate_ver)

        # Unit 
        unit_ver = QVBoxLayout()
        unit_ver.addWidget(QLabel("ឯកតា ទំនិញ"))
        self.unit_table = QTableWidget()
        self.unit_table.setColumnCount(3)
        self.unit_table.setHorizontalHeaderLabels(["ID","ឈ្មោះឯកតា","លម្អិត"])
        self.unit_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.unit_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.unit_table.setAlternatingRowColors(True)
        self.unit_table.setStyleSheet(TABLE_STYLE)
        self.unit_table.setFont(QFont(self.app.default_font_family, 10))
        self.unit_table.doubleClicked.connect(self.edit_unit)

        wrap_btn_unit = QHBoxLayout()
        self.btn_add_unit = QPushButton("បញ្ចូលឯកតាថ្មី")
        self.btn_add_unit.setStyleSheet(BTN_ADD)
        self.btn_add_unit.clicked.connect(self.add_new_unit)

        self.btn_delete_unit = QPushButton("លុបចេញ")
        self.btn_delete_unit.setStyleSheet(BTN_CANCEL)
        self.btn_delete_unit.clicked.connect(self.delete_selected_unit)


        unit_ver.addWidget(self.unit_table)

        wrap_btn_unit.addWidget(self.btn_add_unit)
        wrap_btn_unit.addWidget(self.btn_delete_unit)
        wrap_btn_unit.addStretch()
        unit_ver.addLayout(wrap_btn_unit)   
        cols_widget.addLayout(unit_ver)



        # Taste 

        taste_Ver = QVBoxLayout()

        taste_Ver.addWidget(QLabel("រសជាតិ"))



        self.taste_table = QTableWidget()
        self.taste_table.setColumnCount(3)
        self.taste_table.setHorizontalHeaderLabels(["ID","ឈ្មោះរសជាតិ","លម្អិត"])
        self.taste_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.taste_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.taste_table.setAlternatingRowColors(True)
        self.taste_table.setStyleSheet(TABLE_STYLE)
        self.taste_table.setFont(QFont(self.app.default_font_family, 10))
        self.taste_table.doubleClicked.connect(self.edit_taste)
        
        self.btn_add_taste = QPushButton("បញ្ចូលរសជាតិថ្មី")
        self.btn_add_taste.setStyleSheet(BTN_ADD)
        self.btn_add_taste.clicked.connect(self.add_new_taste)

        self.btn_delete_taste = QPushButton("លុបចេញ")
        self.btn_delete_taste.setStyleSheet(BTN_CANCEL)
        self.btn_delete_taste.clicked.connect(self.delete_selected_taste)

        taste_Ver.addWidget(self.taste_table)
        wrap_btn_taste = QHBoxLayout()
        wrap_btn_taste.addWidget(self.btn_add_taste)
        wrap_btn_taste.addWidget(self.btn_delete_taste)
        wrap_btn_taste.addStretch()
        taste_Ver.addLayout(wrap_btn_taste)
        cols_widget.addLayout(taste_Ver)
       


        cate_widget.addLayout(cols_widget)


    def load_category(self):
        try:
            cate = self.app.cate.get_all_category()

            self.cate_table.setRowCount(len(cate))
            for row, cate in enumerate(cate):
                cate_id = QTableWidgetItem(str(cate['id']))
                cate_id.setData(Qt.UserRole,cate['id'])
                self.cate_table.setItem(row,0,cate_id)
                self.cate_table.setItem(row,1,QTableWidgetItem(cate['name']))
                self.cate_table.setItem(row,2,QTableWidgetItem(cate['description'] or ""))
            self.cate_table.setColumnHidden(0,True)
        except Exception as e:
            print("error")


    def add_new_cate(self):
        cate_dialog = CategoryDialog(self)
        if cate_dialog.exec() == QDialog.Accepted:
            data = cate_dialog.save_cate()
            if data:
                try:
                    self.app.cate.add_category(data)
                    self.load_category()
                    save_success_message(self, "ប្រភេទទំនិញត្រូវបានបញ្ចូលដោយជោគជ័យ")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to add category: {e}")
    def edit_cate(self,index):
        row = index.row()

        row_id = self.cate_table.item(row,0).data(Qt.UserRole)

        data = {
            "cate_name" : self.cate_table.item(row,1).text(),
            "cate_des" : self.cate_table.item(row,2).text()
        }

        dialog = CategoryDialog(self, cate_data=data)
        if dialog.exec() == QDialog.Accepted:
            update_cate = dialog.save_cate()
            if update_cate:
                try:
                    self.app.cate.update_category(row_id,update_cate)

                    self.load_category()

                    save_success_message(self,"ប្រភេទទំនិញត្រូវបានកែប្រែដោយជោគជ័យ")
                except Exception as e:
                    QMessageBox.critical(self,"Error",f"Update Error {e}")
            

    
    # Unit 
    def load_unit(self):

        try:
            units = self.app.unit.get_all_unit()
            self.unit_table.setRowCount(len(units))

            for row,unit in enumerate(units):
                unit_id = QTableWidgetItem(str(unit['id']))
                unit_id.setData(Qt.UserRole,unit['id'])
                self.unit_table.setItem(row,0,unit_id)
                self.unit_table.setItem(row,1,QTableWidgetItem(unit["name"]))
                self.unit_table.setItem(row,2,QTableWidgetItem(unit["description"]))
            self.unit_table.setColumnHidden(0,True)


        except Exception as e:
            print("No data recored")

    def add_new_unit(self):
        dialog = UnitDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.save_data()
            if data:
                try:
                    self.app.unit.add_unit(data)
                    self.load_unit()
                    save_success_message(self, "ឯកតាទំនិញត្រូវបានបញ្ចូលដោយជោគជ័យ")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to add unit: {e}")
        
    def edit_unit(self,index):
        row = index.row()

        row_id = self.unit_table.item(row,0).data(Qt.UserRole)

        data = {
            "unit_name" : self.unit_table.item(row,1).text(),
            "unit_des" : self.unit_table.item(row,2).text()
        }

        dialog = UnitDialog(self, unit_data=data)
        if dialog.exec() == QDialog.Accepted:
            update = dialog.save_data()
            if update:
                try:
                    self.app.unit.update_unit(row_id,update)

                    self.load_unit()

                    save_success_message(self,"ឯកតាទំនិញត្រូវបានកែប្រែដោយជោគជ័យ")
                except Exception as e:
                    QMessageBox.critical(self,"Error",f"Update Error {e}")
    def load_taste(self):
        try:
            tastes = self.app.taste.get_all_taste()

            self.taste_table.setRowCount(len(tastes))
            for row, taste in enumerate(tastes):
                taste_id = QTableWidgetItem(str(taste['id']))
                taste_id.setData(Qt.UserRole,taste['id'])
                self.taste_table.setItem(row,0,taste_id)
                self.taste_table.setItem(row,1,QTableWidgetItem(taste["name"]))
                self.taste_table.setItem(row,2,QTableWidgetItem(taste["description"]))

            self.taste_table.setColumnHidden(0,True)

        except Exception as e:
            print("No Data recoed")

    def add_new_taste(self):
        dialog = TasteDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.save_data()
            if data:
                try:
                    self.app.taste.add_taste(data)
                    self.load_taste()
                    save_success_message(self, "រសជាតិត្រូវបានបញ្ចូលដោយជោគជ័យ")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to add taste: {e}")
        
    def edit_taste(self,index):
        row = index.row()

        row_id = self.taste_table.item(row,0).data(Qt.UserRole)

        data = {
            "taste_name" : self.taste_table.item(row,1).text(),
            "taste_des" : self.taste_table.item(row,2).text()
        }

        dialog = TasteDialog(self, taste_data=data)
        if dialog.exec() == QDialog.Accepted:
            update = dialog.save_data()
            if update:
                try:
                    self.app.taste.update_taste(row_id,update)

                    self.load_taste()

                    save_success_message(self, "រសជាតិត្រូវបានកែប្រែដោយជោគជ័យ")
                except Exception as e:
                    QMessageBox.critical(self,"Error",f"Update Error {e}")
    
        
    # Delete Group 
    def delete_selected_cate(self):
        selected_rows = set(index.row() for index in self.cate_table.selectedIndexes())
        if not selected_rows:
            none_selected_warning(self, "សូមជ្រើសរើសប្រភេទទំនិញយ៉ាងហោចណាស់មួយដើម្បីលុបចេញ")
            return

        if confirm_delete(self, f"តើអ្នកពិតជាចង់លុបប្រភេទទំនិញ {len(selected_rows)} ជួរមែនទេ?"):
            try:
                for row in sorted(selected_rows, reverse=True):
                    cate_id = self.cate_table.item(row, 0).data(Qt.UserRole)
                    self.app.cate.delete_category(cate_id)
                    self.cate_table.removeRow(row)
                save_success_message(self, "ប្រភេទទំនិញត្រូវបានលុបចេញ")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete categories: {e}")

    

    def delete_selected_unit(self):
        selected_rows = set(index.row() for index in self.unit_table.selectedIndexes())
        if not selected_rows:
            none_selected_warning(self, "សូមជ្រើសរើសឯកតាទំនិញយ៉ាងហោចណាស់មួយដើម្បីលុបចេញ")
            return

        if confirm_delete(self, f"តើអ្នកពិតជាចង់លុបឯកតាទំនិញ {len(selected_rows)} ជួរមែនទេ?"):
            try:
                for row in sorted(selected_rows, reverse=True):
                    unit_id = self.unit_table.item(row, 0).data(Qt.UserRole)
                    self.app.unit.delete_unit(unit_id)
                    self.unit_table.removeRow(row)
                save_success_message(self, "ឯកតាទំនិញត្រូវបានលុបចេញ")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete units: {e}")

    def delete_selected_taste(self):
        selected_rows = set(index.row() for index in self.taste_table.selectedIndexes())
        if not selected_rows:
            none_selected_warning(self, "សូមជ្រើសរើសរសជាតិយ៉ាងហោចណាស់មួយដើម្បីលុបចេញ")
            return

        if confirm_delete(self, f"តើអ្នកពិតជាចង់លុបរសជាតិ {len(selected_rows)} ជួរមែនទេ?"):
            try:
                for row in sorted(selected_rows, reverse=True):
                    taste_id = self.taste_table.item(row, 0).data(Qt.UserRole)
                    self.app.taste.delete_taste(taste_id)
                    self.taste_table.removeRow(row)
                save_success_message(self, "រសជាតិត្រូវបានលុបចេញ")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete tastes: {e}")
    