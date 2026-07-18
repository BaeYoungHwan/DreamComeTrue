import pytest

from src.core.db import get_connection, init_db
from src.inventory.items import create_item
from src.inventory.stock import (
    InsufficientStockError,
    current_stock,
    delete_transaction,
    list_transactions,
    record_transaction,
)


def _conn_with_item(tmp_path, name="상추", unit="kg"):
    conn = get_connection(str(tmp_path / "farm.db"))
    init_db(conn)
    item_id = create_item(conn, name, unit)
    return conn, item_id


def test_harvest_increases_stock(tmp_path):
    conn, item_id = _conn_with_item(tmp_path)
    record_transaction(conn, item_id, "harvest", 10)

    stock = current_stock(conn, item_id)
    conn.close()

    assert stock == 10


def test_shipment_decreases_stock(tmp_path):
    conn, item_id = _conn_with_item(tmp_path)
    record_transaction(conn, item_id, "harvest", 10)
    record_transaction(conn, item_id, "shipment", 4)

    stock = current_stock(conn, item_id)
    conn.close()

    assert stock == 6


def test_loss_decreases_stock(tmp_path):
    conn, item_id = _conn_with_item(tmp_path)
    record_transaction(conn, item_id, "harvest", 10)
    record_transaction(conn, item_id, "loss", 2)

    stock = current_stock(conn, item_id)
    conn.close()

    assert stock == 8


def test_shipment_rejects_when_exceeds_available_stock(tmp_path):
    conn, item_id = _conn_with_item(tmp_path)
    record_transaction(conn, item_id, "harvest", 5)

    with pytest.raises(InsufficientStockError):
        record_transaction(conn, item_id, "shipment", 6)
    conn.close()


def test_record_transaction_rejects_invalid_type(tmp_path):
    conn, item_id = _conn_with_item(tmp_path)

    with pytest.raises(ValueError):
        record_transaction(conn, item_id, "invalid", 1)
    conn.close()


def test_record_transaction_rejects_nonexistent_item(tmp_path):
    conn = get_connection(str(tmp_path / "farm.db"))
    init_db(conn)

    with pytest.raises(ValueError):
        record_transaction(conn, 999, "harvest", 1)
    conn.close()


def test_record_transaction_stores_given_date(tmp_path):
    conn, item_id = _conn_with_item(tmp_path)
    record_transaction(conn, item_id, "harvest", 10, occurred_on="2026-07-01")

    row = conn.execute(
        "SELECT created_at FROM stock_transactions WHERE item_id = ?", (item_id,)
    ).fetchone()
    conn.close()

    assert row[0] == "2026-07-01"


def test_list_transactions_excludes_sale_linked_shipments(tmp_path):
    conn, item_id = _conn_with_item(tmp_path)
    record_transaction(conn, item_id, "harvest", 10)
    record_transaction(conn, item_id, "loss", 1)
    conn.execute(
        "INSERT INTO stock_transactions (item_id, type, quantity) VALUES (?, 'shipment', 2)",
        (item_id,),
    )
    sale_tx_id = conn.execute(
        "SELECT id FROM stock_transactions WHERE type = 'shipment'"
    ).fetchone()[0]
    conn.execute(
        "INSERT INTO sales (item_id, stock_transaction_id, buyer, quantity, unit_price, total_amount) "
        "VALUES (?, ?, '직거래', 2, 1000, 2000)",
        (item_id, sale_tx_id),
    )
    conn.commit()

    transactions = list_transactions(conn, item_id)
    conn.close()

    types = sorted(t["type"] for t in transactions)
    assert types == ["harvest", "loss"]


def test_delete_transaction_removes_row_and_restores_stock(tmp_path):
    conn, item_id = _conn_with_item(tmp_path)
    record_transaction(conn, item_id, "harvest", 10)
    tx_id = record_transaction(conn, item_id, "loss", 3)

    delete_transaction(conn, tx_id)
    stock = current_stock(conn, item_id)
    conn.close()

    assert stock == 10


def test_current_stock_tracks_variants_independently(tmp_path):
    from src.core.migrations import run_migrations
    from src.inventory.variants import create_variant

    conn, item_id = _conn_with_item(tmp_path)
    run_migrations(conn)
    variant_a = create_variant(conn, item_id, size="특", weight="1kg")
    variant_b = create_variant(conn, item_id, size="특", weight="500g")

    record_transaction(conn, item_id, "harvest", 10, variant_id=variant_a)
    record_transaction(conn, item_id, "harvest", 5, variant_id=variant_b)
    record_transaction(conn, item_id, "shipment", 4, variant_id=variant_a)

    stock_a = current_stock(conn, item_id, variant_id=variant_a)
    stock_b = current_stock(conn, item_id, variant_id=variant_b)
    stock_total = current_stock(conn, item_id)
    conn.close()

    assert stock_a == 6
    assert stock_b == 5
    assert stock_total == 11


def test_shipment_rejects_when_variant_stock_insufficient(tmp_path):
    from src.core.migrations import run_migrations
    from src.inventory.variants import create_variant

    conn, item_id = _conn_with_item(tmp_path)
    run_migrations(conn)
    variant_id = create_variant(conn, item_id, size="특", weight="1kg")
    record_transaction(conn, item_id, "harvest", 3, variant_id=variant_id)

    with pytest.raises(InsufficientStockError):
        record_transaction(conn, item_id, "shipment", 4, variant_id=variant_id)
    conn.close()
