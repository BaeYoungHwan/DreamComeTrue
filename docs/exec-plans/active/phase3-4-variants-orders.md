# Phase 3-4 — 품목 변형(크기×무게)·가격 마스터 + 선입금 주문출하

> 출처: `docs/product-specs/PRD-v2.md` 7-C, 7-D 절
> 생성: 2026-07-18 (다른 창의 Phase 1 채널·정산 작업 완료 확인 후 착수)

## 목표
품목마다 크기×무게 조합의 "변형(variant)"을 등록하고 변형별 기준 단가(가격 마스터)를 설정, 입출고·판매 시 변형을 선택하면 재고가 변형 단위로 추적되고 단가가 자동으로 채워지도록 한다. 또한 선입금 주문(고객명·변형·수량·입금확인일 → 출고대기 → 출고완료)을 관리한다.

## 태스크
- [x] `src/core/db.py` — SCHEMA_SQL에 `item_variants`/`orders` 테이블, `stock_transactions`/`sales.variant_id` 반영 (신규 설치용)
- [x] `src/core/migrations.py` — migration 002(item_variants + variant_id 컬럼), 003(orders) 추가
- [x] `tests/test_migrations.py` 확장 — 002/003 멱등성·컬럼 생성 검증
- [x] `tests/test_variants.py` — 변형 CRUD, 삭제 차단(VariantInUseError)
- [x] `src/inventory/variants.py` — CRUD + 예외 클래스
- [x] `tests/test_stock.py` 확장 — variant_id 지정 시 변형별 재고 계산·차감
- [x] `src/inventory/stock.py` — `record_transaction`/`current_stock`에 `variant_id` 지원
- [x] `tests/test_sales.py` 확장 — variant_id 지정 케이스
- [x] `src/sales/sales.py` — `record_sale`/`list_sales`에 `variant_id` 지원
- [x] `tests/test_orders.py` — 주문 생성/조회/출고 처리, 이미 출고된 주문 재출고 차단
- [x] `src/orders/orders.py` — 주문 CRUD + 출고 처리(재고 차감 연동)
- [x] `tests/test_dashboard.py` 확장 — 품목×변형 매트릭스 집계
- [x] `src/dashboard/dashboard.py` — 품목×변형 매트릭스 함수 추가
- [x] `tests/test_app.py` 확장 — 7탭 골든패스(변형 등록·가격 자동표시, 입고, 주문 접수→출고 처리)
- [x] `app.py` — 품목 관리 탭에 변형·가격 관리 UI, 입출고·판매 탭에 변형 선택+단가 자동입력, 신규 "선입금 주문" 탭, 대시보드 매트릭스
- [x] pytest 전체 통과 (88개)
- [ ] 브라우저 골든패스 검증 — 다른 세션이 chrome-devtools 브라우저 프로필을 점유 중이라 보류. AppTest 골든패스(`test_variant_price_and_order_golden_path`)로 동일 시나리오를 대체 검증함 (품목→변형/가격 등록→입고→주문접수→출고처리, 각 단계 DB 상태까지 직접 조회해 확인).

## 완료 기준 (DoD, PRD-v2 5절 참조)
- [x] 품목 하나에 여러 변형(예: 블루베리-특-1kg / 블루베리-특-500g)을 등록하고 변형별 재고가 독립적으로 추적됨
- [x] 변형에 기준 단가를 설정해두면 판매 입력 시 수량만 입력해도 단가·합계가 자동 계산됨 (직접 수정도 가능 — `on_change` 콜백으로 단가 자동 반영)
- [x] 선입금 주문 접수 → 출고 처리 시나리오가 오류 없이 1회 동작 (AppTest + DB 상태로 확인)
- [x] 기존(변형 없는) 품목·거래는 그대로 동작 (하위 호환 — variant_id 옵션 파라미터, 기존 테스트 전부 무수정 통과)

## 참고 — 발견한 이슈
`ship_order()` 버튼 핸들러에서 `st.success(...)` 직후 `st.rerun()`을 호출하면 메시지가 렌더링되지 않는(직전 세션에서 정산 리포트 탭에 발생했던 것과 동일한 유형의) 문제를 AppTest로 사전에 발견. 기존 삭제 버튼들의 컨벤션(액션 후 바로 rerun, 성공 메시지 생략)에 맞춰 `st.success` 호출을 제거해 일관성을 유지함.
