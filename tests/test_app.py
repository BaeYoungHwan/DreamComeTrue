import uuid

from streamlit.testing.v1 import AppTest


def test_app_runs_without_exception():
    at = AppTest.from_file("app.py")
    at.run()

    assert not at.exception
    assert at.title[0].value == "로컬 팜 인벤토리"


def test_app_has_seven_tabs_including_orders_and_channel_management():
    at = AppTest.from_file("app.py")
    at.run()

    tab_labels = [t.label for t in at.tabs]
    assert tab_labels == [
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
    from src.core.db import DEFAULT_DB_PATH, get_connection

    at = AppTest.from_file("app.py")
    at.run()
    assert not at.exception

    item_name = f"블루베리_{uuid.uuid4().hex[:8]}"
    at.text_input(key="item_form_name").set_value(item_name)
    at.text_input(key="item_form_unit").set_value("kg")
    at.button(key="FormSubmitter:item_form-등록").click().run()
    assert not at.exception

    conn = get_connection(DEFAULT_DB_PATH)
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
    conn = get_connection(DEFAULT_DB_PATH)
    status = conn.execute(
        "SELECT status FROM orders WHERE customer_name = '홍길동' AND variant_id = "
        "(SELECT id FROM item_variants WHERE item_id = ?)",
        (item_id,),
    ).fetchone()[0]
    conn.close()
    assert status == "출고완료"
