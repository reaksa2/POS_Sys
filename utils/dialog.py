from PySide6.QtWidgets import QMessageBox
from PySide6.QtGui import QFont
from PySide6.QtCore import QTimer

def get_app_font_family(parent):
    try:
        if hasattr (parent,'app') and hasattr(parent.app,'default_font_family'):
            return parent.app.default_font_family
        if hasattr(parent,'default_font_family'):
            return parent.default_font_family

    except:
        pass
    return "Khmer OS Siemreap"

def confirm_delete(parent, message, confirm_text="លុប", cancel_text="បោះបង់",win_title="បញ្ជាក់ការលុបចេញ"):
    font_family = get_app_font_family(parent)
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(win_title)
    msg_box.setText(message)
    msg_box.setIcon(QMessageBox.Icon.Question)
    
    ok_btn = msg_box.addButton(confirm_text, QMessageBox.ButtonRole.YesRole)
    cancel_btn = msg_box.addButton(cancel_text, QMessageBox.ButtonRole.NoRole)
    msg_box.setDefaultButton(cancel_btn)

    msg_box.setStyleSheet(f"""
        QMessageBox {{ background-color: #2A2A2A; font-family:"{font_family}" }}
        QLabel {{ color: white; font-size: 14px; font-family:"{font_family}" }}
        QPushButton {{
            background-color: #4B5563; color: white;
            padding: 8px 20px; border-radius: 6px; font-weight: bold; min-width: 80px;
        }}
        QPushButton:hover {{ background-color: #6B7280; }}
    """)
    ok_btn.setStyleSheet(f"""
        QPushButton {{
            background-color: #EF4444; color: white;
            padding: 8px 20px; border-radius: 6px; font-weight: bold; min-width: 80px;
            font-family:"{font_family}"
        }}
        QPushButton:hover {{ background-color: #DC2626; }}
    """)

    msg_box.exec()
    return msg_box.clickedButton() == ok_btn


def none_selected_warning(parent, message,win_title = "គ្នានការជ្រើសរើស",auto_close_ms=2500):
    font_family = get_app_font_family(parent)
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(win_title)
    msg_box.setText(message)
    msg_box.setIcon(QMessageBox.Icon.Warning)
    
    ok_btn = msg_box.addButton("បាទ/ចាស", QMessageBox.ButtonRole.AcceptRole)
    msg_box.setDefaultButton(ok_btn)

    msg_box.setStyleSheet(f"""
        QMessageBox {{ background-color: #2A2A2A;font-family:"{font_family}"; }}
        QLabel {{ color: white; font-size: 14px;font-family:"{font_family}"; }}
        QPushButton {{
            background-color: #4B5563; color: white;
            padding: 8px 20px; border-radius: 6px; font-weight: bold; min-width: 80px;
            font-family:"{font_family}";
        }}
        QPushButton:hover {{ background-color: #6B7280; }}
    """)
    ok_btn.setStyleSheet(f"""
        QPushButton {{
            background-color: #EF4444; color: white;
            padding: 8px 20px; border-radius: 6px; font-weight: bold; min-width: 80px;
            font-family:"{font_family}";
        }}
        QPushButton:hover {{ background-color: #DC2626; }}
    """)
    if auto_close_ms:
        QTimer.singleShot(auto_close_ms, msg_box.close)
    msg_box.exec()


def save_success_message(parent, message,win_title = "ជោគជ័យ",auto_close_ms=1500):
    font_family = get_app_font_family(parent)
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(win_title)
    msg_box.setText(message)
    msg_box.setIcon(QMessageBox.Icon.Information)
    
    ok_btn = msg_box.addButton("បាទ/ចាស", QMessageBox.ButtonRole.AcceptRole)
    msg_box.setDefaultButton(ok_btn)

    msg_box.setStyleSheet(f"""
        QMessageBox {{ background-color: #2A2A2A;font-family:"{font_family}"; }}
        QLabel {{ color: white; font-size: 14px;font-family:"{font_family}"; }}
        QPushButton {{
            background-color: #4B5563; color: white;
            padding: 8px 20px; border-radius: 6px; font-weight: bold; min-width: 80px;
            font-family:"{font_family}";
        }}
        QPushButton:hover {{ background-color: #6B7280; }}
    """)
    ok_btn.setStyleSheet(f"""
        QPushButton {{
            background-color: #22C55E; color: white;font-family:"{font_family}";
            padding: 8px 20px; border-radius: 6px; font-weight: bold; min-width: 80px;
        }}
        QPushButton:hover {{ background-color: #16A34A; }}
    """)
    if auto_close_ms:
        QTimer.singleShot(auto_close_ms, msg_box.close)
    msg_box.exec()