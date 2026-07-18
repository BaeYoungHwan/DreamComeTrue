import pytest

from src.core.db import get_connection, init_db
from src.inventory.items import create_item
from src.inventory.stock import current_stock, record_transaction
from src.inventory.variants import create_variant
from src.orders.orders import (
    OrderAlreadyShippedError,
    OrderNotFoundError,
    create_order,
    get_order,
    list_orders,
    ship_order,
)


def _conn_with_variant(tmp_path, harvested=10):
    conn = get_connection(str(tmp_path / "farm.db"))
    init_db(conn)
    item_id = create_item(conn, "블루베리", "kg")
    variant_id = create_variant(conn, item_id, size="특", weight="1kg", default_price=15000)
    record_transaction(conn, item_id, "harvest", harvested, variant_id=variant_id)
    return conn, item_id, variant_id


def test_create_order_starts_in_waiting_status(tmp_path):
    conn, item_id, variant_id = _conn_with_variant(tmp_path)
    order_id = create_order(conn, variant_id, "홍길동", 3, deposit_confirmed_at="2026-07-18")

    order = get_order(conn, order_id)
    conn.close()

    assert order["status"] == "출고대기"
    assert order["customer_name"] == "홍길동"
    assert order["quantity"] == 3
    assert order["deposit_confirmed_at"] == "2026-07-18"


def test_list_orders_filters_by_status(tmp_path):
    conn, item_id, variant_id = _conn_with_variant(tmp_path)
    order_id = create_order(conn, variant_id, "홍길동", 3)
    create_order(conn, variant_id, "김철수", 2)
    ship_order(conn, order_id)

    waiting = list_orders(conn, status="출고대기")
    shipped = list_orders(conn, status="출고완료")
    conn.close()

    assert [o["customer_name"] for o in waiting] == ["김철수"]
    assert [o["customer_name"] for o in shipped] == ["홍길동"]


def test_ship_order_reduces_variant_stock_and_marks_completed(tmp_path):
    conn, item_id, variant_id = _conn_with_variant(tmp_path, harvested=10)
    order_id = create_order(conn, variant_id, "홍길동", 3)

    ship_order(conn, order_id)

    order = get_order(conn, order_id)
    stock = current_stock(conn, item_id, variant_id=variant_id)
    conn.close()

    assert order["status"] == "출고완료"
    assert order["shipped_stock_transaction_id"] is not None
    assert stock == 7


def test_ship_order_raises_when_already_shipped(tmp_path):
    conn, item_id, variant_id = _conn_with_variant(tmp_path)
    order_id = create_order(conn, variant_id, "홍길동", 3)
    ship_order(conn, order_id)

    with pytest.raises(OrderAlreadyShippedError):
        ship_order(conn, order_id)
    conn.close()


def test_ship_order_raises_when_order_not_found(tmp_path):
    conn, item_id, variant_id = _conn_with_variant(tmp_path)

    with pytest.raises(OrderNotFoundError):
        ship_order(conn, 999)
    conn.close()


def test_create_order_rejects_non_positive_quantity(tmp_path):
    conn, item_id, variant_id = _conn_with_variant(tmp_path)

    with pytest.raises(ValueError):
        create_order(conn, variant_id, "홍길동", 0)
    conn.close()
