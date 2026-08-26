import os
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QFormLayout, QTabWidget, QDoubleSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QMessageBox, QDialog, QDialogButtonBox, QFrame,
    QFileDialog, QGroupBox, QScrollArea,QCheckBox,QApplication
)

from PySide6.QtGui import QPixmap,QTextDocument, QPageSize, QPageLayout, QFont
from PySide6.QtCore import Qt,QSizeF, QMarginsF
from PySide6.QtPrintSupport import QPrinterInfo,QPrinter

from utils.style import BTN_SAVE,BTN_ADD,BTN_CANCEL, INPUT_STYLE, TABLE_STYLE,BTN_NEUTRAL,BTN_PRINT,TAB_STYLE
from utils.dialog import save_success_message,none_selected_warning,confirm_delete
from .userDialog import UserDialog

from utils.backup import backup_database
class SettingsWidget(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(TAB_STYLE)

        self.tab_business = QWidget()
        self.setup_business_tab()
        self.tabs.addTab(self.tab_business, "🏢 អាជីវកម្ម")

        self.tab_defaults = QWidget()
        self.setup_defaults_tab()
        self.tabs.addTab(self.tab_defaults, "💰 ការកំណត់ជារួម")

        self.tab_printer = QWidget()
        self.setup_printer_tab()
        self.tabs.addTab(self.tab_printer, "🖨️ ម៉ាស៊ីនបោះពុម្ព")

        self.tab_users = QWidget()
        self.setup_users_tab()
        self.tabs.addTab(self.tab_users, "👥 អ្នកប្រើប្រាស់")

        # In __init__, after Printer/Users tabs:
        self.tab_backup = QWidget()
        self.setup_backup_tab()
        self.tabs.addTab(self.tab_backup, "💾 បម្រុងទុក")

        

        layout.addWidget(self.tabs)

    def refresh(self):
        self.load_users()

    # ==================== BUSINESS TAB ====================
    def setup_business_tab(self):
        root_layout = QVBoxLayout(self.tab_business)
        root_layout.setContentsMargins(10, 10, 10, 10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        self.business_layout = QVBoxLayout(container)
        self.business_layout.setSpacing(20)
        self.business_layout.setContentsMargins(20, 20, 20, 20)

        scroll.setWidget(container)
        root_layout.addWidget(scroll)

        self.create_logo_card()
        self.create_general_card()
        # self.create_bank_qr_card()
        self.create_brands_card()
        self.create_receipt_footer_card()

        save_btn = QPushButton("💾 រក្សាទុកព័ត៌មានផ្ទាល់ខ្លួន")
        save_btn.setFixedHeight(45)
        save_btn.setStyleSheet(BTN_SAVE)
        save_btn.clicked.connect(self.save_business_info)
        self.business_layout.addWidget(save_btn)

        self.load_business_info()

    def load_business_info(self):
        s = self.app.settings.get_all()

        self.biz_logo.setText(s.get("business_logo", ""))
        self.biz_name.setText(s.get("business_name", ""))
        self.biz_phone.setText(s.get("business_phone", ""))
        self.biz_facebook.setText(s.get("business_facebook", ""))
        self.biz_telegram.setText(s.get("business_telegram", ""))
        # self.khqr_image.setText(s.get("khqr_image", ""))
        self.receipt_footer.setPlainText(s.get("receipt_footer", "សូមអរគុណ!"))

        self.refresh_logo_preview()
        self.load_brands()
        # self.refresh_khqr_preview()

    # ==================== BRANDS (Dynamic) ====================

    def create_brands_card(self):
        """Card that holds multiple brand forms"""
        self.brands_card = QGroupBox("🏷️ ម៉ាក / សាខា (Brands)")
        self.brands_card.setStyleSheet(self.group_style())

        self.brands_layout = QVBoxLayout(self.brands_card)
        self.brands_layout.setSpacing(12)

        # Container for all brand forms
        self.brands_container = QVBoxLayout()
        self.brands_container.setSpacing(10)
        self.brands_layout.addLayout(self.brands_container)

        # Add button
        add_btn = QPushButton("➕ បន្ថែមម៉ាកថ្មី")
        add_btn.setStyleSheet(BTN_SAVE)
        add_btn.clicked.connect(lambda checked=False: self.add_brand_form())
        self.brands_layout.addWidget(add_btn)

        self.business_layout.addWidget(self.brands_card)

        # Keep list of brand widgets for easy access
        self.brand_widgets = []


    def add_brand_form(self, data=None):
        """Create one brand form (can be empty or pre-filled)"""
        if not isinstance(data, dict):
            data = {}

        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #1F1F1F;
                border: 1px solid #444;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        form_layout = QFormLayout(frame)
        form_layout.setSpacing(8)
        form_layout.setContentsMargins(12, 12, 12, 12)

        name_edit = QLineEdit(data.get("name", ""))
        phone_edit = QLineEdit(data.get("phone", ""))
        telegram_edit = QLineEdit(data.get("telegram", ""))
        facebook_edit = QLineEdit(data.get("facebook", ""))
        address_edit = QTextEdit(data.get("address", ""))

        for w in (name_edit, phone_edit, telegram_edit, facebook_edit):
            w.setStyleSheet(INPUT_STYLE)

        form_layout.addRow("ឈ្មោះម៉ាក *:", name_edit)
        form_layout.addRow("លេខទូរស័ព្ទ:", phone_edit)
        form_layout.addRow("Telegram:", telegram_edit)
        form_layout.addRow("Facebook:", facebook_edit)
        form_layout.addRow("អាសយដ្ឋាន:", address_edit)

        # Remove button
        remove_btn = QPushButton("🗑️ លុបម៉ាកនេះ")
        remove_btn.setStyleSheet(BTN_CANCEL)
        remove_btn.clicked.connect(lambda: self.remove_brand_form(frame))
        form_layout.addRow(remove_btn)

        self.brands_container.addWidget(frame)

        # Store references
        self.brand_widgets.append({
            "frame": frame,
            "id": data.get("id"),          # ← keep the id
            "name": name_edit,
            "phone": phone_edit,
            "telegram": telegram_edit,
            "facebook": facebook_edit,
            "address": address_edit,
        })


    # def remove_brand_form(self, frame):
    #     """Remove a brand form"""
    #     for i, item in enumerate(self.brand_widgets):
    #         if item["frame"] is frame:
    #             self.brand_widgets.pop(i)
    #             break
    #     frame.setParent(None)
    #     frame.deleteLater()
    def remove_brand_form(self, frame):
        for i, item in enumerate(self.brand_widgets):
            if item["frame"] is frame:
                self.brand_widgets.pop(i)
                break
        frame.setParent(None)
        frame.deleteLater()


    def get_brands_data(self):
        brands = []
        for item in self.brand_widgets:
            name = item["name"].text().strip()
            if not name:
                continue
            brands.append({
                "id": item.get("id"),          # ← important
                "name": name,
                "phone": item["phone"].text().strip(),
                "telegram": item["telegram"].text().strip(),
                "facebook": item["facebook"].text().strip(),
                "address": item["address"].toPlainText().strip(),
            })
        return brands


    def load_brands(self):
        # Clear existing forms
        for item in self.brand_widgets[:]:
            self.remove_brand_form(item["frame"])
        self.brand_widgets.clear()

        try:
            brands = self.app.brand.get_brands() or []
        except Exception:
            brands = []
        
        if not brands:
            self.add_brand_form() 
        
        else:
            for b in brands:
                self.add_brand_form(b)
              


    def create_receipt_footer_card(self):
        card = QGroupBox("🧾 ការកំណត់វិក្កយបត្រ")
        card.setStyleSheet(self.group_style())

        layout = QVBoxLayout(card)
        layout.setSpacing(8)

        footer_label = QLabel("អត្ថបទបញ្ចប់វិក្កយបត្រ:")
        footer_label.setStyleSheet("color: #CCCCCC;")
        self.receipt_footer = QTextEdit()
        self.receipt_footer.setMaximumHeight(80)
        self.receipt_footer.setPlaceholderText("Thank you for your purchase!")
        self.receipt_footer.setStyleSheet(INPUT_STYLE)

        layout.addWidget(footer_label)
        layout.addWidget(self.receipt_footer)

        self.business_layout.addWidget(card)
    
    def refresh_logo_preview(self):

        path = self.biz_logo.text().strip()

        self.logo_preview.clear()

        if not path:

            self.logo_preview.setText("No Logo")
            return

        if not os.path.exists(path):

            self.logo_preview.setText("Logo\nNot Found")
            return

        pixmap = QPixmap(path)

        if pixmap.isNull():

            self.logo_preview.setText("Invalid Logo")
            return

        self.logo_preview.setPixmap(
            pixmap.scaled(
                120,
                120,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )
   
    def save_business_info(self):
        
        data = {
            "business_logo": self.biz_logo.text().strip(),
            "business_name": self.biz_name.text().strip(),
            "business_phone": self.biz_phone.text().strip(),
            "business_facebook": self.biz_facebook.text().strip(),
            "business_telegram": self.biz_telegram.text().strip(),
            "business_address": self.biz_address.text().strip(),
            "receipt_footer": self.receipt_footer.toPlainText().strip(),
            
        }
        
        self.app.settings.set_many(data)
        brands = self.get_brands_data()
        # if not brands:
        #     QMessageBox.warning(self, "Warning", "សូមបញ្ចូលម៉ាកយ៉ាងហោចណាស់មួយ")
        #     return
        self.app.brand.create_brands(brands)

        save_success_message(self, message="ការកំណត់ព័ត៌មានទូទៅជោគជ័យ")


    def create_logo_card(self):

        card = QGroupBox("🏪 រូបភាពហាង")
        card.setStyleSheet(self.group_style())

        layout = QVBoxLayout(card)

        self.logo_preview = QLabel()

        self.logo_preview.setFixedSize(140,140)
        self.logo_preview.setAlignment(Qt.AlignCenter)

        self.logo_preview.setStyleSheet("""
            border:2px dashed #666;
            border-radius:10px;
            color:#999;
            background:#1F1F1F;
        """)

        self.logo_preview.setText("No Logo")

        self.biz_logo = QLineEdit()
        self.biz_logo.setReadOnly(True)
        self.biz_logo.setStyleSheet(INPUT_STYLE)

        btn_layout = QHBoxLayout()

        upload_btn = QPushButton("📁 ដាក់បញ្ជូល រូបសម្គាល់")
        remove_btn = QPushButton("❌ លុប")

        upload_btn.setStyleSheet(BTN_SAVE)
        remove_btn.setStyleSheet(BTN_CANCEL)

        upload_btn.clicked.connect(self.select_logo)
        remove_btn.clicked.connect(self.remove_logo)

        btn_layout.addWidget(upload_btn)
        btn_layout.addWidget(remove_btn)

        layout.addWidget(self.logo_preview, alignment=Qt.AlignCenter)
        layout.addWidget(self.biz_logo)
        layout.addLayout(btn_layout)

        self.business_layout.addWidget(card)


    def create_general_card(self):
        card = QGroupBox("🏢 ព័ត៌មានទូទៅ")
        card.setStyleSheet(self.group_style())

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 16, 12, 12)
        card_layout.setSpacing(10)

        # Inner frame (same style as Brand form)
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #1F1F1F;
                border: 1px solid #444;
                border-radius: 8px;
            }
        """)

        form = QFormLayout(frame)
        form.setSpacing(10)
        form.setContentsMargins(14, 14, 14, 14)

        self.biz_name = QLineEdit()
        self.biz_phone = QLineEdit()
        self.biz_facebook = QLineEdit()
        self.biz_telegram = QLineEdit()
        self.biz_address = QLineEdit()

        for w in [self.biz_name, self.biz_phone, self.biz_facebook, self.biz_telegram, self.biz_address]:
            w.setStyleSheet(INPUT_STYLE)

        form.addRow("ឈ្មោះហាង:", self.biz_name)
        form.addRow("លេខទូរស័ព្ទ:", self.biz_phone)
        form.addRow("Facebook:", self.biz_facebook)
        form.addRow("Telegram:", self.biz_telegram)
        form.addRow("អាសយដ្ឋាន:", self.biz_address)

        card_layout.addWidget(frame)
        self.business_layout.addWidget(card)   # ← important: add the card, not the layout
    
    def group_style(self):

        return """
        QGroupBox{
            color:white;
            font-size:15px;
            font-weight:bold;
            border:1px solid #444;
            border-radius:10px;
            margin-top:10px;
            padding-top:12px;
            background:#2A2A2A;
        }

        QGroupBox::title{
            subcontrol-origin:margin;
            left:12px;
            padding:0 6px;
        }
        """


    def select_logo(self):

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select Business Logo",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp)"
        )

        if not filename:
            return

        self.biz_logo.setText(filename)

        self.refresh_logo_preview()

    def remove_logo(self):

        self.biz_logo.clear()

        self.refresh_logo_preview()
    # ==================== ORDER DEFAULTS TAB ====================
    def setup_defaults_tab(self):
        layout = QVBoxLayout(self.tab_defaults)
        layout.setContentsMargins(20, 20, 20, 20)

        card = QFrame()
        card.setStyleSheet("background-color: #2A2A2A; border-radius: 12px;")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)

        form = QFormLayout()
        form.setSpacing(12)

        self.default_delivery = QDoubleSpinBox()
        self.default_delivery.setRange(0, 1000000)
        self.default_delivery.setSuffix(" $")
        self.default_delivery.setStyleSheet(INPUT_STYLE)

        self.default_discount = QDoubleSpinBox()
        self.default_discount.setRange(0, 100)      # ← was (0, 1000000)
        self.default_discount.setSuffix(" %")       # ← was " $"
        self.default_discount.setStyleSheet(INPUT_STYLE)

        self.exchange_rate = QDoubleSpinBox()
        self.exchange_rate.setRange(0, 100000)
        self.exchange_rate.setDecimals(0)
        self.exchange_rate.setSuffix(" ៛ / $")
        self.exchange_rate.setSingleStep(50)
        self.exchange_rate.setStyleSheet(INPUT_STYLE)

        form.addRow("ស្តង់ដាថ្លៃដឹក:", self.default_delivery)
        form.addRow("ស្តង់ដា បញ្ចុះតម្លៃ​ (%):", self.default_discount)
        form.addRow("អត្រាប្ដូរប្រាក់ (KHR per USD):", self.exchange_rate)

        card_layout.addLayout(form)

        save_btn = QPushButton("💾 រក្សាទុក")
        save_btn.setStyleSheet(BTN_SAVE)
        save_btn.clicked.connect(self.save_defaults)
        card_layout.addWidget(save_btn)

        layout.addWidget(card)
        layout.addStretch()

        self.load_defaults()

    def load_defaults(self):
        s = self.app.settings.get_all()
        self.default_delivery.setValue(float(s.get("default_delivery", 0) or 0))
        self.default_discount.setValue(float(s.get("default_discount", 0) or 0))   # now a %
        self.exchange_rate.setValue(float(s.get("exchange_rate", 4100) or 4100))

    def save_defaults(self):
        self.app.settings.set_many({
            "default_delivery": self.default_delivery.value(),
            "default_discount": self.default_discount.value(),
            "exchange_rate": self.exchange_rate.value(),
        })
        save_success_message(self, message="ការកំណត់ព័ត៌មានជារួមជោគជ័យ", win_title="រក្សាទុក")
    
    def setup_printer_tab(self):
        layout = QVBoxLayout(self.tab_printer)
        layout.setContentsMargins(20, 20, 20, 20)

        card = QFrame()
        card.setStyleSheet("background-color: #2A2A2A; border-radius: 12px;")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)

        form = QFormLayout()
        form.setSpacing(12)

        self.printer_combo = QComboBox()
        self.printer_combo.setStyleSheet(INPUT_STYLE)
        self.refresh_printer_list()
        form.addRow("ម៉ាស៊ីនបោះពុម្ពវិក្កយបត្រ:", self.printer_combo)

        self.paper_size_combo = QComboBox()
        self.paper_size_combo.setStyleSheet(INPUT_STYLE)
        self.paper_size_combo.addItem("A5 (148 × 210mm)", "A5")
        self.paper_size_combo.addItem("A4 (210 × 297mm)", "A4")
        self.paper_size_combo.addItem("80mm Receipt Roll", "80MM")
        form.addRow("ទំហំក្រដាស:", self.paper_size_combo)

        card_layout.addLayout(form)

        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("🔄 ផ្ទុកឡើងវិញ")
        refresh_btn.setStyleSheet(self._button_style("#4B5563", "#6B7280"))
        refresh_btn.clicked.connect(self.refresh_printer_list)
        btn_layout.addWidget(refresh_btn)

        test_btn = QPushButton("🖨️ សាកល្បងបោះពុម្ព")
        test_btn.setStyleSheet(self._button_style("#3B82F6", "#2563EB"))
        test_btn.clicked.connect(self.test_print)
        btn_layout.addWidget(test_btn)

        card_layout.addLayout(btn_layout)

        save_btn = QPushButton("💾 រក្សាទុកការកំណត់")
        save_btn.setStyleSheet(self._button_style("#22C55E", "#16A34A"))
        save_btn.clicked.connect(self.save_printer_settings)
        card_layout.addWidget(save_btn)

        layout.addWidget(card)
        layout.addStretch()

        self.load_printer_settings()

    def refresh_printer_list(self):
        from PySide6.QtPrintSupport import QPrinterInfo
        current = self.printer_combo.currentData() if self.printer_combo.count() > 0 else None
        self.printer_combo.clear()
        self.printer_combo.addItem("System Default", "")
        for name in QPrinterInfo.availablePrinterNames():
            self.printer_combo.addItem(name, name)
        if current:
            index = self.printer_combo.findData(current)
            if index >= 0:
                self.printer_combo.setCurrentIndex(index)

    def load_printer_settings(self):
        s = self.app.settings.get_all()
        saved_printer = s.get("receipt_printer", "")
        index = self.printer_combo.findData(saved_printer)
        self.printer_combo.setCurrentIndex(index if index >= 0 else 0)

        saved_paper = s.get("receipt_paper_size", "A5")
        index2 = self.paper_size_combo.findData(saved_paper)
        self.paper_size_combo.setCurrentIndex(index2 if index2 >= 0 else 0)

    def save_printer_settings(self):
        self.app.settings.set_many({
            "receipt_printer": self.printer_combo.currentData(),
            "receipt_paper_size": self.paper_size_combo.currentData(),
        })
        save_success_message(self, message="ការកំណត់ម៉ាស៊ីនបោះពុម្ពត្រូវបានរក្សាទុក")

    def test_print(self):
        from PySide6.QtPrintSupport import QPrinter, QPrinterInfo
        from PySide6.QtGui import QTextDocument, QPageSize, QPageLayout, QFont
        from PySide6.QtCore import QSizeF, QMarginsF

        selected_printer = self.printer_combo.currentData()
        available = QPrinterInfo.availablePrinterNames()

        printer = QPrinter(QPrinter.HighResolution)
        if selected_printer and selected_printer in available:
            printer.setPrinterName(selected_printer)
        elif not printer.printerName():
            none_selected_warning(self, message="មិនមានម៉ាស៊ីនបោះពុម្ពសម្រាប់សាកល្បង")
            return

        doc = QTextDocument()
        doc.setDefaultFont(QFont(self.app.default_font_family, 11))
        doc.setHtml(f"""
            <div style="text-align:center; padding:20px;">
                <h2>✅ សាកល្បងបោះពុម្ពជោគជ័យ</h2>
                <p>ម៉ាស៊ីនបោះពុម្ព: {printer.printerName()}</p>
                <p>ប្រសិនបើអ្នកអានឃើញនេះ ម៉ាស៊ីនបោះពុម្ពរបស់អ្នកបានកំណត់ត្រឹមត្រូវហើយ។</p>
            </div>
        """)

        a5_size = QPageSize(QSizeF(148, 210), QPageSize.Millimeter, "A5 Custom")
        printer.setPageSize(a5_size)
        printer.setPageOrientation(QPageLayout.Portrait)
        printer.setPageMargins(QMarginsF(8, 8, 8, 8), QPageLayout.Millimeter)
        doc.setPageSize(printer.pageRect(QPrinter.Point).size())

        try:
            doc.print_(printer)
            save_success_message(self, message=f"ទំព័រសាកល្បងបានផ្ញើទៅ '{printer.printerName()}'")
        except Exception as e:
            QMessageBox.critical(self, "Print Failed", str(e))


    def _button_style(self, bg, hover):
        return f"""
            QPushButton {{
                background-color: {bg}; color: white; padding: 10px 20px;
                border: none; border-radius: 8px; font-size: 14px; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {hover}; }}
        """
    # ==================== USERS TAB ====================
    def setup_users_tab(self):
        layout = QVBoxLayout(self.tab_users)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        toolbar = QHBoxLayout()
        add_btn = QPushButton("➕ បន្ថែមអ្នកប្រើថ្មី")
        add_btn.setStyleSheet(BTN_SAVE)
        add_btn.clicked.connect(self.add_new_user)
        toolbar.addWidget(add_btn)
        toolbar.addStretch()

        self.users_table = QTableWidget()
        self.users_table.setColumnCount(7)
        self.users_table.setHorizontalHeaderLabels(
            ["ID", "ឈ្មោះប្រើប្រាស់", "ឈ្មោះអ្នកប្រើប្រាស់", "តួនាទី", "ម៉ាកយីហោ", "ស្ថានភាព", "សកម្មភាព"]
        )
        self.users_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.users_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.users_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.users_table.setAlternatingRowColors(True)
        self.users_table.doubleClicked.connect(self.edit_user)
        self.users_table.setStyleSheet(TABLE_STYLE)
        layout.addWidget(self.users_table)
        layout.addLayout(toolbar)

        hint = QLabel("💡 ចុចពីរដងលើអ្នកប្រើដើម្បីកែប្រែ")
        hint.setStyleSheet("color: #777; font-size: 12px;")
        layout.addWidget(hint)

        self.load_users()

    def load_users(self):
        try:
            users = self.app.users.get_all_users()
            self.users_table.setSortingEnabled(False)
            self.users_table.setRowCount(len(users))
            for row, u in enumerate(users):
                id_item = QTableWidgetItem(str(u['id']))
                id_item.setData(Qt.UserRole, u['id'])
                self.users_table.setItem(row, 0, id_item)
                self.users_table.setItem(row, 1, QTableWidgetItem(u['username'] or ""))
                self.users_table.setItem(row, 2, QTableWidgetItem(u['name'] or ""))
                self.users_table.setItem(row, 3, QTableWidgetItem(u['role'] or ""))
                self.users_table.setItem(row, 4, QTableWidgetItem(u['brand_name'] or "-"))

                is_active = bool(u['active'])
                status_item = QTableWidgetItem("សកម្ម" if is_active else "អសកម្ម")
                status_item.setForeground(Qt.GlobalColor.green if is_active else Qt.GlobalColor.red)
                self.users_table.setItem(row, 5, status_item)

                # --- Toggle button ---
                toggle_btn = QPushButton("បិទដំណើរការ" if is_active else "បើកដំណើរការ")
                toggle_btn.setStyleSheet(self._table_action_btn_style(is_active))
                toggle_btn.setFixedHeight(26)
                toggle_btn.clicked.connect(
                    lambda checked, uid=u['id'], active=is_active: self.toggle_user_status(uid, not active)
                )
                self.users_table.setCellWidget(row, 6, toggle_btn)

            self.users_table.setColumnHidden(0, True)
            self.users_table.setSortingEnabled(True)
        except Exception as e:
            print("Load users error:", e)
    def _table_action_btn_style(self, active):
        if active:
            return """
                QPushButton {
                    background-color: #EF4444; color: white;
                    padding: 4px 8px; border: none; border-radius: 4px;
                    font-size: 11px; font-weight: bold;
                    max-height: 24px;
                }
                QPushButton:hover { background-color: #DC2626; }
            """
        else:
            return """
                QPushButton {
                    background-color: #22C55E; color: black;
                    padding: 4px 8px; border: none; border-radius: 4px;
                    font-size: 11px; font-weight: bold;
                    max-height: 24px;
                }
                QPushButton:hover { background-color: #16A34A; }
            """
    def add_new_user(self):
        dialog = UserDialog(self, app=self.app)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if not data:
                return
            try:
                self.app.users.add_user(data)
                self.load_users()
                save_success_message(self, message="បន្ថែមអ្នកប្រើប្រាស់ថ្មីជោគជ័យ")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add user: {e}")

    def edit_user(self, index):
        row = index.row()
        user_id = self.users_table.item(row, 0).data(Qt.UserRole)
        data = {
            "name": self.users_table.item(row, 2).text(),
            "username": self.users_table.item(row, 1).text(),
            "role": self.users_table.item(row, 3).text(),
        }
        # Find brand_id matching the displayed brand_name — need real id, not just name text
        # Simplest: refetch the actual user row for accurate brand_id
        try:
            users = self.app.users.get_all_users()
            real_user = next((u for u in users if u['id'] == user_id), None)
            if real_user:
                data["brand_id"] = real_user['brand_id']
        except Exception:
            pass

        dialog = UserDialog(self, app=self.app, data=data)
        if dialog.exec() == QDialog.Accepted:
            new_data = dialog.get_data()
            if new_data:
                try:
                    self.app.users.update_user(user_id, new_data)
                    if new_data.get('password'):
                        self.app.users.update_user_password(user_id, new_data['password'])
                    self.load_users()
                    save_success_message(self, message="បានកែប្រែអ្នកប្រើប្រាស់ជោគជ័យ")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to update user: {e}")

    def toggle_user_status(self, user_id, new_active):
        # Prevent a user from disabling their own account
        current_user_id = self.app.user.get('id') if hasattr(self.app, 'user') else None
        if user_id == current_user_id and not new_active:
            none_selected_warning(self,message="អ្នកមិនអាចបិទដំណើរការគណនីខ្លួនឯងបានទេ",win_title="មិនអាចធ្វើបាន")
            return

        action_text = "បើកដំណើរការ" if new_active else "បិទដំណើរការ"
        if not confirm_delete(self, message=f"តើអ្នកចង់{action_text}អ្នកប្រើប្រាស់នេះមែនទេ?", confirm_text=action_text):
            return

        try:
            self.app.users.update_user_status(user_id, new_active)
            self.load_users()
            save_success_message(self, message=f"{action_text}អ្នកប្រើប្រាស់ជោគជ័យ")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update user: {e}")

    # ==================== SHARED STYLES ====================



    def setup_backup_tab(self):
        layout = QVBoxLayout(self.tab_backup)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # ==================== INFO CARD ====================
        info_card = QFrame()
        info_card.setStyleSheet("background-color: #2A2A2A; border-radius: 12px;")
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(20, 15, 20, 15)

        info_title = QLabel("💾 ការបម្រុងទុកទិន្នន័យ")
        info_title.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        info_layout.addWidget(info_title)

        info_text = QLabel(
            "ចម្លងទុកទិន្នន័យទាំងអស់ (ការកម្មង់, អតិថិជន, ផលិតផល, ស្តុក...) ទុកជាបម្រុង "
            "ដើម្បីការពារការបាត់បង់ទិន្នន័យ។"
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("color: #AAAAAA; font-size: 13px;")
        info_layout.addWidget(info_text)

        layout.addWidget(info_card)

        # ==================== ACTIONS CARD ====================
        action_card = QFrame()
        action_card.setStyleSheet("background-color: #2A2A2A; border-radius: 12px;")
        action_layout = QVBoxLayout(action_card)
        action_layout.setContentsMargins(20, 15, 20, 15)
        action_layout.setSpacing(10)

        self.auto_backup_checkbox = QCheckBox("បម្រុងទុកដោយស្វ័យប្រវត្តិ (ជារៀងរាល់ថ្ងៃ)")
        self.auto_backup_checkbox.setStyleSheet("color: white; font-size: 13px;")
        self.auto_backup_checkbox.stateChanged.connect(self.save_backup_settings)
        action_layout.addWidget(self.auto_backup_checkbox)

        btn_row = QHBoxLayout()
        backup_now_btn = QPushButton("💾 បម្រុងទុកឥឡូវនេះ")
        backup_now_btn.setStyleSheet(BTN_SAVE)
        backup_now_btn.clicked.connect(self.backup_now)
        btn_row.addWidget(backup_now_btn)

        open_folder_btn = QPushButton("📁 បើកថតឯកសារបម្រុងទុក")
        open_folder_btn.setStyleSheet(self._button_style("#4B5563", "#6B7280"))
        open_folder_btn.clicked.connect(self.open_backup_folder)
        btn_row.addWidget(open_folder_btn)

        action_layout.addLayout(btn_row)

        self.last_backup_label = QLabel("បម្រុងទុកចុងក្រោយ: មិនទាន់មាន")
        self.last_backup_label.setStyleSheet("color: #999; font-size: 12px;")
        action_layout.addWidget(self.last_backup_label)

        layout.addWidget(action_card)

        # ==================== BACKUP LIST ====================
        list_label = QLabel("ប្រវត្តិការបម្រុងទុក")
        list_label.setStyleSheet("font-size: 14px; font-weight: bold; color: white; margin-top: 10px;")
        layout.addWidget(list_label)

        self.backup_table = QTableWidget()
        self.backup_table.setColumnCount(3)
        self.backup_table.setHorizontalHeaderLabels(["ឈ្មោះឯកសារ", "ទំហំ", "កាលបរិច្ឆេទ"])
        self.backup_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.backup_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.backup_table.setStyleSheet(TABLE_STYLE)
        self.backup_table.doubleClicked.connect(self.on_backup_row_double_click)
        layout.addWidget(self.backup_table)

        hint = QLabel("💡 ចុចពីរដងលើឯកសារបម្រុងទុកដើម្បីស្តារទិន្នន័យត្រឡប់ (Restore)")
        hint.setStyleSheet("color: #777; font-size: 12px;")
        layout.addWidget(hint)

        self.load_backup_settings()
        self.load_backup_list()

    def get_backup_folder(self):
        # self.app.db.db_path is a Path object, e.g. Path("database/pos.db")
        db_dir = self.app.db.db_path.parent
        return str(db_dir / "backups")

    def load_backup_settings(self):
        s = self.app.settings.get_all()
        self.auto_backup_checkbox.setChecked(s.get("auto_backup_enabled", "0") == "1")
        last_backup = s.get("last_backup_at", "")
        if last_backup:
            self.last_backup_label.setText(f"បម្រុងទុកចុងក្រោយ: {last_backup}")

    def save_backup_settings(self):
        self.app.settings.set_many({
            "auto_backup_enabled": "1" if self.auto_backup_checkbox.isChecked() else "0",
        })

    def backup_now(self):
        
        import datetime as dt

        try:
            db_path = str(self.app.db.db_path)   # convert Path → str for consistency
            backup_folder = self.get_backup_folder()
            backup_path = backup_database(db_path, backup_folder, keep_last=10)

            now_str = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.app.settings.set("last_backup_at", now_str)
            self.last_backup_label.setText(f"បម្រុងទុកចុងក្រោយ: {now_str}")

            self.load_backup_list()
            save_success_message(self, message="បម្រុងទុកទិន្នន័យជោគជ័យ!")
        except Exception as e:
            QMessageBox.critical(self, "Backup Error", f"បរាជ័យក្នុងការបម្រុងទុក:\n{e}")

    def open_backup_folder(self):
        import subprocess
        backup_folder = self.get_backup_folder()
        os.makedirs(backup_folder, exist_ok=True)
        try:
            os.startfile(backup_folder)   # Windows
        except AttributeError:
            subprocess.Popen(["xdg-open", backup_folder])   # Linux fallback

    def load_backup_list(self):
        from utils.backup import get_backup_list
        try:
            backups = get_backup_list(self.get_backup_folder())
            self.backup_table.setRowCount(len(backups))
            for row, b in enumerate(backups):
                id_item = QTableWidgetItem(b['filename'])
                id_item.setData(Qt.UserRole, b['path'])
                self.backup_table.setItem(row, 0, id_item)
                self.backup_table.setItem(row, 1, QTableWidgetItem(f"{b['size_mb']:.2f} MB"))
                self.backup_table.setItem(row, 2, QTableWidgetItem(b['modified'].strftime("%Y-%m-%d %H:%M:%S")))
        except Exception as e:
            print("Load backup list error:", e)

    def on_backup_row_double_click(self, index):
        row = index.row()
        backup_path = self.backup_table.item(row, 0).data(Qt.UserRole)
        filename = self.backup_table.item(row, 0).text()

        if not confirm_delete(
            self,
            message=f"តើអ្នកចង់ស្តារទិន្នន័យពី '{filename}' មែនទេ?\n\n"
                    f"⚠️ ព័ត៌មានបច្ចុប្បន្នទាំងអស់នឹងត្រូវបានជំនួស!\n"
                    f"(ប៉ុន្តែនឹងរក្សាទុកច្បាប់ចម្លងបច្ចុប្បន្នជាមុនសិន)",
            confirm_text="ស្តារឡើងវិញ"
        ):
            return

        try:
            from utils.backup import restore_database
            db_path = str(self.app.db.db_path)
            restore_database(backup_path, db_path)

            QMessageBox.information(
                self, "ស្តារជោគជ័យ",
                "ទិន្នន័យត្រូវបានស្តារឡើងវិញ។\nសូមបិទ ហើយបើកកម្មវិធីឡើងវិញ ដើម្បីឲ្យការផ្លាស់ប្តូរដំណើរការ។"
            )
        except Exception as e:
            QMessageBox.critical(self, "Restore Error", f"បរាជ័យក្នុងការស្តារ:\n{e}")
    
    


    