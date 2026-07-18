"""입고/출고/폐기 거래 기록 및 재고 계산."""
import sqlite3

from src.inventory.items import get_item

VALID_TYPES = ("harvest", "shipment", "loss")


class InsufficientStockError(Exception):
    """재고보다 많은 수량을 출고·폐기하려 할 때 발생."""


def current_stock(conn: sqlite3.Connection, item_id: int) -> float:
    row = conn.execute(
        """
        SELECT
            COALESCE(SUM(CASE WHEN type = 'harvest' THEN quantity ELSE 0 END), 0)
            - COALESCE(SUM(CASE WHEN type = 'shipment' THEN quantity ELSE 0 END), 0)
            - COALESCE(SUM(CASE WHEN type = 'loss' THEN quantity ELSE 0 END), 0)
        FROM stock_transactions
        WHERE item_id = ?
        """,
        (item_id,),
    ).fetchone()
    return row[0] or 0


def record_transaction(
    conn: sqlite3.Connection, item_id: int, tx_type: str, quantity: float
) -> int:
    if tx_type not in VALID_TYPES:
        raise ValueError(f"유효하지 않은 거래유형: {tx_type}")
    if quantity <= 0:
        raise ValueError("수량은 0보다 커야 합니다")
    if get_item(conn, item_id) is None:
        raise ValueError(f"존재하지 않는 품목입니다: {item_id}")

    if tx_type in ("shipment", "loss"):
        available = current_stock(conn, item_id)
        if quantity > available:
            raise InsufficientStockError(
                f"재고 부족: 현재 재고 {available}, 요청 수량 {quantity}"
            )

    cur = conn.execute(
        "INSERT INTO stock_transactions (item_id, type, quantity) VALUES (?, ?, ?)",
        (item_id, tx_type, quantity),
    )
    conn.commit()
    return cur.lastrowid
