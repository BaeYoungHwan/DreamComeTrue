import pytest

from src.core.db import get_connection, init_db
from src.inventory.items import create_item
from src.inventory.stock import (
    InsufficientStockError,
    current_stock,
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
