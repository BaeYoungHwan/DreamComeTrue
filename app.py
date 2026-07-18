"""local-farm-inventory Streamlit 진입점."""
import os
from datetime import date

import streamlit as st

from src.core.backup import backup_db
from src.core.db import DEFAULT_DB_PATH, get_connection, init_db
from src.core.migrations import run_migrations
from src.dashboard.dashboard import (
    item_sales_ranking,
    item_variant_matrix,
    monthly_sales_total,
    today_shipments,
)
from src.export.report import (
    all_channels_settlement_to_excel_bytes,
    export_all_data_to_excel_bytes,
    period_report,
    report_to_excel_bytes,
    settlement_to_excel_bytes,
)
from src.inventory.items import (
    ItemInUseError,
    create_item,
    delete_item,
    get_item,
    list_items,
    update_custom_attributes,
)
from src.inventory.stock import (
    InsufficientStockError,
    current_stock,
    delete_transaction,
    list_transactions,
    record_transaction,
)
from src.inventory.variants import (
    VariantInUseError,
    create_variant,
    delete_variant,
    get_variant,
    list_variants,
)
from src.orders.orders import (
    OrderAlreadyShippedError,
    OrderNotFoundError,
    create_order,
    list_orders,
    ship_order,
)
from src.sales.sales import delete_sale, list_sales, record_sale
from src.settlement.channels import (
    ChannelInUseError,
    ChannelNameConflictError,
    create_channel,
    delete_channel,
    list_channels,
    update_channel,
)
from src.settlement.settlement import (
    all_channels_settlement,
    channel_settlement,
    deposit_discrepancy,
    save_settlement,
)

st.set_page_config(page_title="local-farm-inventory", layout="centered")
st.title("로컬 팜 인벤토리")
st.write("농장 재고·매출 관리 시스템에 오신 것을 환영합니다.")


@st.cache_resource
def _get_conn(db_path: str):
    conn = get_connection(db_path)
    init_db(conn)
    run_migrations(conn)
    try:
        backup_db(db_path)
    except FileNotFoundError:
        pass
    return conn


conn = _get_conn(os.environ.get("FARM_DB_PATH", DEFAULT_DB_PATH))

tab_items, tab_stock, tab_sales, tab_orders, tab_channels, tab_dashboard, tab_report = st.tabs(
    ["품목 관리", "입출고", "판매", "선입금 주문", "채널 관리", "대시보드", "정산 리포트"]
)

CHANNEL_TYPE_LABELS = {"consignment": "위탁판매", "direct": "직거래"}

TX_TYPE_LABELS = {"harvest": "수확(입고)", "shipment": "출하(출고)", "loss": "폐기/손실"}

