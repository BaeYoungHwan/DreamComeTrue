# 품질 등급 추적

도메인별 코드 품질 등급을 기록합니다. Phase 완료 시 업데이트.

---

## 등급 기준

| 등급 | 설명 |
|------|------|
| A | 테스트 커버리지 80%+, 문서 최신, 레이어 위반 없음 |
| B | 테스트 60%+, 문서 대체로 최신 |
| C | 테스트 40%+, 문서 일부 오래됨 |
| D | 테스트 미흡, 문서 불일치 다수 |
| F | 테스트 없음 또는 빌드 실패 |

---

## 도메인별 현황

| 도메인 | 등급 | 테스트 커버리지 | 마지막 검토 | 비고 |
|--------|------|----------------|-------------|------|
| core (db/backup) | A | 테스트 7개, 스키마·백업 로직 전체 커버 | 2026-07-18 | Phase 0 완료 (`src/core/db.py`, `src/core/backup.py`) |
| inventory (items/stock) | A | 테스트 12개, 커스텀 속성·재고 계산·음수 방지 전체 커버 | 2026-07-18 | Phase 1 완료 (`src/inventory/items.py`, `src/inventory/stock.py`) |
| sales | A | 테스트 3개, 출고 연동·매출 계산·재고 부족 예외 커버 | 2026-07-18 | Phase 1 완료 (`src/sales/sales.py`) |
| dashboard | A | 테스트 3개, 오늘 출하·이달 매출·순위 집계 커버 | 2026-07-18 | Phase 1 완료 (`src/dashboard/dashboard.py`) |
| export (report) | A | 테스트 3개, 기간 집계·엑셀 생성 커버 + 브라우저 실다운로드 검증 | 2026-07-18 | Phase 1 완료 (`src/export/report.py`) |
| app (Streamlit UI) | A | AppTest 7개 (탭 구조, v1 핵심 골든패스, 채널·정산 골든패스, 변형·주문 골든패스, 전체채널요약, 커스텀 속성 추가·삭제) | 2026-07-21 | 스레드 버그(`check_same_thread`) 발견·수정. AppTest가 실제 운영 DB를 오염시키던 버그 수정(`FARM_DB_PATH` 격리) |
| core.migrations | A | 테스트 12개, 버전 0→3 순차 마이그레이션·멱등성·백필 전체 커버 | 2026-07-18 | `src/core/migrations.py` (다른 세션 001 + 이번 세션 002/003) |
| settlement (channels/settlement) | A | 테스트 다수, CRUD·정산 계산·차액 대사 커버 | 2026-07-18 | `src/settlement/` (다른 세션 구현, PRD-v2 7-A) |
| inventory.variants | A | 테스트 5개, 변형 CRUD·삭제 차단(VariantInUseError) 커버 | 2026-07-18 | PRD-v2 7-C 완료 (`src/inventory/variants.py`) |
| orders | A | 테스트 6개, 주문 생성·조회·출고 처리·중복 출고 차단 커버 | 2026-07-18 | PRD-v2 7-D 완료 (`src/orders/orders.py`) |

---

## 업데이트 절차

1. Phase 완료 시 테스트 커버리지 측정
2. `doc-gardener` 에이전트로 문서 상태 확인
3. 위 표 업데이트 후 커밋

---

## 목표

| 기간 | 목표 |
|------|------|
| MVP | 핵심 도메인 B 이상 |
| v1.0 | 전체 도메인 B 이상 |
| 안정화 | 핵심 도메인 A |
