import sqlite3

import pytest

from src.core.db import get_connection, init_db


def test_init_db_creates_expected_tables(tmp_path):
    conn = get_connection(str(tmp_path / "farm.db"))
    init_db(conn)

    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    conn.close()

    assert {"items", "stock_transactions", "sales"} <= tables


def test_items_custom_attributes_defaults_to_empty_json(tmp_path):
    conn = get_connection(str(tmp_path / "farm.db"))
    init_db(conn)

    conn.execute("INSERT INTO items (name, unit) VALUES ('상추', 'kg')")
    conn.commit()
    row = conn.execute("SELECT custom_attributes FROM items").fetchone()
    conn.close()

    assert row[0] == "{}"


def test_stock_transactions_rejects_invalid_type(tmp_path):
    conn = get_connection(str(tmp_path / "farm.db"))
    init_db(conn)
    conn.execute("INSERT INTO items (name, unit) VALUES ('상추', 'kg')")
    conn.commit()

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO stock_transactions (item_id, type, quantity) "
            "VALUES (1, 'invalid', 1)"
        )
    conn.close()


def test_stock_transactions_rejects_non_positive_quantity(tmp_path):
    conn = get_connection(str(tmp_path / "farm.db"))
    init_db(conn)
    conn.execute("INSERT INTO items (name, unit) VALUES ('상추', 'kg')")
    conn.commit()

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO stock_transactions (item_id, type, quantity) "
            "VALUES (1, 'harvest', 0)"
        )
    conn.close()


def test_sales_rejects_negative_unit_price(tmp_path):
    conn = get_connection(str(tmp_path / "farm.db"))
    init_db(conn)
    conn.execute("INSERT INTO items (name, unit) VALUES ('상추', 'kg')")
    conn.commit()

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO sales (item_id, buyer, quantity, unit_price, total_amount) "
            "VALUES (1, '로컬푸드 매장', 1, -100, 0)"
        )
    conn.close()
