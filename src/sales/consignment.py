"""위탁판매 2단계 관리 — 출고(판매대기) 후 실제 판매 수량 확정 시 매출 반영."""
import sqlite3

from src.inventory.stock import record_transaction
from src.sales.sales import _insert_sale_row


class ShipmentNotFoundError(Exception):
    """존재하지 않는 출고 건을 조회·확정하려 할 때 발생."""


class ShipmentAlreadyConfirmedError(Exception):
    """이미 판매 확정된 출고 건을 다시 확정하려 할 때 발생."""


def create_shipment(
    conn: sqlite3.Connection,
    item_id: int,
    channel_id: int,
    quantity: float,
    variant_id: int | None = None,
    shipped_on: str | None = None,
) -> int:
    if quantity <= 0:
        raise ValueError("수량은 0보다 커야 합니다")

    tx_id = record_transaction(
        conn, item_id, "shipment", quantity, occurred_on=shipped_on, variant_id=variant_id
    )
    cur = conn.execute(
        """
        INSERT INTO consignment_shipments
            (item_id, variant_id, channel_id, stock_transaction_id, shipped_quantity, shipped_at)
        VALUES (?, ?, ?, ?, ?, COALESCE(?, datetime('now')))
        """,
        (item_id, variant_id, channel_id, tx_id, quantity, shipped_on),
    )
    conn.commit()
    return cur.lastrowid


def _row_to_shipment(row: tuple) -> dict:
    return {
        "id": row[0],
        "item_id": row[1],
        "variant_id": row[2],
        "channel_id": row[3],
        "stock_transaction_id": row[4],
        "shipped_quantity": row[5],
        "status": row[6],
        "sold_quantity": row[7],
        "sale_id": row[8],
        "shipped_at": row[9],
        "confirmed_at": row[10],
    }


_SELECT_SHIPMENT = (
    "SELECT id, item_id, variant_id, channel_id, stock_transaction_id, shipped_quantity, "
    "status, sold_quantity, sale_id, shipped_at, confirmed_at FROM consignment_shipments"
)


def get_shipment(conn: sqlite3.Connection, shipment_id: int) -> dict | None:
    row = conn.execute(f"{_SELECT_SHIPMENT} WHERE id = ?", (shipment_id,)).fetchone()
    return _row_to_shipment(row) if row else None


def list_shipments(conn: sqlite3.Connection, status: str | None = None) -> list[dict]:
    if status:
        rows = conn.execute(
            f"{_SELECT_SHIPMENT} WHERE status = ? ORDER BY shipped_at DESC", (status,)
        ).fetchall()
    else:
        rows = conn.execute(f"{_SELECT_SHIPMENT} ORDER BY shipped_at DESC").fetchall()
    return [_row_to_shipment(row) for row in rows]


def confirm_sale(
    conn: sqlite3.Connection,
    shipment_id: int,
    sold_quantity: float,
    unit_price: float,
    sold_on: str | None = None,
) -> int:
    shipment = get_shipment(conn, shipment_id)
    if shipment is None:
        raise ShipmentNotFoundError(f"존재하지 않는 출고 건입니다: {shipment_id}")
    if shipment["status"] == "판매완료":
        raise ShipmentAlreadyConfirmedError("이미 판매 확정된 출고 건입니다.")
    if sold_quantity <= 0:
        raise ValueError("판매 수량은 0보다 커야 합니다")
    if sold_quantity > shipment["shipped_quantity"]:
        raise ValueError("판매 수량이 출고 수량보다 많을 수 없습니다")
    if unit_price <= 0:
        raise ValueError("단가는 0보다 커야 합니다")

    channel_name = conn.execute(
        "SELECT name FROM channels WHERE id = ?", (shipment["channel_id"],)
    ).fetchone()[0]
    sale_id = _insert_sale_row(
        conn,
        shipment["item_id"],
        shipment["stock_transaction_id"],
        shipment["channel_id"],
        shipment["variant_id"],
        channel_name,
        sold_quantity,
        unit_price,
        sold_on,
    )
    conn.execute(
        """
        UPDATE consignment_shipments
        SET status = '판매완료', sold_quantity = ?, sale_id = ?, confirmed_at = COALESCE(?, datetime('now'))
        WHERE id = ?
        """,
        (sold_quantity, sale_id, sold_on, shipment_id),
    )
    conn.commit()
    return sale_id
