import pytest

from src.core.db import get_connection, init_db
from src.inventory.items import create_item
from src.inventory.stock import InsufficientStockError, current_stock, record_transaction
from src.sales.sales import delete_sale, list_sales, record_sale


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


def test_record_sale_stores_given_date(tmp_path):
    conn, item_id = _conn_with_stock(tmp_path, 10)

    sale_id = record_sale(
        conn, item_id, "로컬푸드 매장", 3, 2000, sold_on="2026-07-01"
    )

    row = conn.execute(
        "SELECT sold_at FROM sales WHERE id = ?", (sale_id,)
    ).fetchone()
    tx_row = conn.execute(
        "SELECT created_at FROM stock_transactions WHERE item_id = ? AND type = 'shipment'",
        (item_id,),
    ).fetchone()
    conn.close()

    assert row[0] == "2026-07-01"
    assert tx_row[0] == "2026-07-01"


def test_list_sales_returns_records_for_item(tmp_path):
    conn, item_id = _conn_with_stock(tmp_path, 10)
    record_sale(conn, item_id, "로컬푸드 매장", 3, 2000)

    sales = list_sales(conn, item_id)
    conn.close()

    assert len(sales) == 1
    assert sales[0]["buyer"] == "로컬푸드 매장"
    assert sales[0]["total_amount"] == 6000


def _create_channel(conn, name="모현점"):
    return conn.execute(
        "INSERT INTO channels (name, channel_type, commission_rate) VALUES (?, 'consignment', 10)",
        (name,),
    ).lastrowid


def test_record_sale_stores_channel_id(tmp_path):
    conn, item_id = _conn_with_stock(tmp_path, 10)
    channel_id = _create_channel(conn)

    sale_id = record_sale(conn, item_id, "모현점", 3, 12500, channel_id=channel_id)

    row = conn.execute(
        "SELECT channel_id FROM sales WHERE id = ?", (sale_id,)
    ).fetchone()
    conn.close()

    assert row[0] == channel_id


def test_record_sale_without_channel_id_leaves_it_null(tmp_path):
    conn, item_id = _conn_with_stock(tmp_path, 10)

    sale_id = record_sale(conn, item_id, "직거래 고객", 3, 12500)

    row = conn.execute(
        "SELECT channel_id FROM sales WHERE id = ?", (sale_id,)
    ).fetchone()
    conn.close()

    assert row[0] is None


def test_list_sales_includes_channel_id(tmp_path):
    conn, item_id = _conn_with_stock(tmp_path, 10)
    channel_id = _create_channel(conn)
    record_sale(conn, item_id, "모현점", 3, 12500, channel_id=channel_id)

    sales = list_sales(conn, item_id)
    conn.close()

    assert sales[0]["channel_id"] == channel_id


def test_delete_sale_removes_sale_and_linked_transaction(tmp_path):
    conn, item_id = _conn_with_stock(tmp_path, 10)
    sale_id = record_sale(conn, item_id, "로컬푸드 매장", 3, 2000)

    delete_sale(conn, sale_id)

    stock = current_stock(conn, item_id)
    sales = list_sales(conn, item_id)
    tx_count = conn.execute(
        "SELECT COUNT(*) FROM stock_transactions WHERE item_id = ? AND type = 'shipment'",
        (item_id,),
    ).fetchone()[0]
    conn.close()

    assert stock == 10
    assert sales == []
    assert tx_count == 0


def test_record_sale_stores_variant_id_and_reduces_variant_stock(tmp_path):
    from src.inventory.variants import create_variant

    conn = get_connection(str(tmp_path / "farm.db"))
    init_db(conn)
    item_id = create_item(conn, "블루베리", "kg")
    variant_id = create_variant(conn, item_id, size="특", weight="1kg")
    record_transaction(conn, item_id, "harvest", 10, variant_id=variant_id)

    sale_id = record_sale(conn, item_id, "직거래", 3, 15000, variant_id=variant_id)

    row = conn.execute(
        "SELECT variant_id FROM sales WHERE id = ?", (sale_id,)
    ).fetchone()
    variant_stock = current_stock(conn, item_id, variant_id=variant_id)
    conn.close()

    assert row[0] == variant_id
    assert variant_stock == 7


def test_list_sales_includes_variant_id(tmp_path):
    from src.inventory.variants import create_variant

    conn = get_connection(str(tmp_path / "farm.db"))
    init_db(conn)
    item_id = create_item(conn, "블루베리", "kg")
    variant_id = create_variant(conn, item_id, size="특", weight="1kg")
    record_transaction(conn, item_id, "harvest", 10, variant_id=variant_id)
    record_sale(conn, item_id, "직거래", 3, 15000, variant_id=variant_id)

    sales = list_sales(conn, item_id)
    conn.close()

    assert sales[0]["variant_id"] == variant_id
