"""Shared printer setup so every print path honours Settings → Printer → paper size.
(Previously the paper size was saved but every print was hard-coded to A5.)"""
from PySide6.QtCore import QMarginsF, QSizeF
from PySide6.QtGui import QPageLayout, QPageSize

PAPER_SIZES_MM = {
    "A5": (QSizeF(148, 210), 8),
    "A4": (QSizeF(210, 297), 10),
    "80MM": (QSizeF(80, 297), 3),    # receipt roll: 80mm wide, long page
}


def apply_paper_settings(printer, settings_model):
    key = (settings_model.get("receipt_paper_size", "A5") or "A5").upper()
    size_mm, margin = PAPER_SIZES_MM.get(key, PAPER_SIZES_MM["A5"])
    page_size = QPageSize(size_mm, QPageSize.Millimeter, f"{key} Receipt")
    printer.setPageSize(page_size)
    printer.setPageOrientation(QPageLayout.Portrait)
    printer.setPageMargins(QMarginsF(margin, margin, margin, margin), QPageLayout.Millimeter)
    return page_size
