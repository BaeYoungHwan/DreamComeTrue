"""기간별 정산 리포트 집계 및 엑셀(.xlsx) Export."""
import io
import sqlite3
from typing import Any

from openpyxl import Workbook


def period_report(
    conn: sqlite3.Connection, start_date: str, end_date: str
) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT items.name,
               SUM(sales.quantity) AS total_quantity,
               SUM(sales.total_amount) AS total_amount
        FROM sales
        JOIN items ON items.id = sales.item_id
        WHERE date(sales.sold_at) BETWEEN date(?) AND date(?)
        GROUP BY items.name
        ORDER BY items.name
        """,
        (start_date, end_date),
    ).fetchall()
    return [
        {"item_name": r[0], "total_quantity": r[1], "total_amount": r[2]}
        for r in rows
    ]


def report_to_excel_bytes(rows: list[dict[str, Any]]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "정산리포트"
    ws.append(["품목", "출하량", "판매대금"])
    for row in rows:
        ws.append([row["item_name"], row["total_quantity"], row["total_amount"]])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def export_all_data_to_excel_bytes(conn: sqlite3.Connection) -> bytes:
    wb = Workbook()

    ws_items = wb.active
    ws_items.title = "품목"
    ws_items.append(["id", "이름", "규격", "커스텀속성", "등록일"])
    for row in conn.execute(
        "SELECT id, name, unit, custom_attributes, created_at FROM items"
    ):
        ws_items.append(list(row))

    ws_tx = wb.create_sheet("입출고내역")
    ws_tx.append(["id", "품목ID", "거래유형", "수량", "일시"])
    for row in conn.execute(
        "SELECT id, item_id, type, quantity, created_at FROM stock_transactions"
    ):
        ws_tx.append(list(row))

    ws_sales = wb.create_sheet("판매내역")
    ws_sales.append(["id", "품목ID", "출하처", "수량", "단가", "판매대금", "판매일시"])
    for row in conn.execute(
        "SELECT id, item_id, buyer, quantity, unit_price, total_amount, sold_at FROM sales"
    ):
        ws_sales.append(list(row))

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