with tab_items:
    st.subheader("품목 등록")
    with st.form("item_form", clear_on_submit=True):
        name = st.text_input("농작물 이름", key="item_form_name")
        unit = st.text_input("규격 (예: kg, 박스)", key="item_form_unit")
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
            st.caption(
                "품목마다 다르게 기록하고 싶은 추가 정보를 자유롭게 적어두는 "
                "메모입니다 (예: 당도, 재배방식, 포장단위). 입력하지 않아도 됩니다."
            )
            if item["custom_attributes"]:
                for attr_key, attr_value in item["custom_attributes"].items():
                    st.write(f"- {attr_key}: {attr_value}")
            else:
                st.caption("등록된 속성이 없습니다.")

            col1, col2 = st.columns(2)
            new_key = col1.text_input(
                "속성명 추가", placeholder="예: 당도", key=f"key_{item['id']}"
            )
            new_value = col2.text_input(
                "속성값", placeholder="예: 10 브릭스", key=f"value_{item['id']}"
            )
            if st.button("속성 추가", key=f"add_attr_{item['id']}") and new_key:
                attrs = {**item["custom_attributes"], new_key: new_value}
                update_custom_attributes(conn, item["id"], attrs)
                st.rerun()

            for key in list(item["custom_attributes"].keys()):
                if st.button(f"'{key}' 속성 삭제", key=f"del_attr_{item['id']}_{key}"):
                    attrs = {k: v for k, v in item["custom_attributes"].items() if k != key}
                    update_custom_attributes(conn, item["id"], attrs)
                    st.rerun()

            st.write("**변형(크기×무게) 및 가격 마스터**")
            st.caption(
                "블루베리처럼 크기(특/대/중)와 무게(1kg/500g 등 포장단위)로 나눠 파는 "
                "품목이면 여기서 변형을 등록하세요. 변형별로 재고와 기준 단가를 따로 "
                "관리하며, 기준 단가는 판매 시 자동으로 채워집니다(수정 가능)."
            )
            variants = list_variants(conn, item["id"])
            for v in variants:
                v_col1, v_col2 = st.columns([4, 1])
                price_label = (
                    f"{v['default_price']:,.0f}원" if v["default_price"] is not None else "미설정"
                )
                v_stock = current_stock(conn, item["id"], variant_id=v["id"])
                v_col1.write(
                    f"{v['size'] or '-'} / {v['weight'] or '-'} · 기준단가 {price_label} "
                    f"· 재고 {v_stock}{item['unit']}"
                )
                if v_col2.button("삭제", key=f"del_variant_{v['id']}"):
                    try:
                        delete_variant(conn, v["id"])
                        st.rerun()
                    except VariantInUseError as e:
                        st.error(str(e))

            with st.form(f"variant_form_{item['id']}", clear_on_submit=True):
                vc1, vc2, vc3 = st.columns(3)
                new_size = vc1.text_input(
                    "크기(등급)", placeholder="예: 특", key=f"variant_size_{item['id']}"
                )
                new_weight = vc2.text_input(
                    "무게(포장단위)", placeholder="예: 1kg", key=f"variant_weight_{item['id']}"
                )
                new_price = vc3.number_input(
                    "기준 단가", min_value=0.0, step=100.0, key=f"variant_price_{item['id']}"
                )
                if st.form_submit_button("변형 추가"):
                    create_variant(
                        conn,
                        item["id"],
                        size=new_size or None,
                        weight=new_weight or None,
                        default_price=new_price or None,
                    )
                    st.rerun()

            transactions = list_transactions(conn, item["id"])
            if transactions:
                st.write("**입출고 내역**")
                for tx in transactions:
                    tx_col1, tx_col2 = st.columns([4, 1])
                    tx_col1.write(
                        f"{TX_TYPE_LABELS[tx['type']]} · {tx['quantity']}{item['unit']} · {tx['created_at']}"
                    )
                    if tx_col2.button("삭제", key=f"del_tx_{tx['id']}"):
                        delete_transaction(conn, tx["id"])
                        st.rerun()

            sales_history = list_sales(conn, item["id"])
            if sales_history:
                st.write("**판매 내역**")
                for s in sales_history:
                    s_col1, s_col2 = st.columns([4, 1])
                    s_col1.write(
                        f"{s['sold_at']} · {s['buyer']} · {s['quantity']}{item['unit']} · "
                        f"{s['unit_price']:,.0f}원 · 합계 {s['total_amount']:,.0f}원"
                    )
                    if s_col2.button("삭제", key=f"del_sale_{s['id']}"):
                        delete_sale(conn, s["id"])
                        st.rerun()

            if not transactions and not sales_history:
                st.caption("입출고·판매 기록이 없어 바로 삭제할 수 있습니다.")

            if st.button("품목 삭제", key=f"del_item_{item['id']}"):
                try:
                    delete_item(conn, item["id"])
                    st.rerun()
                except ItemInUseError as e:
                    st.error(str(e))

