# General function definitions
import os
import sys
from pathlib import Path
from PySide6.QtWidgets import QMessageBox
# def resource_path(filename=""):
#     """
#     Get the correct path for resources.
#     Works in development AND after compiling to .exe (PyInstaller)
#     """
#     if getattr(sys, 'frozen', False):
#         # Running as compiled .exe
#         base_path = Path(sys._MEIPASS)
#     else:
#         # Running as normal Python script
#         base_path = Path(__file__).resolve().parent.parent

#     return base_path / "resources" / filename
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).parent.parent   # ← project root, no "resources"
    return str(base_path / relative_path)




@staticmethod
def to_float(text, default=0.0):
    if not text:
        return default
    try:
        # Remove common currency symbols and commas
        cleaned = str(text).replace(",", "").replace("$", "").replace("៛", "").strip()
        return float(cleaned)
    except (ValueError, TypeError):
        return default




