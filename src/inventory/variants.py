"""품목 변형(크기×무게) 및 가격 마스터 관리."""
import sqlite3


class VariantInUseError(Exception):
    """입출고·판매 기록이 있는 변형을 삭제하려 할 때 발생."""


def create_variant(
    conn: sqlite3.Connection,
    item_id: int,
    size: str | None = None,
    weight: str | None = None,
    default_price: float | None = None,
) -> int:
    cur = conn.execute(
        "INSERT INTO item_variants (item_id, size, weight, default_price) VALUES (?, ?, ?, ?)",
        (item_id, size, weight, default_price),
    )
    conn.commit()
    return cur.lastrowid


def _row_to_variant(row: tuple) -> dict:
    return {
        "id": row[0],
        "item_id": row[1],
        "size": row[2],
        "weight": row[3],
        "default_price": row[4],
        "created_at": row[5],
    }


def get_variant(conn: sqlite3.Connection, variant_id: int) -> dict | None:
    row = conn.execute(
        "SELECT id, item_id, size, weight, default_price, created_at "
        "FROM item_variants WHERE id = ?",
        (variant_id,),
    ).fetchone()
    return _row_to_variant(row) if row else None


def list_variants(conn: sqlite3.Connection, item_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT id, item_id, size, weight, default_price, created_at "
        "FROM item_variants WHERE item_id = ? ORDER BY size, weight",
        (item_id,),
    ).fetchall()
    return [_row_to_variant(row) for row in rows]


def update_variant(
    conn: sqlite3.Connection,
    variant_id: int,
    size: str | None,
    weight: str | None,
    default_price: float | None,
) -> None:
    conn.execute(
        "UPDATE item_variants SET size = ?, weight = ?, default_price = ? WHERE id = ?",
        (size, weight, default_price, variant_id),
    )
    conn.commit()


def delete_variant(conn: sqlite3.Connection, variant_id: int) -> None:
    tx_count = conn.execute(
        "SELECT COUNT(*) FROM stock_transactions WHERE variant_id = ?", (variant_id,)
    ).fetchone()[0]
    sales_count = conn.execute(
        "SELECT COUNT(*) FROM sales WHERE variant_id = ?", (variant_id,)
    ).fetchone()[0]
    if tx_count > 0 or sales_count > 0:
        raise VariantInUseError("입출고·판매 기록이 있어 변형을 삭제할 수 없습니다.")

    conn.execute("DELETE FROM item_variants WHERE id = ?", (variant_id,))
    conn.commit()
