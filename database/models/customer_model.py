
from ..db_manager import DatabaseManager

class CustomerModel:
    def __init__(self):
        self.db = DatabaseManager()

# =============== Customer Methods ===============
    def get_all_customers(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE is_active = 1 ORDER BY id")
        data = cursor.fetchall()
        conn.close()
        return data
    def get_customer_name(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name
            FROM customers
            WHERE is_active = 1
                       
        ''')
        data = cursor.fetchall()
        conn.close()
        return data

    def add_customer(self, data):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO customers (name, phone, address, facebook, telegram, type)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (data['name'], data['phone'], data['address'],
                data['facebook'], data['telegram'], data['type']))
            conn.commit()
            return cursor.lastrowid   # ← this was missing
        finally:
            conn.close()

    def update_customer(self, customer_id, data):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE customers 
            SET name=?, phone=?, address=?, facebook=?, telegram=?, type=?
            WHERE id=?
        ''', (data['name'], data['phone'], data['address'],
              data['facebook'], data['telegram'], data['type'], customer_id))
        conn.commit()
        conn.close()

    def delete_customer(self, customer_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE customers SET is_active= 0 WHERE id=?", (customer_id,))
        conn.commit()
        conn.close()

    def get_customer_by_id(self, customer_id):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
            return cursor.fetchone()
        finally:
            conn.close()