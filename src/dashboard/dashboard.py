"""오늘 출하 현황 / 이달 누적 매출 / 품목별 판매 순위 집계."""
import sqlite3


def today_shipments(conn: sqlite3.Connection, today_str: str) -> list[dict]:
    rows = conn.execute(
        """
        SELECT items.name, SUM(stock_transactions.quantity)
        FROM stock_transactions
        JOIN items ON items.id = stock_transactions.item_id
        WHERE stock_transactions.type = 'shipment'
          AND date(stock_transactions.created_at) = date(?)
        GROUP BY items.name
        ORDER BY items.name
        """,
        (today_str,),
    ).fetchall()
    return [{"item_name": r[0], "quantity": r[1]} for r in rows]


def monthly_sales_total(conn: sqlite3.Connection, year_month: str) -> float:
    row = conn.execute(
        "SELECT COALESCE(SUM(total_amount), 0) FROM sales WHERE strftime('%Y-%m', sold_at) = ?",
        (year_month,),
    ).fetchone()
    return row[0]


def item_sales_ranking(conn: sqlite3.Connection, year_month: str) -> list[dict]:
    rows = conn.execute(
        """
        SELECT items.name, SUM(sales.total_amount) AS total
        FROM sales
        JOIN items ON items.id = sales.item_id
        WHERE strftime('%Y-%m', sales.sold_at) = ?
        GROUP BY items.name
        ORDER BY total DESC
        """,
        (year_month,),
    ).fetchall()
    return [{"item_name": r[0], "total_amount": r[1]} for r in rows]
