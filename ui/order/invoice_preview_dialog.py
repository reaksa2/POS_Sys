from PySide6.QtWidgets import (QVBoxLayout,
     QHBoxLayout, QLabel, QPushButton,QDialog,QTextBrowser
)


class InvoicePreviewDialog(QDialog):
    def __init__(self, parent, html):
        super().__init__(parent)
        self.setWindowTitle("បញ្ជាក់ & ព្រីនវិក្កយបត្រ")
        self.resize(420, 600)
        self.setStyleSheet("background-color: #2A2A2A; color: white;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        title = QLabel("🧾 វិក្កយបត្រ")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        self.browser = QTextBrowser()
        self.browser.setStyleSheet("background-color: white; border-radius: 8px;")
        self.browser.setHtml(html)
        layout.addWidget(self.browser, stretch=1)

        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("❌ បោះបង់")
        cancel_btn.setStyleSheet("background-color: #6B7280; color: white; padding: 10px 20px; border-radius: 8px;")
        cancel_btn.clicked.connect(self.reject)

        confirm_btn = QPushButton("✅ បញ្ជាក់ & ព្រីន")
        confirm_btn.setStyleSheet("background-color: #22C55E; color: black; padding: 10px 20px; border-radius: 8px; font-weight: bold;")
        confirm_btn.clicked.connect(self.accept)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(confirm_btn)
        layout.addLayout(btn_layout)