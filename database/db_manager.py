import sqlite3
from pathlib import Path
from datetime import datetime

class DatabaseManager:
    def __init__(self):
        self.db_path = Path("database/pos.db")
        self.db_path.parent.mkdir(exist_ok=True)
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")   # Enable relationships
        return conn

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        # ==================== CUSTOMERS ====================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT UNIQUE,
                address TEXT,
                facebook TEXT,
                telegram TEXT,
                type TEXT DEFAULT 'New',
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT (datetime('now', 'localtime'))
            )
        ''')

        # ==================== CATEGORIES ====================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT (datetime('now', 'localtime'))
            )
        ''')

        # ==================== TASTE ====================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS taste (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT (datetime('now', 'localtime'))
            )
        ''')

        # ==================== UNITS ====================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS units (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT (datetime('now', 'localtime'))
            )
        ''')

        # ==================== USERS ====================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT,
                name TEXT,
                brand_id INTEGER,          -- ← add this
                active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY (brand_id) REFERENCES brands(id)   -- ← add this
            )
        ''')

        # ==================== PRODUCTS ====================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT,
                name TEXT NOT NULL,
                category_id INTEGER,
                units_id INTEGER,
                price REAL NOT NULL DEFAULT 0,
                created_by INTEGER,
                description TEXT,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY (category_id) REFERENCES categories(id),
                FOREIGN KEY (units_id) REFERENCES units(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')

        # ============================================
        # ORDERS
        # ============================================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number TEXT UNIQUE NOT NULL,
                customer_id INTEGER,
                order_by INTEGER,
                brand_id INTEGER,
                total_amount REAL NOT NULL DEFAULT 0,
                delivery_fee REAL NOT NULL DEFAULT 0,
                discount REAL NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'pending',
                payment_method TEXT DEFAULT 'Cash',
                payment_status TEXT DEFAULT 'unpaid',
                paid_amount REAL DEFAULT 0,
                pickup_time TEXT,
                note TEXT,
                created_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE RESTRICT,
                FOREIGN KEY (order_by) REFERENCES users(id) ON DELETE RESTRICT,
                FOREIGN KEY (brand_id) REFERENCES brands(id)
            )
        ''')

        # ============================================
        # ORDER ITEMS
        # ============================================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER,
                product_name TEXT NOT NULL,
                taste TEXT NOT NULL,
                unit TEXT,
                quantity REAL NOT NULL,
                weight REAL,
                unit_price REAL NOT NULL,
                subtotal REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
            )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT,
            updated_at TIMESTAMP DEFAULT (datetime('now', 'localtime'))
        );
                       
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                brand_id INTEGER NOT NULL,
                quantity REAL NOT NULL DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
                FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE,
                UNIQUE(product_id, brand_id)
            );

        
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                brand_id INTEGER NOT NULL,
                movement_type TEXT NOT NULL,      -- 'in' or 'out'
                quantity REAL NOT NULL,
                reason TEXT,                       -- e.g. 'Purchase', 'Sale', 'Adjustment', 'Damaged'
                reference_order_id INTEGER,        -- links to orders.id if it's a sale-driven 'out'
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id),
                FOREIGN KEY (brand_id) REFERENCES brands(id),
                FOREIGN KEY (reference_order_id) REFERENCES orders(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            );
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS brands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                telegram TEXT,
                facebook TEXT,
                address TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_transfers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                from_brand_id INTEGER NOT NULL,
                to_brand_id INTEGER NOT NULL,
                quantity REAL NOT NULL,
                note TEXT,
                transferred_by INTEGER,
                transferred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id),
                FOREIGN KEY (from_brand_id) REFERENCES brands(id),
                FOREIGN KEY (to_brand_id) REFERENCES brands(id),
                FOREIGN KEY (transferred_by) REFERENCES users(id)
            )
        ''')
        # Insert demo data
        self._insert_demo_data(cursor)
        conn.commit()
        conn.close()

    def _insert_demo_data(self, cursor):
        # Users
        cursor.execute("SELECT COUNT(*) as count FROM users")
        if cursor.fetchone()['count'] == 0:
            cursor.execute("INSERT INTO users (username, password, role, name) VALUES ('admin', 'admin123', 'Owner', 'Administrator')")

        # Categories
        cursor.execute("SELECT COUNT(*) as count FROM categories")
        if cursor.fetchone()['count'] == 0:
            categories = ["ជ្រូក", "មាន់", "ទា", "គោ"]
            for cat in categories:
                cursor.execute("INSERT INTO categories (name) VALUES (?)", (cat,))

        cursor.execute("SELECT COUNT(*) as count FROM units")
        if cursor.fetchone()['count'] == 0:
            units = ["គឺឡូក្រាម", "ក្បាល"]
            for unit in units:
                cursor.execute("INSERT INTO units (name) VALUES (?)", (unit,))

        cursor.execute("SELECT COUNT(*) as count FROM taste")
        if cursor.fetchone()['count']==0:
            tastes = ['អំបិលម្ទេស','ទឹកឃ្មុំខ្ទឹមស','ទឹកស៊ីអ៊ីវ ល្ង']
            for taste in tastes:
                cursor.execute("INSERT INTO taste (name) VALUES (?)", (taste,))

        
    

     



    