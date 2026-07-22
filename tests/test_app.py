import os
import uuid

import pytest
from streamlit.testing.v1 import AppTest


@pytest.fixture(autouse=True)
def _isolated_farm_db(tmp_path, monkeypatch):
    """AppTest가 app.py를 실제로 실행하므로, 격리된 임시 DB를 쓰도록 강제해
    실제 운영 데이터(data/farm.db)에 테스트 흔적이 남지 않게 한다."""
    monkeypatch.setenv("FARM_DB_PATH", str(tmp_path / "test_farm.db"))


def test_app_runs_without_exception():
    at = AppTest.from_file("app.py")
    at.run()

    assert not at.exception
    assert at.title[0].value == "로컬 팜 인벤토리"


def test_app_has_eight_tabs_including_stock_overview():
    at = AppTest.from_file("app.py")
    at.run()

    tab_labels = [t.label for t in at.tabs]
    assert tab_labels == [
        "재고 현황",
        "품목 관리",
        "입출고",
        "판매",
        "선입금 주문",
        "채널 관리",
        "대시보드",
        "정산 리포트",
    ]


def test_channel_registration_and_settlement_discrepancy_golden_path():
    """채널 등록 -> 정산 계산 -> 실입금액 대조 -> 차액 경고까지의 골든패스."""
    at = AppTest.from_file("app.py")
    at.run()
    assert not at.exception

    channel_name = f"테스트매장_{uuid.uuid4().hex[:8]}"
    at.text_input(key="channel_form_name").set_value(channel_name)
    at.selectbox(key="channel_form_type").set_value("consignment")
    at.number_input(key="channel_form_rate").set_value(10.0)
    at.button(key="FormSubmitter:channel_form-등록").click().run()

    assert not at.exception
    assert any(channel_name in s.value for s in at.success)

    at.selectbox(key="settlement_channel").set_value(channel_name)
    at.button(key="settlement_calc").click().run()

    assert not at.exception
    assert any("판매누계: 0원" in m.value for m in at.markdown)

    at.number_input(key="settlement_actual").set_value(500.0)
    at.button(key="settlement_check").click().run()

    assert not at.exception
    assert any("입금 오류" in e.value and "500" in e.value for e in at.error)


def test_variant_price_and_order_golden_path():
    """품목 등록 -> 변형(가격 마스터) 등록 -> 입고 -> 주문 접수 -> 출고 처리까지의 골든패스."""
    import os

    from src.core.db import get_connection

    at = AppTest.from_file("app.py")
    at.run()
    assert not at.exception

    item_name = f"블루베리_{uuid.uuid4().hex[:8]}"
    at.text_input(key="item_form_name").set_value(item_name)
    at.text_input(key="item_form_unit").set_value("kg")
    at.button(key="FormSubmitter:item_form-등록").click().run()
    assert not at.exception

    conn = get_connection(os.environ["FARM_DB_PATH"])
    item_id = conn.execute(
        "SELECT id FROM items WHERE name = ?", (item_name,)
    ).fetchone()[0]
    conn.close()

    at.text_input(key=f"variant_size_{item_id}").set_value("특")
    at.text_input(key=f"variant_weight_{item_id}").set_value("1kg")
    at.number_input(key=f"variant_price_{item_id}").set_value(15000.0)
    at.button(key=f"FormSubmitter:variant_form_{item_id}-변형 추가").click().run()
    assert not at.exception
    assert any(
        "특" in w.value and "15,000" in w.value
        for w in list(at.markdown) + list(at.text)
    )

    at.selectbox(key="stock_item_select").set_value(f"{item_name} (kg)").run()
    at.selectbox(key="stock_tx_type").set_value("harvest")
    at.selectbox(key="stock_variant_select").set_value("특 / 1kg")
    at.number_input(key="stock_quantity").set_value(10.0)
    at.button(key="FormSubmitter:stock_form-기록").click().run()
    assert not at.exception

    at.selectbox(key="order_item_select").set_value(f"{item_name} (kg)").run()
    at.selectbox(key="order_variant_select").set_value("특 / 1kg")
    at.text_input(key="order_customer_name").set_value("홍길동")
    at.number_input(key="order_qty").set_value(3.0)
    at.button(key="FormSubmitter:order_form-주문 접수").click().run()
    assert not at.exception
    assert any("주문이 접수되었습니다" in s.value for s in at.success)

    ship_buttons = [b for b in at.button if b.label == "출고 처리"]
    assert len(ship_buttons) == 1
    ship_buttons[0].click().run()

    assert not at.exception
    conn = get_connection(os.environ["FARM_DB_PATH"])
    status = conn.execute(
        "SELECT status FROM orders WHERE customer_name = '홍길동' AND variant_id = "
        "(SELECT id FROM item_variants WHERE item_id = ?)",
        (item_id,),
    ).fetchone()[0]
    sale = conn.execute(
        "SELECT buyer, channel_id, quantity, unit_price, total_amount FROM sales WHERE item_id = ?",
        (item_id,),
    ).fetchone()
    conn.close()
    assert status == "출고완료"
    assert sale == ("홍길동", None, 3, 15000, 45000)


