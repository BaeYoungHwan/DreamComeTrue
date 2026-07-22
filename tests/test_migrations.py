import sqlite3

from src.core.db import get_connection, init_db
from src.core.migrations import current_schema_version, run_migrations

# Phase 2 이전(레거시) 스키마 — channels/settlements/sales.channel_id가 없는 상태를 재현해
# 실제 운영 DB에 마이그레이션을 적용하는 시나리오를 검증한다.
LEGACY_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    unit TEXT NOT NULL,
    custom_attributes TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS stock_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL REFERENCES items(id),
    type TEXT NOT NULL CHECK (type IN ('harvest', 'shipment', 'loss')),
    quantity REAL NOT NULL CHECK (quantity > 0),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL REFERENCES items(id),
    stock_transaction_id INTEGER REFERENCES stock_transactions(id),
    buyer TEXT NOT NULL,
    quantity REAL NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL CHECK (unit_price >= 0),
    total_amount REAL NOT NULL CHECK (total_amount >= 0),
    sold_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def _legacy_conn_with_sales(tmp_path, buyer_quantities: list[tuple[str, float, float]]):
    """buyer_quantities: [(buyer, quantity, unit_price), ...]"""
    conn = get_connection(str(tmp_path / "farm.db"))
    conn.executescript(LEGACY_SCHEMA_SQL)
    conn.commit()
    item_id = conn.execute(
        "INSERT INTO items (name, unit) VALUES ('블루베리', 'kg')"
    ).lastrowid
    for buyer, quantity, unit_price in buyer_quantities:
        conn.execute(
            "INSERT INTO sales (item_id, buyer, quantity, unit_price, total_amount) "
            "VALUES (?, ?, ?, ?, ?)",
            (item_id, buyer, quantity, unit_price, quantity * unit_price),
        )
    conn.commit()
    return conn, item_id


def test_fresh_db_starts_at_version_zero(tmp_path):
    conn = get_connection(str(tmp_path / "farm.db"))
    init_db(conn)

    version = current_schema_version(conn)
    conn.close()

    assert version == 0


def test_run_migrations_sets_version_to_latest(tmp_path):
    conn = get_connection(str(tmp_path / "farm.db"))
    init_db(conn)

    run_migrations(conn)
    version = current_schema_version(conn)
    conn.close()

    assert version == 4


def test_run_migrations_is_idempotent(tmp_path):
    conn = get_connection(str(tmp_path / "farm.db"))
    init_db(conn)

    run_migrations(conn)
    run_migrations(conn)  # 재실행해도 오류 없이 no-op
    version = current_schema_version(conn)
    conn.close()

    assert version == 4


def test_run_migrations_creates_item_variants_and_orders_tables(tmp_path):
    conn = get_connection(str(tmp_path / "farm.db"))
    init_db(conn)

    run_migrations(conn)
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    conn.close()

    assert {"item_variants", "orders"} <= tables


def test_run_migrations_adds_variant_id_to_legacy_stock_transactions_and_sales(tmp_path):
    conn, _ = _legacy_conn_with_sales(tmp_path, [("모현점", 5, 12500)])

    run_migrations(conn)
    tx_columns = {
        row[1] for row in conn.execute("PRAGMA table_info(stock_transactions)").fetchall()
    }
    sales_columns = {row[1] for row in conn.execute("PRAGMA table_info(sales)").fetchall()}
    conn.close()

    assert "variant_id" in tx_columns
    assert "variant_id" in sales_columns


def test_run_migrations_creates_channels_and_settlements_tables(tmp_path):
    conn = get_connection(str(tmp_path / "farm.db"))
    init_db(conn)

    run_migrations(conn)
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    conn.close()

    assert {"channels", "settlements"} <= tables


def test_run_migrations_adds_channel_id_to_legacy_sales_table(tmp_path):
    conn, _ = _legacy_conn_with_sales(tmp_path, [("모현점", 5, 12500)])

    run_migrations(conn)
    columns = {row[1] for row in conn.execute("PRAGMA table_info(sales)").fetchall()}
    conn.close()

    assert "channel_id" in columns


def test_backfill_creates_channel_per_distinct_buyer(tmp_path):
    conn, _ = _legacy_conn_with_sales(
        tmp_path,
        [("모현점", 5, 12500), ("어양점", 3, 6000), ("모현점", 2, 12500)],
    )

    run_migrations(conn)
    channels = conn.execute("SELECT name, channel_type, commission_rate FROM channels").fetchall()
    conn.close()

    assert sorted(channels) == [
        ("모현점", "consignment", 0),
        ("어양점", "consignment", 0),
    ]


def test_backfill_links_existing_sales_to_new_channel(tmp_path):
    conn, item_id = _legacy_conn_with_sales(tmp_path, [("모현점", 5, 12500)])

    run_migrations(conn)
    row = conn.execute(
        "SELECT c.name FROM sales s JOIN channels c ON s.channel_id = c.id WHERE s.item_id = ?",
        (item_id,),
    ).fetchone()
    conn.close()

    assert row[0] == "모현점"


def test_run_migrations_on_already_migrated_db_does_not_duplicate_channels(tmp_path):
    conn, _ = _legacy_conn_with_sales(tmp_path, [("모현점", 5, 12500)])

    run_migrations(conn)
    run_migrations(conn)
    count = conn.execute("SELECT COUNT(*) FROM channels WHERE name = '모현점'").fetchone()[0]
    conn.close()

    assert count == 1


def test_run_migrations_adds_shipping_fee_to_orders_table(tmp_path):
    conn = get_connection(str(tmp_path / "farm.db"))
    init_db(conn)

    run_migrations(conn)
    run_migrations(conn)  # 재실행해도 오류 없이 no-op
    columns = {row[1] for row in conn.execute("PRAGMA table_info(orders)").fetchall()}
    conn.close()

    assert "shipping_fee" in columns
