class UserModel:
    def __init__(self, db):
        self.db = db

    def get_all_users(self):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT u.id, u.username, u.name, u.role, u.active,
                       u.brand_id, COALESCE(b.name, 'គ្មានម៉ាក') as brand_name
                FROM users u
                LEFT JOIN brands b ON u.brand_id = b.id
                ORDER BY u.name
            ''')
            return cursor.fetchall()
        finally:
            conn.close()

    def add_user(self, data):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, password, role, name, brand_id, active)
                VALUES (?, ?, ?, ?, ?, 1)
            ''', (data['username'], data['password'], data['role'], data['name'], data.get('brand_id')))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def update_user(self, user_id, data):
        """New method — needed since currently there's no way to edit an existing user's brand/role"""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET name=?, role=?, brand_id=?
                WHERE id=?
            ''', (data['name'], data['role'], data.get('brand_id'), user_id))
            conn.commit()
        finally:
            conn.close()

    def update_user_status(self, user_id, active):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET active = ? WHERE id = ?", (1 if active else 0, user_id))
            conn.commit()
        finally:
            conn.close()

    def update_user_password(self, user_id, new_password):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password = ? WHERE id = ?", (new_password, user_id))
            conn.commit()
        finally:
            conn.close()