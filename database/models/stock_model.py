# Version Cluad AI 

from .stock_utils import adjust_stock_in_transaction
class StockModel:
    def __init__(self, db):
        self.db = db

    def get_stock(self, product_id, brand_id):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT quantity FROM stock WHERE product_id = ? AND brand_id = ?",
                (product_id, brand_id)
            )
            row = cursor.fetchone()
            return row['quantity'] if row else 0
        finally:
            conn.close()

    def get_all_stock(self, brand_id=None):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            if brand_id:
                cursor.execute('''
                    SELECT s.id, s.product_id, p.name as product_name,
                        s.brand_id, b.name as brand_name, s.quantity, s.updated_at,
                        u.name as unit_name
                    FROM stock s
                    JOIN products p ON s.product_id = p.id
                    JOIN brands b ON s.brand_id = b.id
                    LEFT JOIN units u ON p.units_id = u.id
                    WHERE s.brand_id = ?
                    ORDER BY p.name
                ''', (brand_id,))
            else:
                cursor.execute('''
                    SELECT s.id, s.product_id, p.name as product_name,
                        s.brand_id, b.name as brand_name, s.quantity, s.updated_at,
                        u.name as unit_name
                    FROM stock s
                    JOIN products p ON s.product_id = p.id
                    JOIN brands b ON s.brand_id = b.id
                    LEFT JOIN units u ON p.units_id = u.id
                    ORDER BY b.name, p.name
                ''')
            return cursor.fetchall()
        finally:
            conn.close()

    def adjust_stock(self, product_id, brand_id, movement_type, quantity, reason="",
                      reference_order_id=None, created_by=None):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            new_qty = adjust_stock_in_transaction(
                cursor, product_id, brand_id, movement_type, quantity,
                reason, reference_order_id, created_by
            )
            conn.commit()
            return new_qty
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_movements(self, brand_id=None, product_search=None, period=None,
                   date_from=None, date_to=None, sort_by="date_desc", limit=500):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            query = '''
                SELECT sm.id, sm.movement_type, sm.quantity, sm.reason, sm.created_at,
                    p.name as product_name, b.name as brand_name,
                    COALESCE(u.name, 'System') as created_by_name
                FROM stock_movements sm
                JOIN products p ON sm.product_id = p.id
                JOIN brands b ON sm.brand_id = b.id
                LEFT JOIN users u ON sm.created_by = u.id
                WHERE 1=1
            '''
            params = []

            if brand_id:
                query += " AND sm.brand_id = ?"
                params.append(brand_id)
            if product_search:
                query += " AND p.name LIKE ?"
                params.append(f"%{product_search}%")

            if period == "today":
                query += " AND DATE(sm.created_at) = DATE('now', 'localtime')"
            elif period == "week":
                query += " AND DATE(sm.created_at) >= DATE('now', 'localtime', '-6 days')"
            elif period == "month":
                query += " AND strftime('%Y-%m', sm.created_at) = strftime('%Y-%m', 'now', 'localtime')"
            elif period == "year":
                query += " AND strftime('%Y', sm.created_at) = strftime('%Y', 'now', 'localtime')"
            elif period == "custom":
                if date_from:
                    query += " AND sm.created_at >= ?"
                    params.append(date_from)
                if date_to:
                    query += " AND sm.created_at <= ?"
                    params.append(date_to)

            if sort_by == "date_asc":
                query += " ORDER BY sm.created_at ASC"
            elif sort_by == "product":
                query += " ORDER BY p.name ASC"
            else:
                query += " ORDER BY sm.created_at DESC"

            query += " LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            return cursor.fetchall()
        finally:
            conn.close()

    def transfer_stock(self, product_id, from_brand_id, to_brand_id, quantity, note="", transferred_by=None):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()

            # Check source has enough stock
            cursor.execute(
                "SELECT quantity FROM stock WHERE product_id = ? AND brand_id = ?",
                (product_id, from_brand_id)
            )
            row = cursor.fetchone()
            available = row['quantity'] if row else 0

            if available < quantity:
                raise ValueError(f"ស្តុកមិនគ្រប់គ្រាន់ដើម្បីផ្ទេរ (មាន {available:,.2f}, ស្នើ {quantity:,.2f})")

            # Deduct from source, log 'out' movement
            adjust_stock_in_transaction(
                cursor, product_id=product_id, brand_id=from_brand_id,
                movement_type='out', quantity=quantity,
                reason=f"ផ្ទេរទៅសាខាផ្សេង{': ' + note if note else ''}",
                created_by=transferred_by
            )

            # Add to destination, log 'in' movement
            adjust_stock_in_transaction(
                cursor, product_id=product_id, brand_id=to_brand_id,
                movement_type='in', quantity=quantity,
                reason=f"ផ្ទេរមកពីសាខាផ្សេង{': ' + note if note else ''}",
                created_by=transferred_by
            )

            # Log the transfer itself in stock_transfers
            cursor.execute('''
                INSERT INTO stock_transfers
                    (product_id, from_brand_id, to_brand_id, quantity, note, transferred_by)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (product_id, from_brand_id, to_brand_id, quantity, note, transferred_by))

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_stock_map_for_brand(self, brand_id):
        """Returns {product_id: quantity} for all tracked stock under a brand."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT product_id, quantity FROM stock WHERE brand_id = ?",
                (brand_id,)
            )
            return {row['product_id']: row['quantity'] for row in cursor.fetchall()}
        finally:
            conn.close()

    # StockModel.py 
    def get_available_products_for_brand(self, brand_id):
        """Returns products that have a stock record with quantity > 0 for this brand."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.id, p.code, p.name, p.price, p.description, p.category_id,
                    u.name as unit, c.name as category, s.quantity as stock_qty
                FROM products p
                JOIN stock s ON s.product_id = p.id AND s.brand_id = ?
                LEFT JOIN units u ON p.units_id = u.id
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.is_active = 1 AND s.quantity > 0
                ORDER BY p.name
            ''', (brand_id,))
            return cursor.fetchall()
        finally:
            conn.close()