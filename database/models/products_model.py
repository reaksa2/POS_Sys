from ..db_manager import DatabaseManager

class ProductModel:
    def __init__(self):
        self.db = DatabaseManager()


    # ===================== PRODUCT METHODS =====================
     
    def get_all_products(self):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.id, p.code, p.name, p.price, p.description,p.category_id,
                    u.name as unit, c.name as category
                FROM products p
                LEFT JOIN units u ON p.units_id = u.id
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.is_active = 1
                ORDER BY p.name
            ''')
            return cursor.fetchall()
        finally:
            conn.close()
    def get_product_name(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.id, p.name FROM products p WHERE p.is_active = 1              
                       
        ''')

        data = cursor.fetchall()
        conn.close()
        return data
    

    def add_product(self, data):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO products (code,name, category_id,units_id,price,created_by, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (data['code'], data['name'], data['category_id'],data['unit_id'],data['price'],data['created_by'], data['description']))
        conn.commit()
        conn.close()


    def update_product(self, product_id, data):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE products
            SET name=?, units_id=?, category_id=?,price=?, description=?
            WHERE id=?
        ''', ( data['name'],data['unit_id'], data['category_id'],data['price'], data['description'], product_id))
        conn.commit()
        conn.close()

    def delete_product(self, product_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE products set is_active = 0 WHERE id=?", (product_id,))
        conn.commit()
        conn.close()

    def de_activate_product(self, product_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE products SET is_active=0 WHERE id=?", (product_id,))
        conn.commit()
        conn.close()