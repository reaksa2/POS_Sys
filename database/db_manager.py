import sqlite3
import sys
from pathlib import Path
from datetime import datetime

from utils.auth import hash_password, is_hashed


def _app_base_dir():
    """Folder that holds database/pos.db.

    Previously the path was relative to the *current working directory*, so
    starting POS.exe from a shortcut / taskbar pin with a different "Start in"
    folder silently created a brand-new empty database somewhere else.
    Now it is always next to POS.exe (or the project root when run from source).
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


class DatabaseManager:
    _initialized_paths = set()   # run schema creation/migrations once per process

    def __init__(self):
        self.db_path = _app_base_dir() / "database" / "pos.db"
        legacy_path = Path.cwd() / "database" / "pos.db"
        if not self.db_path.exists() and legacy_path.exists():
            self.db_path = legacy_path   # keep using an existing DB from the old location
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        if str(self.db_path) not in DatabaseManager._initialized_paths:
            self.init_db()
            DatabaseManager._initialized_paths.add(str(self.db_path))

    def get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=10)
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
                updated_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
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
                created_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
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
                created_at TIMESTAMP DEFAULT (datetime('now', 'localtime'))
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
                transferred_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY (product_id) REFERENCES products(id),
                FOREIGN KEY (from_brand_id) REFERENCES brands(id),
                FOREIGN KEY (to_brand_id) REFERENCES brands(id),
                FOREIGN KEY (transferred_by) REFERENCES users(id)
            )
        ''')
        # Insert demo data
        self._insert_demo_data(cursor)
        self._migrate_plaintext_passwords(cursor)
        self._migrate_utc_timestamps(cursor)
        conn.commit()
        conn.close()

    def _migrate_utc_timestamps(self, cursor):
        """One-time fix: older versions stored stock/brand timestamps in UTC
        (CURRENT_TIMESTAMP) while orders used local time. Convert the old rows
        to local time so history filters ("today", "this week") line up."""
        flag = "migration_local_time_v1"
        cursor.execute("SELECT 1 FROM settings WHERE key = ?", (flag,))
        if cursor.fetchone():
            return
        for table, col in (("stock_movements", "created_at"), ("stock_transfers", "transferred_at"),
                           ("stock", "updated_at"), ("brands", "created_at")):
            cursor.execute(f"UPDATE {table} SET {col} = datetime({col}, 'localtime') WHERE {col} IS NOT NULL")
        cursor.execute("INSERT INTO settings (key, value) VALUES (?, '1')", (flag,))

    def _migrate_plaintext_passwords(self, cursor):
        """Upgrade any plain-text passwords to salted hashes (one-time, automatic)."""
        cursor.execute("SELECT id, password FROM users")
        for row in cursor.fetchall():
            pwd = row['password']
            if pwd and not is_hashed(pwd):
                cursor.execute("UPDATE users SET password = ? WHERE id = ?", (hash_password(pwd), row['id']))

    def _insert_demo_data(self, cursor):
        # Users
        cursor.execute("SELECT COUNT(*) as count FROM users")
        if cursor.fetchone()['count'] == 0:
            cursor.execute(
                "INSERT INTO users (username, password, role, name) VALUES ('admin', ?, 'Owner', 'Administrator')",
                (hash_password('admin123'),)
            )

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

        
    

     



    