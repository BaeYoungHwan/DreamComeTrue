"""SQLite 연결 및 스키마 초기화."""
import os
import sqlite3

DEFAULT_DB_PATH = os.path.join("data", "farm.db")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    unit TEXT NOT NULL,
    custom_attributes TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS item_variants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL REFERENCES items(id),
    size TEXT,
    weight TEXT,
    default_price REAL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS stock_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL REFERENCES items(id),
    variant_id INTEGER REFERENCES item_variants(id),
    type TEXT NOT NULL CHECK (type IN ('harvest', 'shipment', 'loss')),
    quantity REAL NOT NULL CHECK (quantity > 0),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    variant_id INTEGER NOT NULL REFERENCES item_variants(id),
    customer_name TEXT NOT NULL,
    quantity REAL NOT NULL CHECK (quantity > 0),
    deposit_confirmed_at TEXT,
    status TEXT NOT NULL DEFAULT '출고대기' CHECK (status IN ('출고대기', '출고완료')),
    shipped_stock_transaction_id INTEGER REFERENCES stock_transactions(id),
    shipping_fee REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    channel_type TEXT NOT NULL CHECK (channel_type IN ('consignment', 'direct')),
    commission_rate REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL REFERENCES items(id),
    stock_transaction_id INTEGER REFERENCES stock_transactions(id),
    channel_id INTEGER REFERENCES channels(id),
    variant_id INTEGER REFERENCES item_variants(id),
    buyer TEXT NOT NULL,
    quantity REAL NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL CHECK (unit_price >= 0),
    total_amount REAL NOT NULL CHECK (total_amount >= 0),
    sold_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS settlements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id INTEGER NOT NULL REFERENCES channels(id),
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,
    sales_total REAL NOT NULL,
    commission_amount REAL NOT NULL,
    expected_deposit REAL NOT NULL,
    actual_deposit REAL,
    deposit_date TEXT,
    memo TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS consignment_shipments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL REFERENCES items(id),
    variant_id INTEGER REFERENCES item_variants(id),
    channel_id INTEGER NOT NULL REFERENCES channels(id),
    stock_transaction_id INTEGER NOT NULL REFERENCES stock_transactions(id),
    shipped_quantity REAL NOT NULL CHECK (shipped_quantity > 0),
    status TEXT NOT NULL DEFAULT '판매대기' CHECK (status IN ('판매대기', '판매완료')),
    sold_quantity REAL,
    sale_id INTEGER REFERENCES sales(id),
    shipped_at TEXT NOT NULL DEFAULT (datetime('now')),
    confirmed_at TEXT
);
"""


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)
    conn.commit()
