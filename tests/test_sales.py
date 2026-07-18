import pytest

from src.core.db import get_connection, init_db
from src.inventory.items import create_item
from src.inventory.stock import InsufficientStockError, current_stock, record_transaction
from src.sales.sales import record_sale


def _conn_with_stock(tmp_path, quantity=10):
    conn = get_connection(str(tmp_path / "farm.db"))
    init_db(conn)
    item_id = create_item(conn, "상추", "kg")
    record_transaction(conn, item_id, "harvest", quantity)
    return conn, item_id


def test_record_sale_creates_shipment_and_reduces_stock(tmp_path):
    conn, item_id = _conn_with_stock(tmp_path, 10)

    record_sale(conn, item_id, "로컬푸드 매장", 3, 2000)

    stock = current_stock(conn, item_id)
    conn.close()

    assert stock == 7


def test_record_sale_computes_total_amount(tmp_path):
    conn, item_id = _conn_with_stock(tmp_path, 10)

    sale_id = record_sale(conn, item_id, "로컬푸드 매장", 3, 2000)

    row = conn.execute(
        "SELECT buyer, quantity, unit_price, total_amount FROM sales WHERE id = ?",
        (sale_id,),
    ).fetchone()
    conn.close()

    assert row == ("로컬푸드 매장", 3, 2000, 6000)


def test_record_sale_rejects_when_stock_insufficient(tmp_path):
    conn, item_id = _conn_with_stock(tmp_path, 2)

    with pytest.raises(InsufficientStockError):
        record_sale(conn, item_id, "로컬푸드 매장", 5, 1000)
    conn.close()