with tab_stock:
    st.subheader("입출고 기록")
    items = list_items(conn)
    if not items:
        st.info("먼저 품목을 등록해주세요.")
    else:
        item_labels = {f"{item['name']} ({item['unit']})": item["id"] for item in items}
        selected_label = st.selectbox("품목", list(item_labels.keys()), key="stock_item_select")
        selected_item_id = item_labels[selected_label]
        NO_VARIANT_STOCK = "변형 없음"
        variant_stock_labels = {NO_VARIANT_STOCK: None}
        for v in list_variants(conn, selected_item_id):
            variant_stock_labels[f"{v['size'] or '-'} / {v['weight'] or '-'}"] = v["id"]

        with st.form("stock_form", clear_on_submit=True):
            tx_type = st.selectbox(
                "거래 유형", list(TX_TYPE_LABELS.keys()),
                format_func=lambda t: TX_TYPE_LABELS[t],
                key="stock_tx_type",
            )
            selected_variant_label = st.selectbox(
                "변형(해당 시 선택)", list(variant_stock_labels.keys()), key="stock_variant_select"
            )
            quantity = st.number_input("수량", min_value=0.0, step=0.1, key="stock_quantity")
            tx_date = st.date_input("거래 일자", value=date.today(), key="stock_date")
            if st.form_submit_button("기록"):
                try:
                    record_transaction(
                        conn,
                        selected_item_id,
                        tx_type,
                        quantity,
                        occurred_on=tx_date.isoformat(),
                        variant_id=variant_stock_labels[selected_variant_label],
                    )
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
        channels = list_channels(conn)
        channel_labels = {c["name"]: c["id"] for c in channels}
        NO_CHANNEL = "직접 입력 (채널 미지정)"
        channel_options = [NO_CHANNEL] + list(channel_labels.keys())

        selected_label = st.selectbox("품목", list(item_labels.keys()), key="sales_item")
        selected_item_id = item_labels[selected_label]
        NO_VARIANT_SALE = "변형 없음"
        variant_sale_labels = {NO_VARIANT_SALE: None}
        for v in list_variants(conn, selected_item_id):
            variant_sale_labels[f"{v['size'] or '-'} / {v['weight'] or '-'}"] = v["id"]

        def _apply_variant_price():
            variant_id = variant_sale_labels.get(st.session_state.get("sales_variant"))
            if variant_id:
                variant = get_variant(conn, variant_id)
                if variant["default_price"] is not None:
                    st.session_state["sales_price"] = float(variant["default_price"])

        selected_variant_label = st.selectbox(
            "변형(해당 시 선택 — 기준 단가가 자동으로 채워집니다)",
            list(variant_sale_labels.keys()),
            key="sales_variant",
            on_change=_apply_variant_price,
        )

        with st.form("sales_form", clear_on_submit=True):
            selected_channel = st.selectbox("채널 (로컬푸드 매장 등)", channel_options, key="sales_channel")
            buyer_manual = st.text_input(
                "직접 입력 출하처 (채널을 선택하지 않은 경우에만 사용)", key="sales_buyer_manual"
            )
            quantity = st.number_input("판매 수량", min_value=0.0, step=0.1, key="sales_qty")
            unit_price = st.number_input("단가", min_value=0.0, step=100.0, key="sales_price")
            sale_date = st.date_input("판매 일자", value=date.today(), key="sales_date")
            if st.form_submit_button("판매 등록"):
                if selected_channel == NO_CHANNEL:
                    buyer, channel_id = buyer_manual, None
                else:
                    buyer, channel_id = selected_channel, channel_labels[selected_channel]
                try:
                    record_sale(
                        conn,
                        selected_item_id,
                        buyer,
                        quantity,
                        unit_price,
                        sold_on=sale_date.isoformat(),
                        channel_id=channel_id,
                        variant_id=variant_sale_labels[selected_variant_label],
                    )
                    st.success("판매가 등록되었습니다.")
                    st.rerun()
                except (ValueError, InsufficientStockError) as e:
                    st.error(str(e))
        if not channels:
            st.caption(
                "'채널 관리' 탭에서 로컬푸드 매장 등을 등록하면 정산 리포트에서 "
                "수수료 자동계산을 이용할 수 있습니다."
            )

