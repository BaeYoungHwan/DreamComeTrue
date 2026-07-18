"""local-farm-inventory Streamlit 진입점."""
from datetime import date

import streamlit as st

from src.core.backup import backup_db
from src.core.db import DEFAULT_DB_PATH, get_connection, init_db
from src.dashboard.dashboard import (
    item_sales_ranking,
    monthly_sales_total,
    today_shipments,
)
from src.export.report import (
    export_all_data_to_excel_bytes,
    period_report,
    report_to_excel_bytes,
)
from src.inventory.items import (
    create_item,
    delete_item,
    list_items,
    update_custom_attributes,
)
from src.inventory.stock import InsufficientStockError, current_stock, record_transaction
from src.sales.sales import record_sale

st.set_page_config(page_title="local-farm-inventory", layout="centered")
st.title("로컬 팜 인벤토리")
st.write("농장 재고·매출 관리 시스템에 오신 것을 환영합니다.")


@st.cache_resource
def _get_conn():
    conn = get_connection(DEFAULT_DB_PATH)
    init_db(conn)
    try:
        backup_db(DEFAULT_DB_PATH)
    except FileNotFoundError:
        pass
    return conn


conn = _get_conn()

tab_items, tab_stock, tab_sales, tab_dashboard, tab_report = st.tabs(
    ["품목 관리", "입출고", "판매", "대시보드", "정산 리포트"]
)

TX_TYPE_LABELS = {"harvest": "수확(입고)", "shipment": "출하(출고)", "loss": "폐기/손실"}

with tab_items:
    st.subheader("품목 등록")
    with st.form("item_form", clear_on_submit=True):
        name = st.text_input("농작물 이름")
        unit = st.text_input("규격 (예: kg, 박스)")
        if st.form_submit_button("등록"):
            if name and unit:
                create_item(conn, name, unit)
                st.success(f"'{name}' 품목이 등록되었습니다.")
                st.rerun()
            else:
                st.error("이름과 규격을 모두 입력해주세요.")

    st.subheader("품목 목록")
    for item in list_items(conn):
        with st.expander(f"{item['name']} ({item['unit']})"):
            st.write("커스텀 속성:", item["custom_attributes"])

            col1, col2 = st.columns(2)
            new_key = col1.text_input("속성명 추가", key=f"key_{item['id']}")
            new_value = col2.text_input("속성값", key=f"value_{item['id']}")
            if st.button("속성 추가", key=f"add_attr_{item['id']}") and new_key:
                attrs = {**item["custom_attributes"], new_key: new_value}
                update_custom_attributes(conn, item["id"], attrs)
                st.rerun()

            for key in list(item["custom_attributes"].keys()):
                if st.button(f"'{key}' 속성 삭제", key=f"del_attr_{item['id']}_{key}"):
                    attrs = {k: v for k, v in item["custom_attributes"].items() if k != key}
                    update_custom_attributes(conn, item["id"], attrs)
                    st.rerun()

            if st.button("품목 삭제", key=f"del_item_{item['id']}"):
                delete_item(conn, item["id"])
                st.rerun()

with tab_stock:
    st.subheader("입출고 기록")
    items = list_items(conn)
    if not items:
        st.info("먼저 품목을 등록해주세요.")
    else:
        item_labels = {f"{item['name']} ({item['unit']})": item["id"] for item in items}
        with st.form("stock_form", clear_on_submit=True):
            selected_label = st.selectbox("품목", list(item_labels.keys()))
            tx_type = st.selectbox(
                "거래 유형", list(TX_TYPE_LABELS.keys()),
                format_func=lambda t: TX_TYPE_LABELS[t],
            )
            quantity = st.number_input("수량", min_value=0.0, step=0.1)
            if st.form_submit_button("기록"):
                try:
                    record_transaction(conn, item_labels[selected_label], tx_type, quantity)
                    st.success("거래가 기록되었습니다.")
                    st.rerun()
                except (ValueError, InsufficientStockError) as e:
                    st.error(str(e))

        st.subheader("현재 재고")
        for item in items:
            st.write(f"{item['name']}: {current_stock(conn, item['id'])} {item['unit']}")

with tab_sales:
    st.subheader("판매 기록")
    items = list_items(conn)
    if not items:
        st.info("먼저 품목을 등록해주세요.")
    else:
        item_labels = {f"{item['name']} ({item['unit']})": item["id"] for item in items}
        with st.form("sales_form", clear_on_submit=True):
            selected_label = st.selectbox("품목", list(item_labels.keys()), key="sales_item")
            buyer = st.text_input("출하처")
            quantity = st.number_input("판매 수량", min_value=0.0, step=0.1, key="sales_qty")
            unit_price = st.number_input("단가", min_value=0.0, step=100.0, key="sales_price")
            if st.form_submit_button("판매 등록"):
                try:
                    record_sale(conn, item_labels[selected_label], buyer, quantity, unit_price)
                    st.success("판매가 등록되었습니다.")
                    st.rerun()
                except (ValueError, InsufficientStockError) as e:
                    st.error(str(e))

with tab_dashboard:
    st.subheader("오늘 출하 현황")
    today_str = date.today().isoformat()
    shipments = today_shipments(conn, today_str)
    if shipments:
        st.table(shipments)
    else:
        st.info("오늘 출하 기록이 없습니다.")

    st.subheader("이달 누적 매출")
    year_month = date.today().strftime("%Y-%m")
    total = monthly_sales_total(conn, year_month)
    st.metric("이달 매출", f"{total:,.0f}원")

    st.subheader("품목별 판매 순위")
    ranking = item_sales_ranking(conn, year_month)
    if ranking:
        st.bar_chart({row["item_name"]: row["total_amount"] for row in ranking})
    else:
        st.info("이달 판매 기록이 없습니다.")

with tab_report:
    st.subheader("기간별 정산 리포트")
    col1, col2 = st.columns(2)
    start_date = col1.date_input("시작일")
    end_date = col2.date_input("종료일")

    if st.button("리포트 조회"):
        rows = period_report(conn, start_date.isoformat(), end_date.isoformat())
        if rows:
            st.table(rows)
            st.download_button(
                "정산 리포트 엑셀 다운로드",
                data=report_to_excel_bytes(rows),
                file_name=f"정산리포트_{start_date}_{end_date}.xlsx",
            )
        else:
            st.info("해당 기간에 판매 기록이 없습니다.")

    st.divider()
    st.subheader("전체 데이터 백업 (엑셀)")
    if st.button("전체 데이터 엑셀 내보내기"):
        st.download_button(
            "전체 데이터 엑셀 다운로드",
            data=export_all_data_to_excel_bytes(conn),
            file_name=f"farm_data_backup_{date.today().isoformat()}.xlsx",
        )
