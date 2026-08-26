from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from datetime import datetime


class DashboardWidget(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)   # ← reduce outer margin
        layout.setSpacing(12)                       # ← reduce space between sections

        # ==================== METRIC CARDS ====================    
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)                 # ← tighter between cards
        cards_layout.setContentsMargins(0, 0, 0, 0)

        self.today_card = self.build_card("💰", "ការលក់ប្រចាំថ្ងៃ", "$0.00", "#22C55E")
        self.month_card = self.build_card("📈", "ការលក់ប្រចាំខែ", "$0.00", "#3B82F6")
        self.pending_card = self.build_card("⏳", "ការកម្មង់ដែលកំពុងរងចាំ", "0", "#F59E0B")
        self.orders_today_card = self.build_card("🧾", "ការកម្មង់ប្រចាំថ្ងៃ", "0", "#A855F7")

        for card in (self.today_card, self.month_card, self.pending_card, self.orders_today_card):
            cards_layout.addWidget(card)

        

        # ==================== CHARTS ROW ====================
        charts_row = QHBoxLayout()
        charts_row.setSpacing(12)
        charts_row.setContentsMargins(0, 0, 0, 0)

        # Donut: pending vs completed
        donut_card = QFrame()
        donut_card.setStyleSheet("background-color: #2A2A2A; border-radius: 12px;")
        donut_card.setFixedHeight(350)
        donut_layout = QVBoxLayout(donut_card)
        donut_layout.setContentsMargins(18, 16, 18, 16)
        donut_title = QLabel("បច្ចុប្បន្នភាពការកម្មង់")
        donut_title.setStyleSheet("font-size: 12px; color: white;")
        donut_layout.addWidget(donut_title)

        self.donut_figure = Figure(figsize=(3.2, 2.8), facecolor="#2A2A2A")
        self.donut_canvas = FigureCanvasQTAgg(self.donut_figure)
        self.donut_canvas.setMinimumHeight(150)
        donut_layout.addWidget(self.donut_canvas)
        charts_row.addWidget(donut_card, stretch=1)

        # Line: 7-day trend
        trend_card = QFrame()
        trend_card.setFixedHeight(350)
        trend_card.setStyleSheet("background-color: #2A2A2A; border-radius: 12px;")
        trend_layout = QVBoxLayout(trend_card)
        trend_layout.setContentsMargins(18, 16, 18, 16)
        trend_title = QLabel("ការវិភាគការលក់ — 7 ថ្ងៃចុងក្រោយ")
        trend_title.setStyleSheet("font-size: 12px; font-weight: bold; color: white;")
        trend_layout.addWidget(trend_title)

        self.figure = Figure(figsize=(6, 2.8), facecolor="#2A2A2A")
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setMinimumHeight(150)
        trend_layout.addWidget(self.canvas)
        charts_row.addWidget(trend_card, stretch=2)
        layout.addLayout(cards_layout)
        layout.addLayout(charts_row)
        layout.addStretch()

        # ==================== RECENT ORDERS TABLE ====================

        self.refresh()

    def build_card(self, icon, label_text, value_text, color):
        card = QFrame()
        card.setStyleSheet("background-color: #2A2A2A; border-radius: 12px;")
        card.setFixedHeight(200)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(8)

        top_row = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"""
            background-color: {color}33; color: {color};
            font-size: 18px; border-radius: 8px; padding: 6px 10px;
        """)
        top_row.addWidget(icon_label)
        top_row.addStretch()
        card_layout.addLayout(top_row)

        label = QLabel(label_text)
        label.setStyleSheet("color: #AAAAAA; font-size: 13px;")
        card_layout.addWidget(label)

        value = QLabel(value_text)
        value.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        value.setObjectName("value")
        card_layout.addWidget(value)

        return card

    def update_card_value(self, card, new_value):
        value_label = card.findChild(QLabel, "value")
        if value_label:
            value_label.setText(new_value)

    def draw_donut(self, completed, pending, cancelled):
        self.donut_figure.clear()
        ax = self.donut_figure.add_subplot(111)

        values = [v for v in (completed, pending, cancelled) if v > 0]
        labels_colors = [
            ("Completed", "#22C55E", completed),
            ("Pending", "#F59E0B", pending),
            ("Cancelled", "#EF4444", cancelled),
        ]
        colors = [c for _, c, v in labels_colors if v > 0]
        total = completed + pending + cancelled

        if total == 0:
            ax.text(0.5, 0.5, "No orders yet", ha='center', va='center', color="#888", fontsize=10)
            ax.axis("off")
        else:
            ax.pie(values, colors=colors, startangle=90, wedgeprops=dict(width=0.4, edgecolor="#2A2A2A"))
            ax.text(0, 0.05, str(total), ha='center', va='center', color="white", fontsize=20, fontweight='bold')
            ax.text(0, -0.15, "Orders", ha='center', va='center', color="#999", fontsize=9)
            ax.set_aspect("equal")

        self.donut_figure.tight_layout()
        self.donut_canvas.draw()

    def draw_trend_chart(self, trend_data):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor("#2A2A2A")

        labels = [datetime.strptime(d['day'], "%Y-%m-%d").strftime("%a") for d in trend_data]
        revenues = [d['revenue'] for d in trend_data]

        ax.plot(labels, revenues, color="#3B82F6", linewidth=2, marker='o', markersize=5,
                markerfacecolor="#3B82F6", markeredgecolor="#2A2A2A")
        ax.fill_between(range(len(labels)), revenues, color="#3B82F6", alpha=0.1)

        ax.tick_params(colors="#999", labelsize=9)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.yaxis.grid(True, color="#3A3A3A", linestyle="-", linewidth=0.5)
        ax.set_axisbelow(True)

        self.figure.tight_layout()
        self.canvas.draw()

    def status_badge(self, status):
        colors = {
            "completed": ("#22C55E", "#0F3D24"),
            "pending": ("#F59E0B", "#3D2E0A"),
            "cancelled": ("#EF4444", "#3D1414"),
        }
        text_color, bg_color = colors.get(status.lower(), ("#999", "#333"))
        item = QTableWidgetItem(status.capitalize())
        item.setForeground(Qt.GlobalColor.white)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        return item

    def refresh(self):
        try:
            today_str = QDate.currentDate().toString("yyyy-MM-dd")
            month_str = QDate.currentDate().toString("yyyy-MM")
            first_day = f"{month_str}-01"
            last_day = QDate.fromString(first_day, "yyyy-MM-dd").addMonths(1).addDays(-1).toString("yyyy-MM-dd")

            today_summary = self.app.order.get_sales_summary(today_str, today_str)
            month_summary = self.app.order.get_sales_summary(first_day, last_day)

            self.update_card_value(self.today_card, f"${today_summary['total_revenue']:,.2f}")
            self.update_card_value(self.month_card, f"${month_summary['total_revenue']:,.2f}")
            self.update_card_value(self.orders_today_card, str(today_summary['order_count']))
        except Exception as e:
            print("Dashboard summary error:", e)

        try:
            pending_count = self.app.order.get_pending_count()
            self.update_card_value(self.pending_card, str(pending_count))
        except Exception as e:
            print("Dashboard pending count error:", e)

        try:
            all_orders = self.app.order.get_orders(None)
            completed = sum(1 for o in all_orders if o['status'] == 'completed')
            pending = sum(1 for o in all_orders if o['status'] == 'pending')
            cancelled = sum(1 for o in all_orders if o['status'] == 'cancelled')
            self.draw_donut(completed, pending, cancelled)
        except Exception as e:
            print("Dashboard donut error:", e)

        try:
            trend = self.app.order.get_sales_trend(7)
            self.draw_trend_chart(trend)
        except Exception as e:
            print("Dashboard chart error:", e)

        # try:
        #     recent = self.app.order.get_recent_orders(6)
        #     self.recent_table.setSortingEnabled(False)
        #     self.recent_table.setRowCount(len(recent))
        #     for row, o in enumerate(recent):
        #         self.recent_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        #         self.recent_table.setItem(row, 1, QTableWidgetItem(o['order_number'] or ""))
        #         self.recent_table.setItem(row, 2, QTableWidgetItem(o['customer_name'] or ""))
        #         self.recent_table.setItem(row, 3, QTableWidgetItem(f"${o['total_amount']:,.2f}"))
        #         self.recent_table.setItem(row, 4, self.status_badge(o['status']))
        #     self.recent_table.setSortingEnabled(True)
        # except Exception as e:
        #     print("Dashboard recent orders error:", e)