with tab_orders:
    st.caption(
        "입금을 먼저 받고 재고가 준비되면 나중에 출고하는 주문입니다. "
        "직거래 택배처럼 출고 후 입금을 확인하는 방식과는 순서가 반대입니다."
    )
    st.subheader("주문 접수")
    order_items = list_items(conn)
    if not order_items:
        st.info("먼저 품목을 등록해주세요.")
    else:
        order_item_labels = {
            f"{item['name']} ({item['unit']})": item["id"] for item in order_items
        }
        order_selected_label = st.selectbox(
            "품목", list(order_item_labels.keys()), key="order_item_select"
        )
        order_item_id = order_item_labels[order_selected_label]
        order_variants = list_variants(conn, order_item_id)

        if not order_variants:
            st.info("이 품목에 등록된 변형이 없습니다. '품목 관리' 탭에서 변형을 먼저 등록해주세요.")
        else:
            order_variant_labels = {
                f"{v['size'] or '-'} / {v['weight'] or '-'}": v["id"] for v in order_variants
            }
            with st.form("order_form", clear_on_submit=True):
                order_selected_variant = st.selectbox(
                    "변형", list(order_variant_labels.keys()), key="order_variant_select"
                )
                customer_name = st.text_input("고객명", key="order_customer_name")
                order_quantity = st.number_input("수량", min_value=0.0, step=0.1, key="order_qty")
                deposit_date = st.date_input(
                    "선입금 확인일", value=date.today(), key="order_deposit_date"
                )
                if st.form_submit_button("주문 접수"):
                    if customer_name:
                        create_order(
                            conn,
                            order_variant_labels[order_selected_variant],
                            customer_name,
                            order_quantity,
                            deposit_confirmed_at=deposit_date.isoformat(),
                        )
                        st.success("주문이 접수되었습니다.")
                        st.rerun()
                    else:
                        st.error("고객명을 입력해주세요.")

    def _order_display_label(order: dict) -> str:
        variant = get_variant(conn, order["variant_id"])
        item = get_item(conn, variant["item_id"]) if variant else None
        item_name = item["name"] if item else "알 수 없음"
        variant_label = f"{variant['size'] or '-'} / {variant['weight'] or '-'}" if variant else "-"
        return (
            f"{order['customer_name']} · {item_name} ({variant_label}) · {order['quantity']}개 "
            f"· 선입금확인: {order['deposit_confirmed_at'] or '-'}"
        )

    st.subheader("출고 대기 목록")
    waiting_orders = list_orders(conn, status="출고대기")
    if not waiting_orders:
        st.info("출고 대기 중인 주문이 없습니다.")
    else:
        for o in waiting_orders:
            o_col1, o_col2 = st.columns([4, 1])
            o_col1.write(_order_display_label(o))
            if o_col2.button("출고 처리", key=f"ship_order_{o['id']}"):
                try:
                    ship_order(conn, o["id"])
                    st.rerun()
                except (OrderNotFoundError, OrderAlreadyShippedError, InsufficientStockError) as e:
                    st.error(str(e))

    st.subheader("출고 완료 내역")
    shipped_orders = list_orders(conn, status="출고완료")
    if shipped_orders:
        for o in shipped_orders:
            st.write(_order_display_label(o))
    else:
        st.caption("출고 완료된 주문이 없습니다.")

