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

## P2 — 검증 및 배포

- [ ] E2E 테스트 작성 (완료 기준 시나리오: 품목등록 → 입고 → 출고 → 폐기 → 정산 → 대시보드, 1회 정상 동작 확인)
- [ ] 엑셀 Export / 커스텀 속성 추가·삭제 / 기간별 정산 리포트 각각 1회 정상 동작 확인
- [ ] 농장 내 PC 로컬 배포 (또는 Streamlit Community Cloud 검토)
- [ ] KPI 측정 기준 설정 (수기 장부 대비 기록 시간 단축 체감 확인)

---

## 일정 메모

- MVP 목표: 다음주 안으로 개발 완성 (2026-07-18 기준 → 2026-07-25 목표)
