from src.core.db import get_connection, init_db
from src.dashboard.dashboard import (
    item_sales_ranking,
    item_variant_matrix,
    monthly_sales_total,
    today_shipments,
)
from src.inventory.items import create_item
from src.inventory.stock import record_transaction
from src.inventory.variants import create_variant
from src.sales.sales import record_sale


def _seed(tmp_path):
    conn = get_connection(str(tmp_path / "farm.db"))
    init_db(conn)
    lettuce = create_item(conn, "상추", "kg")
    tomato = create_item(conn, "토마토", "박스")
    record_transaction(conn, lettuce, "harvest", 20)
    record_transaction(conn, tomato, "harvest", 20)
    record_sale(conn, lettuce, "로컬푸드 매장", 5, 2000)
    record_sale(conn, tomato, "직거래", 3, 5000)
    return conn


def test_today_shipments_returns_items_shipped_today(tmp_path):
    conn = _seed(tmp_path)
    today = conn.execute("SELECT date('now')").fetchone()[0]

    result = today_shipments(conn, today)
    conn.close()

    names = {row["item_name"] for row in result}
    assert names == {"상추", "토마토"}


def test_monthly_sales_total_sums_current_month(tmp_path):
    conn = _seed(tmp_path)
    year_month = conn.execute("SELECT strftime('%Y-%m', 'now')").fetchone()[0]

    total = monthly_sales_total(conn, year_month)
    conn.close()

    assert total == 5 * 2000 + 3 * 5000


def test_item_sales_ranking_orders_by_total_amount_desc(tmp_path):
    conn = _seed(tmp_path)
    year_month = conn.execute("SELECT strftime('%Y-%m', 'now')").fetchone()[0]

    ranking = item_sales_ranking(conn, year_month)
    conn.close()

    assert [row["item_name"] for row in ranking] == ["토마토", "상추"]


def test_item_variant_matrix_groups_by_item_and_variant(tmp_path):
    conn = get_connection(str(tmp_path / "farm.db"))
    init_db(conn)
    blueberry = create_item(conn, "블루베리", "kg")
    variant_a = create_variant(conn, blueberry, size="특", weight="1kg")
    variant_b = create_variant(conn, blueberry, size="특", weight="500g")
    record_transaction(conn, blueberry, "harvest", 10, variant_id=variant_a)
    record_transaction(conn, blueberry, "harvest", 10, variant_id=variant_b)
    record_sale(conn, blueberry, "직거래", 3, 15000, variant_id=variant_a)
    record_sale(conn, blueberry, "직거래", 2, 8000, variant_id=variant_b)
    year_month = conn.execute("SELECT strftime('%Y-%m', 'now')").fetchone()[0]

    matrix = item_variant_matrix(conn, year_month)
    conn.close()

    assert {
        (row["item_name"], row["size"], row["weight"], row["total_quantity"], row["total_amount"])
        for row in matrix
    } == {
        ("블루베리", "특", "1kg", 3, 45000),
        ("블루베리", "특", "500g", 2, 16000),
    }