with tab_channels:
    st.subheader("채널 등록 (로컬푸드 매장 등)")
    with st.form("channel_form", clear_on_submit=True):
        channel_name = st.text_input("채널명 (예: 모현점)", key="channel_form_name")
        channel_type = st.selectbox(
            "유형",
            list(CHANNEL_TYPE_LABELS.keys()),
            format_func=lambda t: CHANNEL_TYPE_LABELS[t],
            key="channel_form_type",
        )
        commission_rate = st.number_input(
            "수수료율(%)", min_value=0.0, step=0.1, key="channel_form_rate"
        )
        if st.form_submit_button("등록"):
            if channel_name:
                try:
                    create_channel(conn, channel_name, channel_type, commission_rate)
                    st.success(f"'{channel_name}' 채널이 등록되었습니다.")
                    st.rerun()
                except ChannelNameConflictError as e:
                    st.error(str(e))
            else:
                st.error("채널명을 입력해주세요.")

    st.subheader("채널 목록")
    channels = list_channels(conn)
    if not channels:
        st.info("등록된 채널이 없습니다.")
    else:
        for c in channels:
            type_label = CHANNEL_TYPE_LABELS[c["channel_type"]]
            with st.expander(f"{c['name']} ({type_label}, 수수료 {c['commission_rate']}%)"):
                col1, col2, col3 = st.columns(3)
                new_name = col1.text_input("채널명", value=c["name"], key=f"ch_name_{c['id']}")
                new_type = col2.selectbox(
                    "유형",
                    list(CHANNEL_TYPE_LABELS.keys()),
                    index=list(CHANNEL_TYPE_LABELS.keys()).index(c["channel_type"]),
                    format_func=lambda t: CHANNEL_TYPE_LABELS[t],
                    key=f"ch_type_{c['id']}",
                )
                new_rate = col3.number_input(
                    "수수료율(%)",
                    min_value=0.0,
                    step=0.1,
                    value=float(c["commission_rate"]),
                    key=f"ch_rate_{c['id']}",
                )
                btn_col1, btn_col2 = st.columns(2)
                if btn_col1.button("수정 저장", key=f"ch_update_{c['id']}"):
                    try:
                        update_channel(conn, c["id"], new_name, new_type, new_rate)
                        st.rerun()
                    except ChannelNameConflictError as e:
                        st.error(str(e))
                if btn_col2.button("삭제", key=f"ch_delete_{c['id']}"):
                    try:
                        delete_channel(conn, c["id"])
                        st.rerun()
                    except ChannelInUseError as e:
                        st.error(str(e))

with tab_dashboard:
    st.subheader("오늘 출하 현황")
    today_str = date.today().isoformat()
    shipments = today_shipments(conn, today_str)
    if shipments:
        st.table(
            [{"품목": s["item_name"], "수량": s["quantity"]} for s in shipments]
        )
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

    st.subheader("품목 × 변형 매트릭스")
    matrix = item_variant_matrix(conn, year_month)
    if matrix:
        st.table(
            [
                {
                    "품목": r["item_name"],
                    "크기": r["size"] or "-",
                    "무게": r["weight"] or "-",
                    "판매수량": r["total_quantity"],
                    "판매대금": r["total_amount"],
                }
                for r in matrix
            ]
        )
    else:
        st.caption("이달 변형별 판매 기록이 없습니다.")

