from PySide6.QtWidgets import (QVBoxLayout,QLabel,QTabWidget,QTableWidget,QDialog,QHeaderView,QTableWidgetItem,QHBoxLayout,QPushButton,QMessageBox)
from PySide6.QtGui import (QFont,QTextDocument)
from PySide6.QtPrintSupport import (QPrinter,QPrintPreviewDialog)
from PySide6.QtCore import QMarginsF, Qt,QSizeF
from PySide6.QtGui import QTextDocument, QPageSize, QPageLayout, QFont

from .invoice_template import build_receipt_html
from utils.style import TABLE_STYLE,BTN_ADD,BTN_EDIT,BTN_PRINT,BTN_CANCEL,BTN_COMPLETE
from utils.dialog import save_success_message,none_selected_warning
class OrderDetailDialog(QDialog):
    def __init__(self, parent, app, order_id):
        super().__init__(parent)
        self.app = app
        self.order_id = order_id
        self.status_changed = False

        self.setWindowTitle(f"Order {order_id}")
        self.setFixedSize(520, 480)
        self.setStyleSheet("background-color: #2A2A2A; color: white;")

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        order = self.app.order.get_order_by_id(order_id)
        self.order = order

        header = QLabel(f"📋 {order['order_number']} — {order['status'].capitalize()}")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(header)

        info = QLabel(f"ឈ្មោះអតិថិជន: {order['customer_name']}\nកាលបរិច្ឆេទ: {order['created_at']}")
        info.setStyleSheet("color: #CCCCCC;")
        layout.addWidget(info)

        items = self.app.order.get_order_items(order_id)
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["ទំនិញ", "រសជាតិ", "ចំនួន", "តម្លៃ", "តម្លៃសរុប"])
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        header = table.horizontalHeader()
        header.setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1,QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2,QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3,QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4,QHeaderView.ResizeMode.ResizeToContents)
        table.setAlternatingRowColors(True)
        table.setStyleSheet(TABLE_STYLE)

        table.setRowCount(len(items))
        for row, it in enumerate(items):
            table.setItem(row, 0, QTableWidgetItem(it['product_name']))
            table.setItem(row, 1, QTableWidgetItem(it['taste'] or ""))
            table.setItem(row, 2, QTableWidgetItem(str(it['quantity'])))
            table.setItem(row, 3, QTableWidgetItem(f"{it['unit_price']:,.2f}"))
            table.setItem(row, 4, QTableWidgetItem(f"{it['subtotal']:,.2f}"))
        layout.addWidget(table)
        # Value color, label stays muted/white
        v = "#FCD34D"   # amber/gold for key numbers
        label_color = "#CCCCCC"
        total_color = "#22C55E"  # green for final total
        paid_color = "#3B82F6"   # blue for paid amount
        delivery_color = "#F97316"  # orange for delivery fee
        total = order['total_amount']-order['paid_amount']-order['discount']+order['delivery_fee']
        totals = QLabel(
            f"<span style='color:{label_color};'>សរុប:</span> <span style='color:{total_color};'>{order['total_amount']:,.2f} $</span>"
            f"<span style='color:{label_color};'>ថ្លៃដឹក:</span> <span style='color:{delivery_color};'>{order['delivery_fee']:,.2f} $</span>"
            f"<span style='color:{label_color};'>បានបង់:</span> <span style='color:{paid_color};'>-{order['paid_amount']:,.2f} $</span>"
            f"<span style='color:{label_color};'>បញ្ចុះតម្លៃ:</span> <span style='color:{v};'>-{order['discount']:,.2f} $</span>"
            f"<span style='color:{label_color};'>សរុបចុងក្រោយ:</span> <span style='color:{total_color};'>{total:,.2f} $</span>"
        )
        totals.setStyleSheet("font-size: 12px;")
        layout.addWidget(totals)

        btn_layout = QHBoxLayout()

        if order['status'] == 'pending':
            edit_btn = QPushButton("កែប្រែ")
            edit_btn.setStyleSheet(BTN_EDIT)
            edit_btn.clicked.connect(self.edit_order)
            btn_layout.addWidget(edit_btn)
            complete_btn = QPushButton("កម្មង់")
            complete_btn.setStyleSheet(BTN_COMPLETE)
            complete_btn.clicked.connect(lambda: self.set_status('completed'))
            btn_layout.addWidget(complete_btn)

            cancel_btn = QPushButton("លុបចោល")
            cancel_btn.setStyleSheet(BTN_CANCEL)
            cancel_btn.clicked.connect(lambda: self.set_status('cancelled'))
            btn_layout.addWidget(cancel_btn)


        print_btn = QPushButton("ព្រីន")
        print_btn.setStyleSheet(BTN_PRINT)
        print_btn.clicked.connect(self.print_receipt)
        close_btn = QPushButton("ចាកចេញ")
        close_btn.setStyleSheet(BTN_CANCEL)
        close_btn.clicked.connect(self.close)

        btn_layout.addWidget(print_btn)
        btn_layout.addWidget(close_btn)

       
        

        layout.addLayout(btn_layout)

    def set_status(self, new_status):
        try:
            brand_id = self.order['brand_id']
            updated_by = self.app.user.get('id') if hasattr(self.app, 'user') else None
            self.app.order.update_order_status(self.order_id, new_status, brand_id=brand_id, updated_by=updated_by)
            self.status_changed = True
            save_success_message(self, message=f"ការកម្មង់កំពុងស្ថិតក្នុងស្ថានភាព {new_status}.", win_title="បច្ចុប្បន្នភាព")
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update order: {e}")
    

    def edit_order(self):
        # parent is OrderWidget
        parent = self.parent()
        if hasattr(parent, 'load_order_for_edit'):
            parent.load_order_for_edit(self.order_id)
            self.close()
        else:
            
            none_selected_warning(self,message="មិនអាចធ្វើការកែប្រែបាន",win_title="កំហុស")


    def print_receipt(self):
        try:
            html = build_receipt_html(self.app, self.order, self.app.order.get_order_items(self.order_id))

            doc = QTextDocument()
            doc.setDefaultFont(QFont("Consolas", 11))
            doc.setHtml(html)

            printer = QPrinter(QPrinter.HighResolution)

            saved_printer_name = self.app.settings.get("receipt_printer", "")
            from PySide6.QtPrintSupport import QPrinterInfo
            available_printers = QPrinterInfo.availablePrinterNames()
            if saved_printer_name and saved_printer_name in available_printers:
                printer.setPrinterName(saved_printer_name)

            a5_size = QPageSize(QSizeF(148, 210), QPageSize.Millimeter, "A5 Custom")
            printer.setPageSize(a5_size)
            printer.setPageOrientation(QPageLayout.Portrait)
            printer.setPageMargins(QMarginsF(8, 8, 8, 8), QPageLayout.Millimeter)
            doc.setPageSize(printer.pageRect(QPrinter.Point).size())

            preview = QPrintPreviewDialog(printer, self)

            def paint(p):
                doc.setPageSize(p.pageRect(QPrinter.Point).size())
                doc.print_(p)

            preview.paintRequested.connect(paint)
            preview.exec()

        except Exception as e:
            QMessageBox.critical(self, "Print Error", f"Failed to open print preview: {e}")




