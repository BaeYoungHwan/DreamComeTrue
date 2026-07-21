# TODO — local-farm-inventory

> 워크플로우: `[ ]` 대기 → `[🔄]` 진행 중 → `[x]` 완료
> 재시작 시: `docs/ref/session-state.md` 확인 후 `[🔄]` 항목부터 재개

---

## 시작 전

- [x] `/init-project` 실행 완료
- [ ] `docs/design-docs/architecture-v1.md` 검토 및 확정
- [ ] `docs/design-docs/ARD-v1.md` 비기능 요건 확정
- [ ] Phase 분할 후 `docs/exec-plans/active/`에 실행 계획 생성

---

## P0 — 기반 구축

- [x] 레포 초기화 및 폴더 구조 생성 (src/core/, tests/ 등 — src/inventory·sales·dashboard·export는 P1에서 실제 코드 추가 시 생성)
- [x] Python 3.12 + Streamlit + SQLite 설치 및 Hello World 확인 (`app.py`, `pytest`/`AppTest`로 검증)
- [x] SQLite 스키마 초안 작성 (품목, 재고, 판매 테이블 — `src/core/db.py`)
- [x] SQLite 자동 백업 스크립트 초안 (`src/core/backup.py`)

---

## P1 — MVP 핵심 기능

- [x] 품목 등록 및 관리 (농작물 이름, 규격 kg/박스 등 등록) — `src/inventory/items.py`
- [x] 입출고(재고) 관리 (수확/출고/폐기 3종 거래, 음수 재고 방지, 재고 = 입고 − 출고 − 폐기) — `src/inventory/stock.py`
- [x] 폐기·손실 수량 입력 및 재고 반영
- [x] 판매 및 매출 관리 (출하처별 판매 수량·단가 입력, 품목 고정 단가 없음) — `src/sales/sales.py`
- [x] 간이 대시보드 (오늘 출하 현황, 이달 누적 매출, 품목별 판매 순위 그래프) — `src/dashboard/dashboard.py`
- [x] 품목별 커스텀 속성 추가·삭제 UI (JSON 컬럼 기반, 품목마다 다른 속성 지원) — `items.py` + `app.py` 품목 관리 탭
- [x] 엑셀(.xlsx) Export 기능 (재고·판매 데이터) — `src/export/report.py`
- [x] 기간별 정산 리포트 (시작일~종료일 지정, 품목별 출하량·판매대금 집계 + 엑셀 출력)

---

## P1.1 — 실사용 시뮬레이션 피드백 수정

> 부모님 실사용 시뮬레이션에서 발견된 5건. 상세 원인·수정 내역은 `docs/exec-plans/completed/p1.1-simulation-fixes.md` 참조.

- [x] 대시보드·정산 리포트 표 헤더 영어 → 한글 (`품목`/`수량`/`출하량`/`판매대금`), 커스텀 속성 dict 표시 → 목록형
- [x] 거래·판매 기록이 있는 품목 삭제 시 크래시 → 차단 + 안내 메시지 (`ItemInUseError`)
- [x] 입출고·판매 탭에 날짜 입력란 추가 (`occurred_on`/`sold_on` 파라미터)
- [x] 정산 리포트 탭 — 엑셀 다운로드 클릭 시 표·금액이 사라지는 버그 → `st.session_state` 리팩터링 (전체 데이터 백업 버튼도 동일 버그 함께 수정)
- [x] 품목 커스텀 속성 안내문구·placeholder 추가
- [x] 입출고·판매 개별 내역 조회·삭제 기능 추가 (기록이 있어 삭제 차단된 품목도 내역 삭제 후 품목 삭제 가능) — `list_transactions`/`delete_transaction`, `list_sales`/`delete_sale`

---

## P1.2 — 채널·수수료 정산 (PRD-v2 7-A)

> 수기 장부(로컬푸드 위탁판매 정산) 분석 기반 확장. 상세 내역은 `docs/exec-plans/completed/phase2-channel-settlement.md`, 기획은 `docs/product-specs/PRD-v2.md` 참조.

- [x] 스키마 마이그레이션 인프라 신설 (`PRAGMA user_version` 기반, `src/core/migrations.py`)
- [x] 채널(출하처) 마스터 CRUD + 기존 `sales.buyer` 자동 매핑 백필 — `src/settlement/channels.py`
- [x] 판매 기록에 채널 연결 (`sales.channel_id`) — `src/sales/sales.py`
- [x] 채널별 정산 계산(판매누계·수수료·예상입금액) + 실입금액 대사(차액 경고) — `src/settlement/settlement.py`
- [x] 채널 정산 엑셀 Export — `src/export/report.py`
- [x] `app.py`에 "채널 관리" 탭 신설, 판매 탭 채널 선택 UI, 정산 리포트 탭 채널별 정산 섹션 추가
- [x] 브라우저 실증: 사진1 실제 장부 값(판매누계 293,400원 → 수수료 29,340원 → 예상입금액 264,060원 vs 실입금 260,800원)으로 입금 오류 경고 재현 확인
- [x] 전체 채널 정산 요약 — 매장별로 하나씩 조회하지 않고 등록된 모든 채널을 한 화면·엑셀로 비교 (`all_channels_settlement`, `all_channels_settlement_to_excel_bytes`)

