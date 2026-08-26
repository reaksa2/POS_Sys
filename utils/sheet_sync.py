import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import socket


def has_internet(timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
        return True
    except OSError:
        return False


class SheetsSync:
    def __init__(self, credentials_path, sheet_id):
        self.credentials_path = credentials_path
        self.sheet_id = sheet_id

    def connect(self):
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file(self.credentials_path, scopes=scopes)
        client = gspread.authorize(creds)
        return client.open_by_key(self.sheet_id)

    def get_all_table_names(self, db):
        conn = db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            return [row['name'] for row in cursor.fetchall()]
        finally:
            conn.close()

    def sync_table(self, db, spreadsheet, table_name):
        conn = db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()

            if not rows:
                return 0

            headers = list(rows[0].keys())

            try:
                worksheet = spreadsheet.worksheet(table_name)
                worksheet.clear()
            except gspread.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(title=table_name, rows=max(len(rows) + 10, 100), cols=len(headers) + 2)

            data = [headers]
            for row in rows:
                data.append([str(row[h]) if row[h] is not None else "" for h in headers])

            worksheet.update(data)
            return len(rows)
        finally:
            conn.close()

    def sync_all_tables(self, db):
        """Syncs EVERY table in the database. Returns {table_name: row_count}."""
        spreadsheet = self.connect()
        table_names = self.get_all_table_names(db)

        results = {}
        for table_name in table_names:
            try:
                count = self.sync_table(db, spreadsheet, table_name)
                results[table_name] = count
            except Exception as e:
                results[table_name] = f"Error: {e}"

        results['_synced_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return results