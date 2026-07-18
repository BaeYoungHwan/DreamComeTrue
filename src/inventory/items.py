"""품목 등록·조회·커스텀 속성 관리."""
import json
import sqlite3


class ItemInUseError(Exception):
    """입출고·판매 기록이 있는 품목을 삭제하려 할 때 발생."""


def create_item(
    conn: sqlite3.Connection,
    name: str,
    unit: str,
    custom_attributes: dict | None = None,
) -> int:
    attrs_json = json.dumps(custom_attributes or {}, ensure_ascii=False)
    cur = conn.execute(
        "INSERT INTO items (name, unit, custom_attributes) VALUES (?, ?, ?)",
        (name, unit, attrs_json),
    )
    conn.commit()
    return cur.lastrowid


def _row_to_item(row: tuple) -> dict:
    return {
        "id": row[0],
        "name": row[1],
        "unit": row[2],
        "custom_attributes": json.loads(row[3]),
        "created_at": row[4],
    }


def get_item(conn: sqlite3.Connection, item_id: int) -> dict | None:
    row = conn.execute(
        "SELECT id, name, unit, custom_attributes, created_at FROM items WHERE id = ?",
        (item_id,),
    ).fetchone()
    return _row_to_item(row) if row else None


def list_items(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT id, name, unit, custom_attributes, created_at FROM items ORDER BY name"
    ).fetchall()
    return [_row_to_item(row) for row in rows]


def update_custom_attributes(
    conn: sqlite3.Connection, item_id: int, custom_attributes: dict
) -> None:
    conn.execute(
        "UPDATE items SET custom_attributes = ? WHERE id = ?",
        (json.dumps(custom_attributes, ensure_ascii=False), item_id),
    )
    conn.commit()


def delete_item(conn: sqlite3.Connection, item_id: int) -> None:
    tx_count = conn.execute(
        "SELECT COUNT(*) FROM stock_transactions WHERE item_id = ?", (item_id,)
    ).fetchone()[0]
    sales_count = conn.execute(
        "SELECT COUNT(*) FROM sales WHERE item_id = ?", (item_id,)
    ).fetchone()[0]
    if tx_count > 0 or sales_count > 0:
        item = get_item(conn, item_id)
        name = item["name"] if item else item_id
        raise ItemInUseError(
            f"'{name}' 품목은 입출고·판매 기록이 있어 삭제할 수 없습니다."
        )

    conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
