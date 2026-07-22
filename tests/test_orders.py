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


def test_create_order_stores_shipping_fee(tmp_path):
    conn, item_id, variant_id = _conn_with_variant(tmp_path)
    order_id = create_order(conn, variant_id, "홍길동", 3, shipping_fee=4000)

    order = get_order(conn, order_id)
    conn.close()

    assert order["shipping_fee"] == 4000


def test_ship_order_creates_sales_row_with_variant_default_price(tmp_path):
    conn, item_id, variant_id = _conn_with_variant(tmp_path, harvested=10)
    order_id = create_order(conn, variant_id, "홍길동", 3)

    ship_order(conn, order_id, occurred_on="2026-07-20")

    row = conn.execute(
        "SELECT buyer, channel_id, variant_id, quantity, unit_price, total_amount, sold_at "
        "FROM sales WHERE item_id = ?",
        (item_id,),
    ).fetchone()
    conn.close()

    assert row == ("홍길동", None, variant_id, 3, 15000, 45000, "2026-07-20")


def test_ship_order_does_not_double_deduct_stock(tmp_path):
    """ship_order가 record_transaction과 sales 기록을 모두 수행해도 재고는 1회만 차감돼야 한다."""
    conn, item_id, variant_id = _conn_with_variant(tmp_path, harvested=10)
    order_id = create_order(conn, variant_id, "홍길동", 3)

    ship_order(conn, order_id)

    tx_count = conn.execute(
        "SELECT COUNT(*) FROM stock_transactions WHERE item_id = ? AND type = 'shipment'",
        (item_id,),
    ).fetchone()[0]
    stock = current_stock(conn, item_id, variant_id=variant_id)
    conn.close()

    assert tx_count == 1
    assert stock == 7


def test_ship_order_shipping_fee_not_included_in_sale_total_amount(tmp_path):
    conn, item_id, variant_id = _conn_with_variant(tmp_path, harvested=10)
    order_id = create_order(conn, variant_id, "홍길동", 3, shipping_fee=5000)

    ship_order(conn, order_id)

    total_amount = conn.execute(
        "SELECT total_amount FROM sales WHERE item_id = ?", (item_id,)
    ).fetchone()[0]
    conn.close()

    assert total_amount == 45000  # 3 * 15000, 택배비 5000은 미포함
