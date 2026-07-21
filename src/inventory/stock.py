"""입고/출고/폐기 거래 기록 및 재고 계산."""
import sqlite3
from datetime import datetime

from src.inventory.items import get_item, list_items
from src.inventory.variants import list_variants

VALID_TYPES = ("harvest", "shipment", "loss")


class InsufficientStockError(Exception):
    """재고보다 많은 수량을 출고·폐기하려 할 때 발생."""


def current_stock(
    conn: sqlite3.Connection, item_id: int, variant_id: int | None = None
) -> float:
    query = """
        SELECT
            COALESCE(SUM(CASE WHEN type = 'harvest' THEN quantity ELSE 0 END), 0)
            - COALESCE(SUM(CASE WHEN type = 'shipment' THEN quantity ELSE 0 END), 0)
            - COALESCE(SUM(CASE WHEN type = 'loss' THEN quantity ELSE 0 END), 0)
        FROM stock_transactions
        WHERE item_id = ?
    """
    params: tuple = (item_id,)
    if variant_id is not None:
        query += " AND variant_id = ?"
        params = (item_id, variant_id)

    row = conn.execute(query, params).fetchone()
    return row[0] or 0


def record_transaction(
    conn: sqlite3.Connection,
    item_id: int,
    tx_type: str,
    quantity: float,
    occurred_on: str | None = None,
    variant_id: int | None = None,
) -> int:
    if tx_type not in VALID_TYPES:
        raise ValueError(f"유효하지 않은 거래유형: {tx_type}")
    if quantity <= 0:
        raise ValueError("수량은 0보다 커야 합니다")
    if get_item(conn, item_id) is None:
        raise ValueError(f"존재하지 않는 품목입니다: {item_id}")

    if tx_type in ("shipment", "loss"):
        available = current_stock(conn, item_id, variant_id=variant_id)
        if quantity > available:
            raise InsufficientStockError(
                f"재고 부족: 현재 재고 {available}, 요청 수량 {quantity}"
            )

    created_at = occurred_on or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur = conn.execute(
        "INSERT INTO stock_transactions (item_id, type, quantity, created_at, variant_id) "
        "VALUES (?, ?, ?, ?, ?)",
        (item_id, tx_type, quantity, created_at, variant_id),
    )
    conn.commit()
    return cur.lastrowid


def list_transactions(conn: sqlite3.Connection, item_id: int) -> list[dict]:
    """판매(sales)에 연결되지 않은 입출고 내역만 반환한다. 판매 연동 출고 내역은 판매 내역 쪽에서 관리한다."""
    rows = conn.execute(
        """
        SELECT id, type, quantity, created_at, variant_id
        FROM stock_transactions
        WHERE item_id = ?
          AND id NOT IN (
              SELECT stock_transaction_id FROM sales
              WHERE stock_transaction_id IS NOT NULL
          )
        ORDER BY created_at DESC, id DESC
        """,
        (item_id,),
    ).fetchall()
    return [
        {
            "id": r[0],
            "type": r[1],
            "quantity": r[2],
            "created_at": r[3],
            "variant_id": r[4],
        }
        for r in rows
    ]


def delete_transaction(conn: sqlite3.Connection, tx_id: int) -> None:
    conn.execute("DELETE FROM stock_transactions WHERE id = ?", (tx_id,))
    conn.commit()


def stock_overview(conn: sqlite3.Connection) -> list[dict]:
    """모든 품목의 현재 재고를 한눈에 볼 수 있는 목록.
    변형이 있는 품목은 변형별로, 없는 품목은 품목 전체로 한 행씩 반환한다."""
    rows = []
    for item in list_items(conn):
        variants = list_variants(conn, item["id"])
        if variants:
            for v in variants:
                rows.append(
                    {
                        "item_name": item["name"],
                        "unit": item["unit"],
                        "size": v["size"],
                        "weight": v["weight"],
                        "stock": current_stock(conn, item["id"], variant_id=v["id"]),
                    }
                )
        else:
            rows.append(
                {
                    "item_name": item["name"],
                    "unit": item["unit"],
                    "size": None,
                    "weight": None,
                    "stock": current_stock(conn, item["id"]),
                }
            )
    return rows