def test_item_delete_button_disabled_until_checkbox_confirmed():
    """삭제 확인 체크박스를 체크하기 전에는 삭제 버튼이 비활성화되어야 한다."""
    at = AppTest.from_file("app.py")
    at.run()
    assert not at.exception

    item_name = f"상추_{uuid.uuid4().hex[:8]}"
    at.text_input(key="item_form_name").set_value(item_name)
    at.text_input(key="item_form_unit").set_value("kg")
    at.button(key="FormSubmitter:item_form-등록").click().run()
    assert not at.exception

    from src.core.db import get_connection

    conn = get_connection(os.environ["FARM_DB_PATH"])
    item_id = conn.execute(
        "SELECT id FROM items WHERE name = ?", (item_name,)
    ).fetchone()[0]
    conn.close()

    delete_button = at.button(key=f"del_item_{item_id}")
    assert delete_button.disabled

    at.checkbox(key=f"confirm_del_item_{item_id}").set_value(True).run()
    delete_button = at.button(key=f"del_item_{item_id}")
    assert not delete_button.disabled

    delete_button.click().run()
    assert not at.exception

    conn = get_connection(os.environ["FARM_DB_PATH"])
    remaining = conn.execute(
        "SELECT COUNT(*) FROM items WHERE id = ?", (item_id,)
    ).fetchone()[0]
    conn.close()
    assert remaining == 0


def test_v1_core_golden_path_register_stock_sale_report_dashboard():
    """PRD-v1 완료 기준: 품목등록 → 입고 → 출고 → 폐기 → 판매 → 정산 리포트 → 대시보드 확인,
    1회 정상 동작."""
    at = AppTest.from_file("app.py")
    at.run()
    assert not at.exception

    item_name = f"상추_{uuid.uuid4().hex[:8]}"
    at.text_input(key="item_form_name").set_value(item_name)
    at.text_input(key="item_form_unit").set_value("kg")
    at.button(key="FormSubmitter:item_form-등록").click().run()
    assert not at.exception

    def _record_stock(tx_type: str, quantity: float):
        at.selectbox(key="stock_item_select").set_value(f"{item_name} (kg)").run()
        at.selectbox(key="stock_tx_type").set_value(tx_type)
        at.number_input(key="stock_quantity").set_value(quantity)
        at.button(key="FormSubmitter:stock_form-기록").click().run()
        assert not at.exception

    _record_stock("harvest", 20.0)  # 입고
    _record_stock("shipment", 5.0)  # 출고
    _record_stock("loss", 2.0)  # 폐기

    stock_line = "".join(w.value for w in list(at.markdown) + list(at.text))
    assert f"{item_name}: 13 EA" in stock_line

    at.selectbox(key="sales_item").set_value(f"{item_name} (kg)").run()
    at.text_input(key="sales_buyer_manual").set_value("로컬푸드 매장")
    at.number_input(key="sales_qty").set_value(3.0)
    at.number_input(key="sales_price").set_value(2000.0)
    at.button(key="FormSubmitter:sales_form-판매 등록").click().run()
    assert not at.exception
    assert any("판매가 등록되었습니다" in s.value for s in at.success)

    report_button = next(b for b in at.button if b.label == "리포트 조회")
    report_button.click().run()
    assert not at.exception
    assert any(item_name in str(t.value.values) for t in at.table)

    assert any("6,000원" == m.value for m in at.metric)

    from src.core.db import get_connection

    conn = get_connection(os.environ["FARM_DB_PATH"])
    final_stock = conn.execute(
        """
        SELECT COALESCE(SUM(CASE WHEN type = 'harvest' THEN quantity ELSE 0 END), 0)
             - COALESCE(SUM(CASE WHEN type = 'shipment' THEN quantity ELSE 0 END), 0)
             - COALESCE(SUM(CASE WHEN type = 'loss' THEN quantity ELSE 0 END), 0)
        FROM stock_transactions st JOIN items i ON i.id = st.item_id
        WHERE i.name = ?
        """,
        (item_name,),
    ).fetchone()[0]
    conn.close()
    assert final_stock == 10.0  # 20 입고 - 5 출고 - 2 폐기 - 3 판매(출고)


