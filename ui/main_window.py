from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QStackedWidget, QPushButton, QFrame, QStatusBar, QMenu, QMessageBox,QScrollArea
)
from PySide6.QtGui import QFont, QAction,QPixmap
from PySide6.QtCore import Qt
from ui.dashboard.dashboard import DashboardWidget
from ui.customer.customer_widget import CustomerWidget
from ui.product.product_widget import ProductWidget
from ui.settings.settings_widget import SettingsWidget
from ui.order.order_widget import OrderWidget
from ui.report.report_widget import ReportWidget
from ui.stock.stock_widget import StockWidget
from utils.style import PAGE_TITLE_STYLE, PAGE_HEADER_STYLE, SIDEBAR_STYLE,BTN_SAVE
from utils.utils import resource_path
from utils.dialog import save_success_message,none_selected_warning,confirm_delete


class MainWindow(QMainWindow):
    def __init__(self, app, user):
        super().__init__()
        self.app = app
        self.user = user
        self.pages = {}
        self.page_widgets = {}
        self.stack = None
        self.menu_buttons = {}

        self.setWindowTitle(f"{self.app.settings.get("business_name","POS")} - {user.get('name', 'Admin')}")
        self.showMaximized()

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ==================== SIDEBAR ====================
        sidebar = QFrame()
        sidebar.setFixedWidth(230)
        sidebar.setStyleSheet(SIDEBAR_STYLE)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setSpacing(6)
        sidebar_layout.setContentsMargins(15, 30, 15, 20)

        sidebar_header = QLabel(self.app.settings.get("business_name","POS"))
        sidebar_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_header.setWordWrap(True)
        sidebar_header.setStyleSheet(f"{PAGE_TITLE_STYLE} margin-bottom:20px")
        sidebar_layout.addWidget(sidebar_header)

        # ==================== MENU ITEMS (role-based) ====================
        self.menu_items = self.get_menu_items_for_role(user.get('role', 'Cashier'))

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("padding: 0px; margin: 0px; border: none;")

        for name, icon in self.menu_items:
            btn = QPushButton(f"{icon}  {name}")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, n=name: self.load_page(n))
            sidebar_layout.addWidget(btn)
            self.menu_buttons[name] = btn

        sidebar_layout.addStretch()

        about_btn = QPushButton("ℹ️ អំពីប្រព័ន្ធ")
        about_btn.setCheckable(True)
        about_btn.clicked.connect(lambda: self.load_page("អំពីប្រព័ន្ធ"))
        about_btn.setStyleSheet("padding: 16px 20px; font-size: 16px;")
        sidebar_layout.addWidget(about_btn)
        self.menu_buttons["About"] = about_btn

        main_layout.addWidget(sidebar)

        # ==================== RIGHT SIDE: HEADER + STACK ====================
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setSpacing(10)

       # Shared top header for every page
        header_frame = QFrame()
        header_frame.setStyleSheet(PAGE_HEADER_STYLE)
        top_header = QHBoxLayout(header_frame)

        self.page_title_label = QLabel("📊 ទំព័រដើម")
        self.page_title_label.setFont(QFont(self.app.default_font_family, 16, QFont.Weight.Bold))
        self.page_title_label.setStyleSheet(PAGE_TITLE_STYLE)
        self.page_title_label.setMaximumHeight(40)
        top_header.addWidget(self.page_title_label)
        top_header.addStretch()

        profile_btn = QPushButton(f"👤 {self.app.user.get('name', 'Admin')}  ▾")
        profile_btn.setFont(QFont(self.app.default_font_family, 12))
        profile_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #2A2A2A; color: white;
                padding: 8px 16px; border-radius: 8px;
                border: 1px solid #444; font-size: 14px;
                font-family: "{self.app.default_font_family}";
            }}
            QPushButton:hover {{ background-color: #3A3A3A; }}
        """)
        profile_menu = QMenu(profile_btn)
        profile_menu.setFont(QFont(self.app.default_font_family, 12))
        profile_menu.setStyleSheet(f"""
            QMenu {{
                background-color: #2A2A2A; color: white; border: 1px solid #444;
                font-family: "{self.app.default_font_family}";
            }}
            QMenu::item {{ padding: 8px 20px; }}
            QMenu::item:selected {{ background-color: #8B5A2B; }}
        """)    
        role_action = QAction(f"តួនាទី: {self.app.user.get('role', '')}", profile_menu)
        role_action.setEnabled(False)
        profile_menu.addAction(role_action)
        profile_menu.addSeparator()
        logout_action = QAction("🚪 ចាកចេញ", profile_menu)
        logout_action.triggered.connect(self.logout)
        profile_menu.addAction(logout_action)
        profile_btn.setMenu(profile_menu)
        top_header.addWidget(profile_btn)

        right_layout.addWidget(header_frame)   # ← changed from addLayout(top_header)
        right_layout.addWidget(self.stack, stretch=1)

        main_layout.addWidget(right_container, stretch=1)

        self.setStatusBar(QStatusBar())

        default_page = "ការកម្មង់" if user.get('role') == "Cashier" else "ទំព័រដើម"
        self.load_page(default_page)
        self.stack.currentChanged.connect(self.on_page_changed)

    def logout(self):
        if not confirm_delete(self,message="តើអ្នកចង់ចាកចេញមែនទេ?",confirm_text="យលព្រម",win_title="ចាកចេញពីប្រព័ន្ធ"):
            return
        try:
            self.close()
            if hasattr(self.app, 'show_login'):
                self.app.show_login()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete customer: {e}")
            

    def on_page_changed(self, index):
        widget = self.stack.widget(index)
        if widget and hasattr(widget, 'refresh'):
            widget.refresh()

    def create_page(self, name: str) -> QWidget:
        if name == "ទំព័រដើម" or name == "Dashboard":
            return DashboardWidget(self.app)
        elif name == "ការកម្មង់" or name == "Orders":
            return OrderWidget(self.app)
        elif name == "ព័ត៌មានអតិថិជន" or name == "Customers":
            return CustomerWidget(self.app)
        elif name == "ទំនិញ" or name == "Products":
            return ProductWidget(self.app)
        elif name == "គ្រប់គ្រងទំនិញ" or name == "Stock":
            return StockWidget(self.app)
        elif name == "របាយការណ៍" or name == "Reports":
            return ReportWidget(self.app)
        elif name == "ការកំណត់" or name == "Settings":
            return SettingsWidget(self.app)
        elif name == "អំពីប្រព័ន្ធ" or name == "About":
            return self.about_info()
        else:
            w = QWidget()
            layout = QVBoxLayout(w)
            label = QLabel(f"<h1>{name} Module</h1><p>Coming soon...</p>")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
            return w

    def load_page(self, name: str):
        if name not in self.pages:
            page_widget = self.create_page(name)
            self.pages[name] = page_widget
            self.stack.addWidget(page_widget)

        index = self.stack.indexOf(self.pages[name])
        self.stack.setCurrentIndex(index)

        for btn_name, btn in self.menu_buttons.items():
            btn.setChecked(btn_name == name)

        # Update header title with icon + page name
        icon = self.get_icon_for_page(name)
        self.page_title_label.setText(f"{icon} {name}")

        self.statusBar().showMessage(f"Opened {name} module", 1500)

    def get_menu_items_for_role(self, role):
        all_items = [
            ("ទំព័រដើម", "📊"),
            ("ការកម្មង់", "📋"),
            ("ព័ត៌មានអតិថិជន", "👥"),
            ("ទំនិញ", "📦"),
            ("គ្រប់គ្រងទំនិញ", "📥"),
            ("របាយការណ៍", "📈"),
            ("ការកំណត់", "⚙️"),
        ]
        if role == "Cashier":
            allowed = {"ទំព័រដើម", "ការកម្មង់","ព័ត៌មានអតិថិជន", "របាយការណ៍"}
            return [item for item in all_items if item[0] in allowed]
        return all_items

    def get_icon_for_page(self, name):
        for item_name, icon in self.menu_items:
            if item_name == name:
                return icon
        if name in ("អំពីប្រព័ន្ធ", "About"):
            return "ℹ️"
        return ""


    def about_info(self):
        w = QWidget()
        outer_layout = QVBoxLayout(w)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(12)
        layout.setContentsMargins(30, 25, 30, 25)

        # Logo
        logo_label = QLabel()
        logo_path = resource_path("logo.png")
        pixmap = QPixmap(str(logo_path))
        if not pixmap.isNull():
            scaled = pixmap.scaled(90, 90, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(scaled)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)

        title = QLabel("សុខា ជ្រូកកណ្ដុរ អាំងពិសេស")
        title.setFont(QFont(self.app.default_font_family, 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffdd88;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("POS — Point of Sale System")
        subtitle.setStyleSheet("font-size: 15px; color: #999;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        version = QLabel("Version 1.5.2")
        version.setStyleSheet("font-size: 13px; color: #666;")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)

        check_update_btn = QPushButton("🔄 ពិនិត្យរកកំណែថ្មី")
        check_update_btn.setStyleSheet(BTN_SAVE)
        check_update_btn.clicked.connect(lambda: self.app.check_for_updates(silent=False))
        layout.addWidget(check_update_btn)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("background-color: #444; max-height: 1px;")
        layout.addWidget(divider)

        # ==================== WHAT'S NEW ====================
        whats_new_title = QLabel("✨ លក្ខណៈពិសេសថ្មី — v1.5.2")
        whats_new_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #22C55E; margin-top: 6px;")
        layout.addWidget(whats_new_title)

        whats_new_items = [
            "គ្រប់គ្រងស្តុកទំនិញ (Stock In / Out / ផ្ទេររវាងសាខា) ដោយឡែកតាមម៉ាកយីហោ",
            "ត្រងទំនិញតាមប្រភេទ និងស្វែងរកឈ្មោះក្នុងប្រអប់ជ្រើសរើសបានលឿន",
            "ការការពារលក់លើសស្តុក (ការកម្មង់, កែសម្រួលបរិមាណ, បញ្ជាទិញ)",
            "ព្រមានពេលស្តុកជិតអស់ ក្នុងអេក្រង់កម្មង់",
            "គ្រប់គ្រងម៉ាកយីហោ/សាខាច្រើន (Brands) ភ្ជាប់ជាមួយអ្នកប្រើប្រាស់និមួយៗ",
            "តាមដានប្រវត្តិចូល/ចេញស្តុក ដោយបញ្ជាក់អ្នកប្រើប្រាស់ដែលធ្វើប្រតិបត្តិការ",
            "តាមដានចំណេញ-ខាត (ថ្លៃដើម vs ចំណូល) និងអត្រាចំណេញ",
            "រាយការណ៍ដែលអាចត្រងតាមម៉ាកយីហោ (ប្រចាំថ្ងៃ/ខែ/ចំណេញ)",
            "គណនីអ្នកប្រើប្រាស់អាចបិទ/បើកដំណើរការ (ជំនួសការលុប)",
        ]
        for item in whats_new_items:
            item_label = QLabel(f"　✓ {item}")
            item_label.setStyleSheet("font-size: 13px; color: #86EFAC; padding-left: 10px;")
            item_label.setWordWrap(True)
            layout.addWidget(item_label)

        divider2 = QFrame()
        divider2.setFrameShape(QFrame.HLine)
        divider2.setStyleSheet("background-color: #444; max-height: 1px; margin-top: 8px;")
        layout.addWidget(divider2)

        features_title = QLabel("🚀 លក្ខណៈពិសេស")
        features_title.setStyleSheet("font-size: 18px; font-weight: bold; color: white; margin-top: 10px;")
        layout.addWidget(features_title)

        feature_groups = [
            ("📊 ទំព័រដើម", [
                "ចំណូលថ្ងៃនេះ, ចំណូលខែនេះ, ការកម្មង់រងចាំ",
                "ក្រាហ្វិចលក់ 7 ថ្ងៃចុងក្រោយ",
                "សភាពការកម្មង់ (Completed / Pending / Cancelled)",
            ]),
            ("📋 ការកម្មង់", [
                "ជ្រើសរើសទំនិញ និងរសជាតិដោយស្វែងរក ឬបន្ថែមថ្មី",
                "ត្រងទំនិញតាមប្រភេទ, បង្ហាញលេចធ្លោសម្រាប់ទំនិញស្តុកតិច",
                "កែសម្រួលចំនួន និងតម្លៃដោយផ្ទាល់ក្នុងតារាង (ការពារលើសស្តុក)",
                "ថ្លៃដឹក, បញ្ចុះតម្លៃ (%), វិធីបង់ប្រាក់, ស្ថានភាពបង់ប្រាក់",
                "កំណត់ម៉ោងទទួល (Pickup Time)",
                "រក្សាទុកជាបណ្ដោះអាសន្ន (Pending) ឬបញ្ជាទិញភ្លាមៗ",
                "មើលវិក្កយបត្រជាមុនមុននឹងបញ្ជាក់",
                "កែប្រែការកម្មង់ដែលនៅរងចាំ",
                "តារាងកម្មង់រងចាំ និងប្រវត្តិកម្មង់ (ត្រង់តាមកាលបរិច្ឆេទ)",
            ]),
            ("🖨️ វិក្កយបត្រ & ការបោះពុម្ព", [
                "បង្កើតវិក្កយបត្រដោយស្វ័យប្រវត្តិ (A5 / A4 / 80mm)",
                "ភ្ជាប់ឡូហ្គោ, QR កូដសម្រាប់បង់ប្រាក់, ព័ត៌មានម៉ាកយីហោទាំងអស់",
                "បោះពុម្ពស្វ័យប្រវត្តិបន្ទាប់ពីបញ្ជាទិញ ឬបោះពុម្ពឡើងវិញពីប្រវត្តិកម្មង់",
            ]),
            ("👥 អតិថិជន", [
                "គ្រប់គ្រងព័ត៌មានអតិថិជន (ទូរស័ព្ទ, អាសយដ្ឋាន, Facebook, Telegram)",
                "បន្ថែមអតិថិជនថ្មីភ្លាមៗពីអេក្រង់កម្មង់",
            ]),
            ("📦 ផលិតផល", [
                "គ្រប់គ្រងទំនិញ, ប្រភេទ, ឯកតា, រសជាតិ",
                "កំណត់ថ្លៃដើម សម្រាប់គណនាចំណេញ",
                "ស្វែងរក និងត្រងទំនិញ",
            ]),
            ("📥 ស្តុកទំនិញ", [
                "ស្តុកចូល / ស្តុកចេញ / ផ្ទេររវាងសាខា",
                "ត្រងតាមប្រភេទ, ស្វែងរកឈ្មោះទំនិញលឿន",
                "ការពារកម្មង់លើសចំនួនស្តុកមាន",
                "ប្រវត្តិចូល/ចេញលម្អិត ព្រមទាំងអ្នកប្រើប្រាស់ដែលបានធ្វើ",
            ]),
            ("📈 រាយការណ៍", [
                "រាយការណ៍ចំណូលប្រចាំថ្ងៃ/ខែ ត្រងតាមម៉ាកយីហោ",
                "ផលិតផលលក់ដាច់បំផុត",
                "ចំណេញ-ខាត (ថ្លៃដើម, ចំណូល, អត្រាចំណេញ) ប្រៀបធៀបតាមម៉ាកយីហោ",
            ]),
            ("⚙️ ការកំណត់", [
                "ព័ត៌មានអំពីអាជីវកម្ម (ឈ្មោះ, ទូរស័ព្ទ, Facebook, Telegram, ឡូហ្គោ)",
                "គ្រប់គ្រងម៉ាកយីហោ/សាខាច្រើន",
                "តម្លៃលំនាំដើម (ថ្លៃដឹក, បញ្ចុះតម្លៃ, អត្រាប្តូរប្រាក់)",
                "ការកំណត់ម៉ាស៊ីនបោះពុម្ព (ជ្រើសរើសម៉ាស៊ីន, ទំហំក្រដាស, សាកល្បងបោះពុម្ព)",
                "គ្រប់គ្រងអ្នកប្រើប្រាស់ភ្ជាប់ជាមួយម៉ាកយីហោ, សិទ្ធិចូលប្រើ (Admin / Manager / Cashier)",
                "បិទ/បើកដំណើរការគណនីអ្នកប្រើប្រាស់",
            ]),
            ("🔐 សុវត្ថិភាព", [
                "ចូលប្រើតាមឈ្មោះ និងពាក្យសម្ងាត់",
                "សិទ្ធិមើលទំព័រខុសគ្នាតាមតួនាទី",
                "ចងចាំឈ្មោះអ្នកប្រើពេលចូលលើកក្រោយ",
                "អ្នកប្រើប្រាស់មិនអាចបិទដំណើរការគណនីខ្លួនឯង",
            ]),
        ]

        for group_title, items in feature_groups:
            group_label = QLabel(group_title)
            group_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #FCD34D; margin-top: 8px;")
            layout.addWidget(group_label)
            for item in items:
                item_label = QLabel(f"　• {item}")
                item_label.setStyleSheet("font-size: 13px; color: #DDDDDD; padding-left: 10px;")
                item_label.setWordWrap(True)
                layout.addWidget(item_label)

        footer_divider = QFrame()
        footer_divider.setFrameShape(QFrame.HLine)
        footer_divider.setStyleSheet("background-color: #444; max-height: 1px; margin-top: 15px;")
        layout.addWidget(footer_divider)

        footer = QLabel("Developed for Restaurant Management © 2026")
        footer.setStyleSheet("font-size: 12px; color: #666; margin-top: 10px;")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)

        scroll.setWidget(container)
        outer_layout.addWidget(scroll)
        return w