with tab_report:
    st.subheader("기간별 정산 리포트")
    col1, col2 = st.columns(2)
    start_date = col1.date_input("시작일")
    end_date = col2.date_input("종료일")

    if st.button("리포트 조회"):
        st.session_state["report_rows"] = period_report(
            conn, start_date.isoformat(), end_date.isoformat()
        )
        st.session_state["report_range"] = (start_date, end_date)

    if "report_rows" in st.session_state:
        rows = st.session_state["report_rows"]
        range_start, range_end = st.session_state["report_range"]
        if rows:
            st.table(
                [
                    {
                        "품목": r["item_name"],
                        "출하량": r["total_quantity"],
                        "판매대금": r["total_amount"],
                    }
                    for r in rows
                ]
            )
            st.download_button(
                "정산 리포트 엑셀 다운로드",
                data=report_to_excel_bytes(rows),
                file_name=f"정산리포트_{range_start}_{range_end}.xlsx",
            )
        else:
            st.info("해당 기간에 판매 기록이 없습니다.")

    st.divider()
    st.subheader("전체 채널 정산 요약")
    st.caption("등록된 모든 채널을 한 화면에서 비교합니다. 매장별로 하나씩 볼 필요 없이 전체 현황을 확인하세요.")
    all_channels_now = list_channels(conn)
    if not all_channels_now:
        st.info("'채널 관리' 탭에서 먼저 채널을 등록해주세요.")
    else:
        sum_col1, sum_col2 = st.columns(2)
        summary_start = sum_col1.date_input("시작일", key="summary_start")
        summary_end = sum_col2.date_input("종료일", key="summary_end")

        if st.button("전체 채널 조회", key="summary_calc"):
            st.session_state["summary_results"] = all_channels_settlement(
                conn, summary_start.isoformat(), summary_end.isoformat()
            )
            st.session_state["summary_range"] = (summary_start, summary_end)

        if "summary_results" in st.session_state:
            summary_results = st.session_state["summary_results"]
            summary_range_start, summary_range_end = st.session_state["summary_range"]
            st.table(
                [
                    {
                        "채널": r["channel_name"],
                        "판매누계": r["sales_total"],
                        "수수료율(%)": r["commission_rate"],
                        "수수료": r["commission_amount"],
                        "예상입금액": r["expected_deposit"],
                    }
                    for r in summary_results
                ]
            )
            st.download_button(
                "전체 채널 정산 엑셀 다운로드",
                data=all_channels_settlement_to_excel_bytes(summary_results),
                file_name=f"전체채널정산_{summary_range_start}_{summary_range_end}.xlsx",
                key="summary_download",
            )

    st.divider()
    st.subheader("채널별 정산 (수수료 자동계산)")
    settlement_channels = list_channels(conn)
    if not settlement_channels:
        st.info("'채널 관리' 탭에서 먼저 채널을 등록해주세요.")
    else:
        settlement_channel_labels = {c["name"]: c["id"] for c in settlement_channels}
        s_col1, s_col2, s_col3 = st.columns(3)
        selected_channel_name = s_col1.selectbox(
            "채널", list(settlement_channel_labels.keys()), key="settlement_channel"
        )
        settlement_start = s_col2.date_input("정산 시작일", key="settlement_start")
        settlement_end = s_col3.date_input("정산 종료일", key="settlement_end")

        if st.button("정산 계산", key="settlement_calc"):
            st.session_state["settlement_result"] = channel_settlement(
                conn,
                settlement_channel_labels[selected_channel_name],
                settlement_start.isoformat(),
                settlement_end.isoformat(),
            )
            st.session_state.pop("settlement_discrepancy", None)

        if "settlement_result" in st.session_state:
            result = st.session_state["settlement_result"]
            st.write(f"**{result['channel_name']}** ({result['period_start']} ~ {result['period_end']})")
            st.write(f"판매누계: {result['sales_total']:,.0f}원")
            st.write(f"수수료 ({result['commission_rate']}%): {result['commission_amount']:,.0f}원")
            st.write(f"예상입금액: {result['expected_deposit']:,.0f}원")

            actual_deposit = st.number_input(
                "실제 통장입금액", min_value=0.0, step=100.0, key="settlement_actual"
            )
            if st.button("입금 대조", key="settlement_check"):
                discrepancy = deposit_discrepancy(result["expected_deposit"], actual_deposit)
                st.session_state["settlement_discrepancy"] = discrepancy
                save_settlement(
                    conn,
                    result["channel_id"],
                    result["period_start"],
                    result["period_end"],
                    result["sales_total"],
                    result["commission_amount"],
                    result["expected_deposit"],
                    actual_deposit=actual_deposit,
                    deposit_date=date.today().isoformat(),
                )

            if "settlement_discrepancy" in st.session_state:
                d = st.session_state["settlement_discrepancy"]
                if d["has_error"]:
                    st.error(
                        f"입금 오류: 차액 {d['diff']:,.0f}원 "
                        f"(예상 {d['expected_deposit']:,.0f}원 / 실제 {d['actual_deposit']:,.0f}원)"
                    )
                else:
                    st.success("예상입금액과 실입금액이 일치합니다.")

            download_result = {**result, **st.session_state.get("settlement_discrepancy", {})}
            st.download_button(
                "채널 정산 엑셀 다운로드",
                data=settlement_to_excel_bytes(download_result),
                file_name=f"채널정산_{result['channel_name']}_{result['period_start']}_{result['period_end']}.xlsx",
                key="settlement_download",
            )

    st.divider()
    st.subheader("전체 데이터 백업 (엑셀)")
    if st.button("전체 데이터 엑셀 내보내기"):
        st.session_state["backup_bytes"] = export_all_data_to_excel_bytes(conn)
        st.session_state["backup_date"] = date.today().isoformat()

    if "backup_bytes" in st.session_state:
        st.download_button(
            "전체 데이터 엑셀 다운로드",
            data=st.session_state["backup_bytes"],
            file_name=f"전체데이터백업_{st.session_state['backup_date']}.xlsx",
        )
