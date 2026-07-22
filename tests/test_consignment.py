import pytest

from src.core.db import get_connection, init_db
from src.inventory.items import create_item
from src.inventory.stock import current_stock, record_transaction
from src.inventory.variants import create_variant
from src.sales.consignment import (
    ShipmentAlreadyConfirmedError,
    ShipmentNotFoundError,
    confirm_sale,
    create_shipment,
    get_shipment,
    list_shipments,
)
from src.settlement.channels import create_channel


def _conn_with_stock(tmp_path, quantity=20):
    conn = get_connection(str(tmp_path / "farm.db"))
    init_db(conn)
    item_id = create_item(conn, "상추", "kg")
    if quantity > 0:
        record_transaction(conn, item_id, "harvest", quantity)
    channel_id = create_channel(conn, "모현점", "consignment", commission_rate=10)
    return conn, item_id, channel_id


def test_create_shipment_reduces_stock_and_starts_waiting(tmp_path):
    conn, item_id, channel_id = _conn_with_stock(tmp_path, 20)

    shipment_id = create_shipment(conn, item_id, channel_id, 8)

    shipment = get_shipment(conn, shipment_id)
    stock = current_stock(conn, item_id)
    conn.close()

    assert shipment["status"] == "판매대기"
    assert shipment["shipped_quantity"] == 8
    assert stock == 12  # 재고는 출고 시점에 바로 차감


def test_create_shipment_does_not_create_sale_yet(tmp_path):
    conn, item_id, channel_id = _conn_with_stock(tmp_path, 20)
    create_shipment(conn, item_id, channel_id, 8)

    sales_count = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    conn.close()

    assert sales_count == 0


def test_confirm_sale_creates_sale_without_double_deducting_stock(tmp_path):
    conn, item_id, channel_id = _conn_with_stock(tmp_path, 20)
    shipment_id = create_shipment(conn, item_id, channel_id, 8)

    sale_id = confirm_sale(conn, shipment_id, sold_quantity=6, unit_price=3000)

    row = conn.execute(
        "SELECT buyer, quantity, unit_price, total_amount, channel_id FROM sales WHERE id = ?",
        (sale_id,),
    ).fetchone()
    stock = current_stock(conn, item_id)
    shipment = get_shipment(conn, shipment_id)
    conn.close()

    assert row == ("모현점", 6, 3000, 18000, channel_id)
    assert stock == 12  # 확정 시 재고가 추가로 또 빠지면 안 됨(출고 시 이미 차감)
    assert shipment["status"] == "판매완료"
    assert shipment["sold_quantity"] == 6
    assert shipment["sale_id"] == sale_id


def test_confirm_sale_allows_partial_quantity_with_no_extra_handling(tmp_path):
    """출고량 전체가 안 팔려도 판매 수량만 입력받고 나머지는 그냥 기록에만 남는다."""
    conn, item_id, channel_id = _conn_with_stock(tmp_path, 20)
    shipment_id = create_shipment(conn, item_id, channel_id, 10)

    confirm_sale(conn, shipment_id, sold_quantity=7, unit_price=3000)

    shipment = get_shipment(conn, shipment_id)
    conn.close()

    assert shipment["shipped_quantity"] == 10
    assert shipment["sold_quantity"] == 7


def test_confirm_sale_rejects_quantity_exceeding_shipped(tmp_path):
    conn, item_id, channel_id = _conn_with_stock(tmp_path, 20)
    shipment_id = create_shipment(conn, item_id, channel_id, 5)

    with pytest.raises(ValueError):
        confirm_sale(conn, shipment_id, sold_quantity=6, unit_price=3000)
    conn.close()


def test_confirm_sale_rejects_zero_price(tmp_path):
    conn, item_id, channel_id = _conn_with_stock(tmp_path, 20)
    shipment_id = create_shipment(conn, item_id, channel_id, 5)

    with pytest.raises(ValueError):
        confirm_sale(conn, shipment_id, sold_quantity=3, unit_price=0)
    conn.close()


def test_confirm_sale_raises_when_already_confirmed(tmp_path):
    conn, item_id, channel_id = _conn_with_stock(tmp_path, 20)
    shipment_id = create_shipment(conn, item_id, channel_id, 5)
    confirm_sale(conn, shipment_id, sold_quantity=3, unit_price=3000)

    with pytest.raises(ShipmentAlreadyConfirmedError):
        confirm_sale(conn, shipment_id, sold_quantity=1, unit_price=3000)
    conn.close()


def test_confirm_sale_raises_when_shipment_not_found(tmp_path):
    conn, item_id, channel_id = _conn_with_stock(tmp_path, 20)

    with pytest.raises(ShipmentNotFoundError):
        confirm_sale(conn, 999, sold_quantity=1, unit_price=3000)
    conn.close()


def test_list_shipments_filters_by_status(tmp_path):
    conn, item_id, channel_id = _conn_with_stock(tmp_path, 20)
    waiting_id = create_shipment(conn, item_id, channel_id, 5)
    confirmed_id = create_shipment(conn, item_id, channel_id, 3)
    confirm_sale(conn, confirmed_id, sold_quantity=3, unit_price=3000)

    waiting = list_shipments(conn, status="판매대기")
    confirmed = list_shipments(conn, status="판매완료")
    conn.close()

    assert [s["id"] for s in waiting] == [waiting_id]
    assert [s["id"] for s in confirmed] == [confirmed_id]


def test_create_shipment_stores_variant_id(tmp_path):
    conn, item_id, channel_id = _conn_with_stock(tmp_path, 0)
    variant_id = create_variant(conn, item_id, size="특", weight="1kg", default_price=15000)
    record_transaction(conn, item_id, "harvest", 10, variant_id=variant_id)

    shipment_id = create_shipment(conn, item_id, channel_id, 4, variant_id=variant_id)

    shipment = get_shipment(conn, shipment_id)
    variant_stock = current_stock(conn, item_id, variant_id=variant_id)
    conn.close()

    assert shipment["variant_id"] == variant_id
    assert variant_stock == 6
