# utils/styles.py

TABLE_STYLE = """
    QTableWidget {
        background-color: #1F1F1F;
        gridline-color: #3A3A3A;
        border: 1px solid #444;
        border-radius: 8px;
        color: white;
        font-family: "Khmer OS Siemreap";
        font-size: 12px;
    }
    QTableWidget::item:alternate { background-color: #232323; }
    QTableWidget::item:selected { background-color: #555; }
    QTableWidget::item:hover { background-color: #555; }
    QHeaderView::section {
        background-color: #2A2A2A; color: white;
        border: 1px solid #444; padding: 8px;
        font-family: "Khmer OS Siemreap";
        font-size: 12px;
        font-weight: bold;
    }
"""

# New: a compact/lighter variant, e.g. for smaller order-detail tables
TABLE_STYLE_COMPACT = """
    QTableWidget {
        background-color: #262626;
        gridline-color: #3A3A3A;
        border: none;
        border-radius: 6px;
        color: white;
    }
    QTableWidget::item { padding: 4px; }
    QTableWidget::item:alternate { background-color: #2E2E2E; }
    QTableWidget::item:selected { background-color: #3B82F6; }
    QHeaderView::section {
        background-color: #1F1F1F; color: #AAA;
        border: none; padding: 6px; font-weight: bold; font-size: 12px;
    }
"""
# New: a compact/lighter variant, e.g. for smaller order-detail tables
BTN_SEARCH_STYLE = """
    QLineEdit {
        background-color: #1F1F1F; color: white; padding: 10px 12px;
        border-radius: 8px; border: 1px solid #444; font-size: 14px;
    }
    QLineEdit:focus { border: 1px solid #8B5A2B; }
"""


def button_style(bg, hover, text_color="white"):
    return f"""
        QPushButton {{
            background-color: {bg};
            color: {text_color};
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: bold;
        }}
        QPushButton:hover {{ background-color: {hover}; }}
        QPushButton:pressed {{ background-color: {hover}; }}
    """

# ==================== PRESET BUTTON STYLES ====================

BTN_ADD = button_style("#22C55E", "#16A34A")            # green — add/create actions
BTN_SAVE = button_style("#3B82F6", "#2563EB")            # blue — save/update actions
BTN_CANCEL = button_style("#EF4444", "#DC2626")          # red — cancel/delete/destructive
BTN_NEUTRAL = button_style("#4B5563", "#6B7280")         # gray — clear/close/neutral
BTN_PRINT = button_style("#6B7280", "#4B5563")           # muted gray — print/secondary
BTN_EDIT = button_style("#3B82F6", "#2563EB")            # blue — edit actions
BTN_COMPLETE = button_style("#22C55E", "#16A34A", text_color="black")  # green w/ black text — completion actions



TAB_STYLE = """
    QTabWidget::pane {
        border: 1px solid #444;
        background-color: #1F1F1F;
        border-bottom: none;
        border-left: none;
        border-right: none;
    }
    QTabBar::tab {
        padding: 5px 10px;
        font-size: 12px;
        background-color: #2A2A2A;
        border: 1px solid #444;
        border-bottom: none;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        margin-right: 4px;
    }
    QTabBar::tab:selected {
        background-color: #8B5A2B;
        color: white;
        font-weight: bold;
        border: 1px solid #D4A373;
    }
    QTabBar::tab:hover:!selected {
        background-color: #3A3A3A;
    }
"""


PAGE_TITLE_STYLE = "font-size: 18px; font-weight: bold; color: #E5E7EB; border-bottom:transparent;"

PAGE_HEADER_STYLE = """
    QFrame {
                    background-color: #8B5A2B;
                    border-bottom: 1px solid #3A3A3A;
                    border-radius: 8px;
                }
    """


SIDEBAR_STYLE = """
            QFrame { background-color: #8B5A2B; color: white; }
            QPushButton { text-align: left; padding: 16px 20px; font-size: 16px; border: none; border-radius: 8px; }
            QPushButton:hover { background-color: #A67B5B; }
            QPushButton:pressed, QPushButton:checked { background-color: #D4A373; }
        """


INPUT_STYLE = """
    QLineEdit, QComboBox, QTextEdit, QSpinBox, QDoubleSpinBox, QDateEdit,QDateTimeEdit {
        background-color: #1F1F1F;
        color: white;
        padding: 8px 10px;
        border: 1px solid #444;
        border-radius: 8px;
        font-size: 14px;
    }
    QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus,QDateEdit:focus, QDateTimeEdit:focus {
        border: 1px solid #8B5A2B;
    }
"""

SIDEBAR_TITLE_STYLE = """
    color: #ffdd88;
    font-size: 16px;
    font-weight: bold;
    padding: 4px 8px 16px 8px;
"""


# utils/style.py

def get_tooltip_style(font_family):
    return f"""
        QToolTip {{
            background-color: #2A2A2A;
            color: white;
            border: 1px solid #444;
            padding: 6px 10px;
            font-family: "{font_family}";
            font-size: 13px;
        }}
    """

def get_app_global_style(font_family):
    return f"""
        QWidget {{
            background-color: #1F1F1F;
            color: white;
            font-family: "{font_family}";
        }}
        {get_tooltip_style(font_family)}
    """