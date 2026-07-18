"""출하 채널(로컬푸드 매장 등) 마스터 관리."""
import sqlite3

VALID_CHANNEL_TYPES = ("consignment", "direct")


class ChannelNameConflictError(Exception):
    """이미 존재하는 채널명으로 등록·수정하려 할 때 발생."""


class ChannelInUseError(Exception):
    """판매·정산 기록이 있는 채널을 삭제하려 할 때 발생."""


def _validate(channel_type: str, commission_rate: float) -> None:
    if channel_type not in VALID_CHANNEL_TYPES:
        raise ValueError(f"channel_type은 {VALID_CHANNEL_TYPES} 중 하나여야 합니다")
    if commission_rate < 0:
        raise ValueError("수수료율은 0 이상이어야 합니다")


def create_channel(
    conn: sqlite3.Connection,
    name: str,
    channel_type: str,
    commission_rate: float = 0,
) -> int:
    _validate(channel_type, commission_rate)
    if conn.execute("SELECT id FROM channels WHERE name = ?", (name,)).fetchone():
        raise ChannelNameConflictError(f"'{name}' 채널은 이미 등록되어 있습니다.")

    cur = conn.execute(
        "INSERT INTO channels (name, channel_type, commission_rate) VALUES (?, ?, ?)",
        (name, channel_type, commission_rate),
    )
    conn.commit()
    return cur.lastrowid


def _row_to_channel(row: tuple) -> dict:
    return {
        "id": row[0],
        "name": row[1],
        "channel_type": row[2],
        "commission_rate": row[3],
        "created_at": row[4],
    }


def get_channel(conn: sqlite3.Connection, channel_id: int) -> dict | None:
    row = conn.execute(
        "SELECT id, name, channel_type, commission_rate, created_at FROM channels WHERE id = ?",
        (channel_id,),
    ).fetchone()
    return _row_to_channel(row) if row else None


def list_channels(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT id, name, channel_type, commission_rate, created_at FROM channels ORDER BY name"
    ).fetchall()
    return [_row_to_channel(row) for row in rows]


def update_channel(
    conn: sqlite3.Connection,
    channel_id: int,
    name: str,
    channel_type: str,
    commission_rate: float,
) -> None:
    _validate(channel_type, commission_rate)
    conflict = conn.execute(
        "SELECT id FROM channels WHERE name = ? AND id != ?", (name, channel_id)
    ).fetchone()
    if conflict:
        raise ChannelNameConflictError(f"'{name}' 채널은 이미 등록되어 있습니다.")

    conn.execute(
        "UPDATE channels SET name = ?, channel_type = ?, commission_rate = ? WHERE id = ?",
        (name, channel_type, commission_rate, channel_id),
    )
    conn.commit()


def delete_channel(conn: sqlite3.Connection, channel_id: int) -> None:
    sales_count = conn.execute(
        "SELECT COUNT(*) FROM sales WHERE channel_id = ?", (channel_id,)
    ).fetchone()[0]
    settlements_count = conn.execute(
        "SELECT COUNT(*) FROM settlements WHERE channel_id = ?", (channel_id,)
    ).fetchone()[0]
    if sales_count > 0 or settlements_count > 0:
        channel = get_channel(conn, channel_id)
        name = channel["name"] if channel else channel_id
        raise ChannelInUseError(
            f"'{name}' 채널은 판매·정산 기록이 있어 삭제할 수 없습니다."
        )

    conn.execute("DELETE FROM channels WHERE id = ?", (channel_id,))
    conn.commit()
