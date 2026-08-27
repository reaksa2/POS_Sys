import requests
from PySide6.QtCore import QThread, Signal


CURRENT_VERSION = "1.3.0"   # ← update this each time you release
GITHUB_REPO = "reaksa2/POS_Sys"   # your repo


def get_latest_version_info():
    """Returns (latest_version, download_url, release_notes) or raises on failure."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    data = response.json()

    latest_version = data.get("tag_name", "").lstrip("v")
    release_notes = data.get("body", "")

    download_url = ""
    for asset in data.get("assets", []):
        if asset.get("name", "").endswith(".exe"):
            download_url = asset.get("browser_download_url", "")
            break

    return latest_version, download_url, release_notes


def is_newer_version(latest, current):
    """Simple version comparison, e.g. '1.4.0' > '1.3.0'"""
    def parse(v):
        return tuple(int(x) for x in v.split(".") if x.isdigit())
    try:
        return parse(latest) > parse(current)
    except Exception:
        return False


class UpdateCheckWorker(QThread):
    update_available = Signal(str, str, str)   # latest_version, download_url, notes
    no_update = Signal()
    check_failed = Signal(str)

    def run(self):
        try:
            latest_version, download_url, notes = get_latest_version_info()
            if is_newer_version(latest_version, CURRENT_VERSION):
                self.update_available.emit(latest_version, download_url, notes)
            else:
                self.no_update.emit()
        except Exception as e:
            self.check_failed.emit(str(e))