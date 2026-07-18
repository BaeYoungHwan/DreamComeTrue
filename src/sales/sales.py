"""판매(출하) 기록 — 출고 거래 + 매출 레코드 생성."""
import sqlite3

from src.inventory.stock import record_transaction


def record_sale(
    conn: sqlite3.Connection,
    item_id: int,
    buyer: str,
    quantity: float,
    unit_price: float,
) -> int:
    if quantity <= 0:
        raise ValueError("수량은 0보다 커야 합니다")
    if unit_price < 0:
        raise ValueError("단가는 0 이상이어야 합니다")

    tx_id = record_transaction(conn, item_id, "shipment", quantity)
    total_amount = quantity * unit_price

    cur = conn.execute(
        """
        INSERT INTO sales (item_id, stock_transaction_id, buyer, quantity, unit_price, total_amount)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (item_id, tx_id, buyer, quantity, unit_price, total_amount),
    )
    conn.commit()
    return cur.lastrowid