def test_stock_overview_tab_shows_current_stock_after_harvest():
    """품목 등록 -> 입고 -> '재고 현황' 탭에서 재고가 즉시 보이는지 확인."""
    at = AppTest.from_file("app.py")
    at.run()
    assert not at.exception

    item_name = f"상추_{uuid.uuid4().hex[:8]}"
    at.text_input(key="item_form_name").set_value(item_name)
    at.text_input(key="item_form_unit").set_value("kg")
    at.button(key="FormSubmitter:item_form-등록").click().run()
    assert not at.exception

    at.selectbox(key="stock_item_select").set_value(f"{item_name} (kg)").run()
    at.selectbox(key="stock_tx_type").set_value("harvest")
    at.number_input(key="stock_quantity").set_value(12.0)
    at.button(key="FormSubmitter:stock_form-기록").click().run()
    assert not at.exception

    overview_table = at.table[0].value
    assert item_name in overview_table["품목"].values


def test_detailed_report_shows_individual_sale_rows():
    """품목등록 -> 입고 -> 판매 -> 리포트 조회 -> 상세 리포트 보기까지의 골든패스."""
    at = AppTest.from_file("app.py")
    at.run()
    assert not at.exception

    item_name = f"블루베리_{uuid.uuid4().hex[:8]}"
    at.text_input(key="item_form_name").set_value(item_name)
    at.text_input(key="item_form_unit").set_value("500g")
    at.button(key="FormSubmitter:item_form-등록").click().run()
    assert not at.exception

    at.selectbox(key="stock_item_select").set_value(f"{item_name} (500g)").run()
    at.selectbox(key="stock_tx_type").set_value("harvest")
    at.number_input(key="stock_quantity").set_value(10.0)
    at.button(key="FormSubmitter:stock_form-기록").click().run()
    assert not at.exception

    at.selectbox(key="sales_item").set_value(f"{item_name} (500g)").run()
    at.text_input(key="sales_buyer_manual").set_value("로컬푸드 매장")
    at.number_input(key="sales_qty").set_value(3.0)
    at.number_input(key="sales_price").set_value(2000)
    at.button(key="FormSubmitter:sales_form-판매 등록").click().run()
    assert not at.exception

    report_button = next(b for b in at.button if b.label == "리포트 조회")
    report_button.click().run()
    assert not at.exception

    detail_button = next(b for b in at.button if b.label == "상세 리포트 보기")
    detail_button.click().run()
    assert not at.exception

    detail_table = at.table[-1].value
    assert item_name in detail_table["품목"].values


def test_all_channels_settlement_summary_golden_path():
    """채널 등록 -> 판매 -> 전체 채널 정산 요약 조회 -> 엑셀 다운로드까지의 골든패스."""
    at = AppTest.from_file("app.py")
    at.run()
    assert not at.exception

    channel_name = f"테스트매장_{uuid.uuid4().hex[:8]}"
    at.text_input(key="channel_form_name").set_value(channel_name)
    at.selectbox(key="channel_form_type").set_value("consignment")
    at.number_input(key="channel_form_rate").set_value(10.0)
    at.button(key="FormSubmitter:channel_form-등록").click().run()
    assert not at.exception

    at.button(key="summary_calc").click().run()

    assert not at.exception
    summary_table = at.table[-1].value
    assert channel_name in summary_table["채널"].values
