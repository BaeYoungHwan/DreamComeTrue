"""채널별 정산 — 판매누계·수수료·예상입금액 계산 및 입금 대사."""
import sqlite3

from src.settlement.channels import get_channel, list_channels


def channel_settlement(
    conn: sqlite3.Connection, channel_id: int, start_date: str, end_date: str
) -> dict:
    channel = get_channel(conn, channel_id)
    if channel is None:
        raise ValueError(f"채널 ID {channel_id}를 찾을 수 없습니다")

    row = conn.execute(
        """
        SELECT COALESCE(SUM(total_amount), 0)
        FROM sales
        WHERE channel_id = ? AND date(sold_at) BETWEEN date(?) AND date(?)
        """,
        (channel_id, start_date, end_date),
    ).fetchone()
    sales_total = row[0]
    commission_amount = round(sales_total * channel["commission_rate"] / 100)
    expected_deposit = sales_total - commission_amount

    return {
        "channel_id": channel_id,
        "channel_name": channel["name"],
        "period_start": start_date,
        "period_end": end_date,
        "sales_total": sales_total,
        "commission_rate": channel["commission_rate"],
        "commission_amount": commission_amount,
        "expected_deposit": expected_deposit,
    }


def all_channels_settlement(
    conn: sqlite3.Connection, start_date: str, end_date: str
) -> list[dict]:
    return [
        channel_settlement(conn, channel["id"], start_date, end_date)
        for channel in list_channels(conn)
    ]


def deposit_discrepancy(expected_deposit: float, actual_deposit: float) -> dict:
    diff = actual_deposit - expected_deposit
    return {
        "expected_deposit": expected_deposit,
        "actual_deposit": actual_deposit,
        "diff": diff,
        "has_error": diff != 0,
    }


def save_settlement(
    conn: sqlite3.Connection,
    channel_id: int,
    period_start: str,
    period_end: str,
    sales_total: float,
    commission_amount: float,
    expected_deposit: float,
    actual_deposit: float | None = None,
    deposit_date: str | None = None,
    memo: str | None = None,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO settlements (
            channel_id, period_start, period_end, sales_total,
            commission_amount, expected_deposit, actual_deposit, deposit_date, memo
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            channel_id,
            period_start,
            period_end,
            sales_total,
            commission_amount,
            expected_deposit,
            actual_deposit,
            deposit_date,
            memo,
        ),
    )
    conn.commit()
    return cur.lastrowid


def _row_to_settlement(row: tuple) -> dict:
    return {
        "id": row[0],
        "channel_id": row[1],
        "period_start": row[2],
        "period_end": row[3],
        "sales_total": row[4],
        "commission_amount": row[5],
        "expected_deposit": row[6],
        "actual_deposit": row[7],
        "deposit_date": row[8],
        "memo": row[9],
        "created_at": row[10],
    }


def list_settlements(conn: sqlite3.Connection, channel_id: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT id, channel_id, period_start, period_end, sales_total,
               commission_amount, expected_deposit, actual_deposit, deposit_date, memo, created_at
        FROM settlements
        WHERE channel_id = ?
        ORDER BY period_start DESC, id DESC
        """,
        (channel_id,),
    ).fetchall()
    return [_row_to_settlement(row) for row in rows]
