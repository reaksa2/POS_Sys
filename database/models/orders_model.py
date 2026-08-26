import uuid
from datetime import datetime, date, timedelta
from .stock_utils import adjust_stock_in_transaction


class OrderModel:
    def __init__(self, db):
        self.db = db

    def generate_order_number(self):
        """e.g. SK-20260810-4F2A1B"""
        return f"SK-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    # ============================================
    # HISTORY BY DATE RANGE
    # ============================================
    def get_orders_history_by_range(self, start_datetime, end_datetime):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT o.id, o.order_number, o.customer_id,
                    COALESCE(c.name, 'Walk-in') as customer_name,
                    o.total_amount, o.delivery_fee, o.discount, o.status, o.created_at,
                    o.payment_method, o.payment_status, o.paid_amount, o.pickup_time, o.brand_id
                FROM orders o
                LEFT JOIN customers c ON o.customer_id = c.id
                WHERE o.status IN ('completed', 'cancelled')
                AND o.created_at BETWEEN ? AND ?
                ORDER BY o.created_at DESC
            ''', (start_datetime, end_datetime))
            return cursor.fetchall()
        finally:
            conn.close()

    def get_history_summary_by_range(self, start_datetime, end_datetime):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT
                    COALESCE(SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END), 0) as order_count,
                    COALESCE(SUM(CASE WHEN status = 'completed' THEN total_amount ELSE 0 END), 0) as total_revenue,
                    COALESCE(SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END), 0) as cancelled_count
                FROM orders
                WHERE created_at BETWEEN ? AND ?
            ''', (start_datetime, end_datetime))
            return cursor.fetchone()
        finally:
            conn.close()

    # ============================================
    # PLACE ORDER
    # ============================================
    def place_order(self, customer_id, items, delivery_fee=0, discount=0, order_by=None,
                     status='pending', payment_method='Cash', payment_status='unpaid',
                     paid_amount=0, pickup_time=None, brand_id=None):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            items_total = sum(item['price'] * item['quantity'] for item in items)
            total_amount = items_total   # ← items-only; delivery/discount applied at display/receipt time
            order_number = self.generate_order_number()

            cursor.execute('''
                INSERT INTO orders
                    (order_number, customer_id, order_by, total_amount, delivery_fee, discount,
                     status, payment_method, payment_status, paid_amount, pickup_time, brand_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (order_number, customer_id, order_by, total_amount, delivery_fee, discount,
                  status, payment_method, payment_status, paid_amount, pickup_time, brand_id))

            order_id = cursor.lastrowid

            for item in items:
                subtotal = item['price'] * item['quantity']
                cursor.execute('''
                    INSERT INTO order_items
                        (order_id, product_id, product_name, taste, unit, quantity, weight, unit_price, subtotal)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    order_id, item.get('price_id'), item['name'], item.get('taste', ''), item.get('unit', ''),
                    item['quantity'], item.get('weight'), item['price'], subtotal
                ))

                if status == 'completed' and brand_id and item.get('price_id'):
                    adjust_stock_in_transaction(
                        cursor, product_id=item['price_id'], brand_id=brand_id,
                        movement_type='out', quantity=item['quantity'],
                        reason='ការលក់', reference_order_id=order_id, created_by=order_by
                    )

            conn.commit()
            return order_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    # ============================================
    # UPDATE EXISTING (PENDING) ORDER
    # ============================================
    def update_order(self, order_id, customer_id, items, delivery_fee, discount, status='pending',
                      payment_method='Cash', payment_status='unpaid', paid_amount=0,
                      pickup_time=None, brand_id=None, updated_by=None):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()

            # Check current status before overwriting, so we know if we're transitioning INTO completed
            cursor.execute("SELECT status, brand_id FROM orders WHERE id = ?", (order_id,))
            existing = cursor.fetchone()
            old_status = existing['status'] if existing else None
            old_brand_id = existing['brand_id'] if existing else None

            items_total = sum(item['price'] * item['quantity'] for item in items)
            total_amount = items_total

            # Use the brand this order was originally created under, unless explicitly overridden
            effective_brand_id = brand_id if brand_id else old_brand_id

            cursor.execute('''
                UPDATE orders
                SET customer_id=?, total_amount=?, delivery_fee=?, discount=?, status=?,
                    payment_method=?, payment_status=?, paid_amount=?, pickup_time=?, brand_id=?
                WHERE id=?
            ''', (customer_id, total_amount, delivery_fee, discount, status,
                  payment_method, payment_status, paid_amount, pickup_time, effective_brand_id, order_id))

            cursor.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))

            for item in items:
                subtotal = item['price'] * item['quantity']
                cursor.execute('''
                    INSERT INTO order_items
                        (order_id, product_id, product_name, taste, unit, quantity, weight, unit_price, subtotal)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    order_id, item.get('price_id'), item['name'], item.get('taste', ''), item.get('unit', ''),
                    item['quantity'], item.get('weight'), item['price'], subtotal
                ))

                # Deduct stock only if we're NOW completed and WEREN'T before (avoid double-deduction)
                if status == 'completed' and old_status != 'completed' and effective_brand_id and item.get('price_id'):
                    adjust_stock_in_transaction(
                        cursor, product_id=item['price_id'], brand_id=effective_brand_id,
                        movement_type='out', quantity=item['quantity'],
                        reason='ការលក់ (កែប្រែ)', reference_order_id=order_id, created_by=updated_by
                    )

            conn.commit()
            return order_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    # ============================================
    # ORDER LISTS
    # ============================================
    def get_orders(self, status_filter=None):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            if status_filter:
                cursor.execute('''
                    SELECT o.id, o.order_number, o.customer_id,
                            COALESCE(c.name, 'Walk-in') as customer_name,
                            o.total_amount, o.delivery_fee, o.discount, o.status, o.created_at,
                            o.payment_method, o.payment_status, o.paid_amount, o.pickup_time, o.brand_id
                    FROM orders o
                    LEFT JOIN customers c ON o.customer_id = c.id
                    WHERE o.status = ?
                    ORDER BY o.created_at ASC
                ''', (status_filter,))
            else:
                cursor.execute('''
                    SELECT o.id, o.order_number, o.customer_id,
                            COALESCE(c.name, 'Walk-in') as customer_name,
                            o.total_amount, o.delivery_fee, o.discount, o.status, o.created_at,
                            o.payment_method, o.payment_status, o.paid_amount, o.pickup_time, o.brand_id
                    FROM orders o
                    LEFT JOIN customers c ON o.customer_id = c.id
                    ORDER BY o.created_at DESC
                ''')
            return cursor.fetchall()
        finally:
            conn.close()

    def get_orders_history(self):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT o.id, o.order_number, o.customer_id,
                        COALESCE(c.name, 'Walk-in') as customer_name,
                        o.total_amount, o.delivery_fee, o.discount, o.status, o.created_at,
                        o.payment_method, o.payment_status, o.paid_amount, o.pickup_time, o.brand_id
                FROM orders o
                LEFT JOIN customers c ON o.customer_id = c.id
                WHERE o.status IN ('completed', 'cancelled')
                ORDER BY o.created_at DESC
            ''')
            return cursor.fetchall()
        finally:
            conn.close()

    def get_order_by_id(self, order_id):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT o.id, o.order_number, o.customer_id,
                    COALESCE(c.name, 'Walk-in') as customer_name,
                    c.phone, c.address, c.facebook, c.telegram,
                    o.total_amount, o.delivery_fee, o.discount, o.status, o.created_at,
                    o.payment_method, o.payment_status, o.paid_amount, o.pickup_time, o.brand_id
                FROM orders o
                LEFT JOIN customers c ON o.customer_id = c.id
                WHERE o.id = ?
            ''', (order_id,))
            return cursor.fetchone()
        finally:
            conn.close()

    def get_order_items(self, order_id):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT product_id, product_name, taste, unit, quantity, unit_price, subtotal
                FROM order_items WHERE order_id = ?
            ''', (order_id,))
            return cursor.fetchall()
        finally:
            conn.close()

    def update_order_status(self, order_id, new_status, brand_id=None, updated_by=None):
        """Used by OrderDetailDialog's set_status — handles stock deduction on completion."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()

            cursor.execute("SELECT status, brand_id FROM orders WHERE id = ?", (order_id,))
            row = cursor.fetchone()
            old_status = row['status'] if row else None
            effective_brand_id = brand_id if brand_id else (row['brand_id'] if row else None)

            cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))

            # Deduct stock only when transitioning INTO completed (not already completed)
            if new_status == 'completed' and old_status != 'completed' and effective_brand_id:
                cursor.execute('''
                    SELECT product_id, quantity FROM order_items WHERE order_id = ?
                ''', (order_id,))
                for item in cursor.fetchall():
                    if item['product_id']:
                        adjust_stock_in_transaction(
                            cursor, product_id=item['product_id'], brand_id=effective_brand_id,
                            movement_type='out', quantity=item['quantity'],
                            reason='ការលក់ (បញ្ជាក់)', reference_order_id=order_id, created_by=updated_by
                        )

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    # ============================================
    # REPORTS
    # ============================================
    def get_daily_sales(self, date_str):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, order_number, total_amount, delivery_fee, discount, status, created_at
                FROM orders
                WHERE DATE(created_at) = ? AND status = 'completed'
                ORDER BY created_at DESC
            ''', (date_str,))
            return cursor.fetchall()
        finally:
            conn.close()

    def get_monthly_sales(self, year_month):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, order_number, total_amount, delivery_fee, discount, status, created_at
                FROM orders
                WHERE strftime('%Y-%m', created_at) = ? AND status = 'completed'
                ORDER BY created_at DESC
            ''', (year_month,))
            return cursor.fetchall()
        finally:
            conn.close()

    def get_sales_summary(self, start_date, end_date):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) as order_count,
                    COALESCE(SUM(total_amount), 0) as total_revenue,
                    COALESCE(SUM(delivery_fee), 0) as total_delivery,
                    COALESCE(SUM(discount), 0) as total_discount
                FROM orders
                WHERE DATE(created_at) BETWEEN ? AND ? AND status = 'completed'
            ''', (start_date, end_date))
            return cursor.fetchone()
        finally:
            conn.close()

    def get_top_products(self, start_date, end_date, limit=10):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT oi.product_name, oi.taste, SUM(oi.quantity) as total_qty,
                    SUM(oi.subtotal) as total_revenue
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                WHERE DATE(o.created_at) BETWEEN ? AND ? AND o.status = 'completed'
                GROUP BY oi.product_name, oi.taste
                ORDER BY total_revenue DESC
                LIMIT ?
            ''', (start_date, end_date, limit))
            return cursor.fetchall()
        finally:
            conn.close()

    def get_sales_trend(self, days=7):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DATE(created_at) as day, SUM(total_amount) as revenue, COUNT(*) as order_count
                FROM orders
                WHERE status = 'completed' AND DATE(created_at) >= DATE('now', ?)
                GROUP BY DATE(created_at)
                ORDER BY day ASC
            ''', (f'-{days-1} days',))
            rows = {r['day']: r for r in cursor.fetchall()}

            result = []
            for i in range(days - 1, -1, -1):
                d = (date.today() - timedelta(days=i)).isoformat()
                if d in rows:
                    result.append({"day": d, "revenue": rows[d]['revenue'], "order_count": rows[d]['order_count']})
                else:
                    result.append({"day": d, "revenue": 0, "order_count": 0})
            return result
        finally:
            conn.close()

    def get_pending_count(self):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM orders WHERE status = 'pending'")
            return cursor.fetchone()['cnt']
        finally:
            conn.close()

    def get_recent_orders(self, limit=8):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT o.id, o.order_number, COALESCE(c.name, 'Walk-in') as customer_name,
                    o.total_amount, o.status, o.created_at
                FROM orders o
                LEFT JOIN customers c ON o.customer_id = c.id
                ORDER BY o.created_at DESC
                LIMIT ?
            ''', (limit,))
            return cursor.fetchall()
        finally:
            conn.close()