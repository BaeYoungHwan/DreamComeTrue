"""스키마 마이그레이션 — PRAGMA user_version 기반 순차 실행 (멱등)."""
import sqlite3
from typing import Callable


def current_schema_version(conn: sqlite3.Connection) -> int:
    return conn.execute("PRAGMA user_version").fetchone()[0]


def _set_schema_version(conn: sqlite3.Connection, version: int) -> None:
    conn.execute(f"PRAGMA user_version = {version}")


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row[1] == column for row in rows)


def _backfill_channels_from_buyer(conn: sqlite3.Connection) -> None:
    buyers = [
        row[0]
        for row in conn.execute(
            "SELECT DISTINCT buyer FROM sales WHERE channel_id IS NULL"
        ).fetchall()
    ]
    for buyer in buyers:
        existing = conn.execute(
            "SELECT id FROM channels WHERE name = ?", (buyer,)
        ).fetchone()
        channel_id = (
            existing[0]
            if existing
            else conn.execute(
                "INSERT INTO channels (name, channel_type, commission_rate) "
                "VALUES (?, 'consignment', 0)",
                (buyer,),
            ).lastrowid
        )
        conn.execute(
            "UPDATE sales SET channel_id = ? WHERE buyer = ? AND channel_id IS NULL",
            (channel_id, buyer),
        )


def _migration_001_channels(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            channel_type TEXT NOT NULL CHECK (channel_type IN ('consignment', 'direct')),
            commission_rate REAL NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
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
        """
    )
    if not _column_exists(conn, "sales", "channel_id"):
        conn.execute(
            "ALTER TABLE sales ADD COLUMN channel_id INTEGER REFERENCES channels(id)"
        )
    _backfill_channels_from_buyer(conn)


def _migration_002_item_variants(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS item_variants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL REFERENCES items(id),
            size TEXT,
            weight TEXT,
            default_price REAL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )
    if not _column_exists(conn, "stock_transactions", "variant_id"):
        conn.execute(
            "ALTER TABLE stock_transactions ADD COLUMN variant_id INTEGER REFERENCES item_variants(id)"
        )
    if not _column_exists(conn, "sales", "variant_id"):
        conn.execute(
            "ALTER TABLE sales ADD COLUMN variant_id INTEGER REFERENCES item_variants(id)"
        )


def _migration_003_orders(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            variant_id INTEGER NOT NULL REFERENCES item_variants(id),
            customer_name TEXT NOT NULL,
            quantity REAL NOT NULL CHECK (quantity > 0),
            deposit_confirmed_at TEXT,
            status TEXT NOT NULL DEFAULT '출고대기' CHECK (status IN ('출고대기', '출고완료')),
            shipped_stock_transaction_id INTEGER REFERENCES stock_transactions(id),
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )


def _migration_004_orders_shipping_fee(conn: sqlite3.Connection) -> None:
    if not _column_exists(conn, "orders", "shipping_fee"):
        conn.execute(
            "ALTER TABLE orders ADD COLUMN shipping_fee REAL NOT NULL DEFAULT 0"
        )


def _migration_005_consignment_shipments(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
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
    )


MIGRATIONS: list[tuple[int, Callable[[sqlite3.Connection], None]]] = [
    (1, _migration_001_channels),
    (2, _migration_002_item_variants),
    (3, _migration_003_orders),
    (4, _migration_004_orders_shipping_fee),
    (5, _migration_005_consignment_shipments),
]


def run_migrations(conn: sqlite3.Connection) -> None:
    version = current_schema_version(conn)
    for target_version, migration in MIGRATIONS:
        if target_version > version:
            migration(conn)
            _set_schema_version(conn, target_version)
    conn.commit()
