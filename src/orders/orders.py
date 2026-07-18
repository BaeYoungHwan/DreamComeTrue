"""선입금 주문출하 관리 — 입금 확인 후 출고 대기, 출고 시 재고 차감."""
import sqlite3

from src.inventory.stock import record_transaction
from src.inventory.variants import get_variant


class OrderNotFoundError(Exception):
    """존재하지 않는 주문을 조회·출고 처리하려 할 때 발생."""


class OrderAlreadyShippedError(Exception):
    """이미 출고 완료된 주문을 다시 출고 처리하려 할 때 발생."""


def create_order(
    conn: sqlite3.Connection,
    variant_id: int,
    customer_name: str,
    quantity: float,
    deposit_confirmed_at: str | None = None,
) -> int:
    if quantity <= 0:
        raise ValueError("수량은 0보다 커야 합니다")

    cur = conn.execute(
        "INSERT INTO orders (variant_id, customer_name, quantity, deposit_confirmed_at) "
        "VALUES (?, ?, ?, ?)",
        (variant_id, customer_name, quantity, deposit_confirmed_at),
    )
    conn.commit()
    return cur.lastrowid


def _row_to_order(row: tuple) -> dict:
    return {
        "id": row[0],
        "variant_id": row[1],
        "customer_name": row[2],
        "quantity": row[3],
        "deposit_confirmed_at": row[4],
        "status": row[5],
        "shipped_stock_transaction_id": row[6],
        "created_at": row[7],
    }


_SELECT_ORDER = (
    "SELECT id, variant_id, customer_name, quantity, deposit_confirmed_at, "
    "status, shipped_stock_transaction_id, created_at FROM orders"
)


def get_order(conn: sqlite3.Connection, order_id: int) -> dict | None:
    row = conn.execute(f"{_SELECT_ORDER} WHERE id = ?", (order_id,)).fetchone()
    return _row_to_order(row) if row else None


def list_orders(conn: sqlite3.Connection, status: str | None = None) -> list[dict]:
    if status:
        rows = conn.execute(
            f"{_SELECT_ORDER} WHERE status = ? ORDER BY created_at DESC", (status,)
        ).fetchall()
    else:
        rows = conn.execute(f"{_SELECT_ORDER} ORDER BY created_at DESC").fetchall()
    return [_row_to_order(row) for row in rows]


def ship_order(
    conn: sqlite3.Connection, order_id: int, occurred_on: str | None = None
) -> None:
    order = get_order(conn, order_id)
    if order is None:
        raise OrderNotFoundError(f"존재하지 않는 주문입니다: {order_id}")
    if order["status"] == "출고완료":
        raise OrderAlreadyShippedError("이미 출고 완료된 주문입니다.")

    variant = get_variant(conn, order["variant_id"])
    tx_id = record_transaction(
        conn,
        variant["item_id"],
        "shipment",
        order["quantity"],
        occurred_on=occurred_on,
        variant_id=order["variant_id"],
    )
    conn.execute(
        "UPDATE orders SET status = '출고완료', shipped_stock_transaction_id = ? WHERE id = ?",
        (tx_id, order_id),
    )
    conn.commit()