---

## P1.3 — 품목 변형(크기×무게)·가격 마스터 + 선입금 주문출하 (PRD-v2 7-C, 7-D)

> 상세 내역은 `docs/exec-plans/active/phase3-4-variants-orders.md`, 기획은 `docs/product-specs/PRD-v2.md` 참조.

- [x] `item_variants`(품목 변형+가격 마스터), `orders`(선입금 주문) 테이블 + 마이그레이션(002/003) — `src/core/db.py`, `src/core/migrations.py`
- [x] 품목 변형 CRUD (크기×무게, 기준 단가) — `src/inventory/variants.py`
- [x] 입출고·판매에 변형별 재고 추적 (`current_stock`/`record_transaction`/`record_sale`에 `variant_id`)
- [x] 판매 탭에서 변형 선택 시 기준 단가 자동 입력 (직접 수정 가능)
- [x] 선입금 주문 관리(고객명·변형·수량·입금확인일 → 출고대기 → 출고완료) — `src/orders/orders.py`
- [x] 대시보드 품목×변형 매트릭스 — `src/dashboard/dashboard.py`
- [x] `app.py`에 "선입금 주문" 탭 신설, 품목 관리 탭에 변형·가격 관리 UI
- [x] pytest 88개 전체 통과 (AppTest 골든패스: 품목→변형/가격 등록→입고→주문접수→출고처리)
- [x] 골든패스 검증 (AppTest + 인접 기능 실브라우저 검증으로 충분히 확인, 이후 세션에서 chrome-devtools 연결 해제됨)

---

## P1.4 — QA 피드백 반영 (`시뮬레이션 피드백.txt`)

> 실사용 QA(사진 속 로컬푸드 정산 장부를 데모 데이터로 재현해 직접 앱 실행) 중 발견된 5건. 계획은 `.claude/plans/fluttering-growing-heron.md` 참조.

- [x] 재고 단위 표시 공백 버그 수정 (`app.py` 변형재고/입출고내역/판매내역 3곳, 예: "3.96500g" → "3.96 500g")
- [x] 정산 리포트에 "상세 리포트" 추가 — 품목별 합산 외에 날짜별 개별 판매 건 조회 + 엑셀 다운로드 (`detailed_period_report`, `detailed_report_to_excel_bytes` — `src/export/report.py`)
- [x] 가격 입력 소수점 제거 — 변형 기준단가/판매 단가/실제 통장입금액 `number_input`을 정수 전용(`format="%d"`)으로 변경
- [x] 커스텀 속성(당도·재배방식 등 자유 메모) UI 제거 — 실사용에서 용도 불명확. DB 컬럼·백엔드 함수는 유지(스키마 변경 없음, 추후 필요시 UI만 재부착 가능)
- [x] "재고 현황" 탭 신설 (첫 번째 탭) — 전체 품목×변형의 현재 재고를 한 화면에서 조회 (`stock_overview` — `src/inventory/stock.py`)
- [x] pytest 99개 전체 통과 (신규 8개: 상세 리포트 2, 재고 현황 2, 앱 골든패스 2, 탭 개수 갱신 1, 커스텀 속성 테스트 제거 1)

---

## P2 — 검증 및 배포

- [x] E2E 테스트 작성 (완료 기준 시나리오: 품목등록 → 입고 → 출고 → 폐기 → 판매 → 정산 리포트 → 대시보드, 1회 정상 동작 확인) — `test_v1_core_golden_path_register_stock_sale_report_dashboard`
- [x] 엑셀 Export / 커스텀 속성 추가·삭제 / 기간별 정산 리포트 각각 1회 정상 동작 확인 — chrome-devtools 연결 해제로 실브라우저 대신 AppTest 골든패스로 검증. 기간별 정산 리포트·엑셀 다운로드(정산 리포트/전체 채널 정산)는 기존 골든패스가 `st.session_state` 경로를 통해 이미 실제로 실행·검증 중이었음을 확인. 커스텀 속성 추가·삭제만 UI 레벨 테스트가 없어 `test_custom_attribute_add_and_delete_golden_path` 신규 추가 (`tests/test_app.py`). pytest 94개 전체 통과
- [x] 농장 PC 로컬 배포 준비 — 외부 URL(Streamlit Cloud 등) 대신 로컬 실행 방식으로 결정 (SQLite 비영구 저장소 위험 + 농장 인터넷 불안정 문제 때문). `앱_실행.bat`/`앱_업데이트.bat` + `docs/deployment/farm-pc-guide.md` 작성 완료. 실제 농장 PC 설치는 사용자가 가이드대로 진행
- [x] KPI 측정 기준 설정 — 스톱워치 등 시간 측정 기능은 과설계로 판단해 앱에 추가하지 않고, 농장 PC 배포 후 2주 실사용 시점에 농장주에게 "확실히 빨라졌다/비슷하다/더 불편하다" 3단계 구두 체감 확인으로 대체. 상세 기준은 `docs/product-specs/PRD-v1.md` 4-2절 참조

---

## 일정 메모

- MVP 목표: 다음주 안으로 개발 완성 (2026-07-18 기준 → 2026-07-25 목표)
