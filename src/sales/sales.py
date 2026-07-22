"""판매(출하) 기록 — 출고 거래 + 매출 레코드 생성."""
import sqlite3

from src.inventory.stock import record_transaction


def record_sale(
    conn: sqlite3.Connection,
    item_id: int,
    buyer: str,
    quantity: float,
    unit_price: float,
    sold_on: str | None = None,
    channel_id: int | None = None,
    variant_id: int | None = None,
) -> int:
    if quantity <= 0:
        raise ValueError("수량은 0보다 커야 합니다")
    if unit_price < 0:
        raise ValueError("단가는 0 이상이어야 합니다")

    tx_id = record_transaction(
        conn, item_id, "shipment", quantity, occurred_on=sold_on, variant_id=variant_id
    )
    total_amount = round(quantity * unit_price)

    if sold_on:
        cur = conn.execute(
            """
            INSERT INTO sales (item_id, stock_transaction_id, channel_id, variant_id, buyer, quantity, unit_price, total_amount, sold_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (item_id, tx_id, channel_id, variant_id, buyer, quantity, unit_price, total_amount, sold_on),
        )
    else:
        cur = conn.execute(
            """
            INSERT INTO sales (item_id, stock_transaction_id, channel_id, variant_id, buyer, quantity, unit_price, total_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (item_id, tx_id, channel_id, variant_id, buyer, quantity, unit_price, total_amount),
        )
    conn.commit()
    return cur.lastrowid


def list_sales(conn: sqlite3.Connection, item_id: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT id, buyer, quantity, unit_price, total_amount, sold_at, channel_id, variant_id
        FROM sales
        WHERE item_id = ?
        ORDER BY sold_at DESC, id DESC
        """,
        (item_id,),
    ).fetchall()
    return [
        {
            "id": r[0],
            "buyer": r[1],
            "quantity": r[2],
            "unit_price": r[3],
            "total_amount": r[4],
            "sold_at": r[5],
            "channel_id": r[6],
            "variant_id": r[7],
        }
        for r in rows
    ]


def delete_sale(conn: sqlite3.Connection, sale_id: int) -> None:
    row = conn.execute(
        "SELECT stock_transaction_id FROM sales WHERE id = ?", (sale_id,)
    ).fetchone()
    if row is None:
        return

    tx_id = row[0]
    conn.execute("DELETE FROM sales WHERE id = ?", (sale_id,))
    if tx_id is not None:
        conn.execute("DELETE FROM stock_transactions WHERE id = ?", (tx_id,))
    conn.commit()
