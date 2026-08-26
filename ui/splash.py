from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QPixmap
from utils.utils import resource_path


class SplashScreen(QWidget):
    finished = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(480, 580)
        self.setStyleSheet("""
            QWidget {
                background-color: #8B5A2B;
                color: white;
                border-radius: 16px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # ==================== LOGO ====================
        logo_label = QLabel()
        logo_path = resource_path("logo.png")
        pixmap = QPixmap(str(logo_path))

        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                160, 160,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            logo_label.setPixmap(scaled_pixmap)
        else:
            logo_label.setText("Logo")
            logo_label.setStyleSheet("color: #ffdd88; font-size: 22px; font-weight: bold;")

        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)

        # ==================== APP NAME ====================
        title = QLabel("សុខា ជ្រូកកណ្ដុរ")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 22px;
            font-weight: bold;
            color: #ffdd88;
            margin-top: 10px;
        """)
        layout.addWidget(title)

        subtitle = QLabel("ប្រព័ន្ធកំពុងដំណើការ")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 13px; color: #e0c9a0;")
        layout.addWidget(subtitle)

        layout.addSpacing(25)

        # ==================== PROGRESS BAR ====================
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)          # show percentage
        self.progress.setFixedHeight(22)
        self.progress.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ★★★ This style makes it look the same on every PC ★★★
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: #5C3A1E;
                border: 1px solid #3E2714;
                border-radius: 11px;
                text-align: center;
                color: white;
                font-size: 12px;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #22C55E;
                border-radius: 10px;
            }
        """)
        layout.addWidget(self.progress)

        # Loading text
        self.loading_label = QLabel("កំពុងផ្ទុក...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setStyleSheet("font-size: 13px; color: #e0c9a0; margin-top: 8px;")
        layout.addWidget(self.loading_label)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.value = 0

    def showEvent(self, event):
        super().showEvent(event)
        self.timer.start(35)   # speed of progress

    def update_progress(self):
        self.value += 4
        self.progress.setValue(self.value)

        if self.value >= 100:
            self.timer.stop()
            self.loading_label.setText("រួចរាល់!")
            self.finished.emit()
            self.close()