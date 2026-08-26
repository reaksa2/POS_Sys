class SettingsModel:
    def __init__(self, db):
        self.db = db

    def get(self, key, default=None):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row['value'] if row else default
        finally:
            conn.close()

    def get_all(self):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM settings")
            return {row['key']: row['value'] for row in cursor.fetchall()}
        finally:
            conn.close()

    def set(self, key, value):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
            ''', (key, str(value)))
            conn.commit()
        finally:
            conn.close()

    def set_many(self, data: dict):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            for key, value in data.items():
                cursor.execute('''
                    INSERT INTO settings (key, value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
                ''', (key, str(value)))
            conn.commit()
        finally:
            conn.close()