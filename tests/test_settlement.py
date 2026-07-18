import pytest

from src.core.db import get_connection, init_db
from src.core.migrations import run_migrations
from src.inventory.items import create_item
from src.inventory.stock import record_transaction
from src.sales.sales import record_sale
from src.settlement.channels import create_channel
from src.settlement.settlement import (
    channel_settlement,
    deposit_discrepancy,
    list_settlements,
    save_settlement,
)


def _conn_with_channel_and_stock(tmp_path, commission_rate=10, quantity=100):
    conn = get_connection(str(tmp_path / "farm.db"))
    init_db(conn)
    run_migrations(conn)
    channel_id = create_channel(conn, "모현점", "consignment", commission_rate)
    item_id = create_item(conn, "블루베리", "500g")
    record_transaction(conn, item_id, "harvest", quantity)
    return conn, channel_id, item_id


def test_channel_settlement_aggregates_sales_within_period(tmp_path):
    conn, channel_id, item_id = _conn_with_channel_and_stock(tmp_path)
    record_sale(conn, item_id, "모현점", 10, 1000, sold_on="2026-06-15", channel_id=channel_id)
    record_sale(conn, item_id, "모현점", 5, 1000, sold_on="2026-06-20", channel_id=channel_id)
    record_sale(conn, item_id, "모현점", 3, 1000, sold_on="2026-07-05", channel_id=channel_id)

    result = channel_settlement(conn, channel_id, "2026-06-01", "2026-06-30")
    conn.close()

    assert result["sales_total"] == 15000


def test_channel_settlement_computes_commission_and_expected_deposit(tmp_path):
    conn, channel_id, item_id = _conn_with_channel_and_stock(tmp_path, commission_rate=10)
    record_sale(
        conn, item_id, "모현점", 1, 293400, sold_on="2026-06-15", channel_id=channel_id
    )

    result = channel_settlement(conn, channel_id, "2026-06-01", "2026-06-30")
    conn.close()

    assert result["sales_total"] == 293400
    assert result["commission_amount"] == 29340
    assert result["expected_deposit"] == 264060


def test_channel_settlement_excludes_other_channels(tmp_path):
    conn, channel_id, item_id = _conn_with_channel_and_stock(tmp_path)
    other_channel_id = create_channel(conn, "어양점", "consignment", 10)
    record_sale(conn, item_id, "모현점", 10, 1000, sold_on="2026-06-15", channel_id=channel_id)
    record_sale(
        conn, item_id, "어양점", 10, 1000, sold_on="2026-06-15", channel_id=other_channel_id
    )

    result = channel_settlement(conn, channel_id, "2026-06-01", "2026-06-30")
    conn.close()

    assert result["sales_total"] == 10000


def test_channel_settlement_raises_for_unknown_channel(tmp_path):
    conn, channel_id, item_id = _conn_with_channel_and_stock(tmp_path)

    with pytest.raises(ValueError):
        channel_settlement(conn, 999, "2026-06-01", "2026-06-30")
    conn.close()


def test_channel_settlement_with_no_sales_returns_zero(tmp_path):
    conn, channel_id, item_id = _conn_with_channel_and_stock(tmp_path)

    result = channel_settlement(conn, channel_id, "2026-06-01", "2026-06-30")
    conn.close()

    assert result["sales_total"] == 0
    assert result["commission_amount"] == 0
    assert result["expected_deposit"] == 0


def test_deposit_discrepancy_reports_no_error_when_matching():
    result = deposit_discrepancy(264060, 264060)

    assert result["diff"] == 0
    assert result["has_error"] is False


def test_deposit_discrepancy_reports_error_when_mismatched():
    result = deposit_discrepancy(264060, 260800)

    assert result["diff"] == -3260
    assert result["has_error"] is True


def test_dod_golden_ledger_case_flags_discrepancy(tmp_path):
    """PRD-v2 DoD: 모현점 판매누계 293,400원 → 수수료 10% 계산 시 29,340원(장부 기재 32,600원과 다름)
    → 예상입금액 264,060원. 실제 통장입금액(장부 기재 260,800원)과 대조하면
    시스템이 자동으로 차액(-3,260원)을 입금 오류로 잡아내야 한다."""
    conn, channel_id, item_id = _conn_with_channel_and_stock(tmp_path, commission_rate=10)
    record_sale(
        conn, item_id, "모현점", 1, 293400, sold_on="2026-06-22", channel_id=channel_id
    )

    result = channel_settlement(conn, channel_id, "2026-06-01", "2026-06-30")
    discrepancy = deposit_discrepancy(result["expected_deposit"], 260800)
    conn.close()

    assert discrepancy["has_error"] is True
    assert discrepancy["diff"] == -3260


def test_save_and_list_settlements(tmp_path):
    conn, channel_id, item_id = _conn_with_channel_and_stock(tmp_path)
    record_sale(conn, item_id, "모현점", 10, 1000, sold_on="2026-06-15", channel_id=channel_id)
    result = channel_settlement(conn, channel_id, "2026-06-01", "2026-06-30")

    save_settlement(
        conn,
        channel_id,
        result["period_start"],
        result["period_end"],
        result["sales_total"],
        result["commission_amount"],
        result["expected_deposit"],
        actual_deposit=8900,
        deposit_date="2026-07-01",
        memo="테스트 메모",
    )
    settlements = list_settlements(conn, channel_id)
    conn.close()

    assert len(settlements) == 1
    assert settlements[0]["actual_deposit"] == 8900
    assert settlements[0]["memo"] == "테스트 메모"
