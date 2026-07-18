# Phase 1 — MVP 핵심 기능

## 목표
품목 등록(커스텀 속성 포함), 입출고/폐기 관리, 판매 관리, 대시보드, 기간별 정산 리포트 + 엑셀 Export를 TDD로 구현하고 Streamlit UI로 연결한다.

## 작업 목록

- [x] `src/inventory/items.py` — 품목 등록/조회/커스텀 속성 추가삭제/삭제
- [x] `src/inventory/stock.py` — 입고/출고/폐기 거래 기록, 재고 계산, 음수 재고 방지
- [x] `src/sales/sales.py` — 판매 기록 (출고 거래 + 매출 레코드)
- [x] `src/dashboard/dashboard.py` — 오늘 출하 현황 / 이달 누적 매출 / 품목별 판매 순위
- [x] `src/export/report.py` — 기간별 정산 리포트 집계 + 엑셀(.xlsx) 생성 (정산 리포트용 + 전체 데이터 백업용)
- [x] `app.py` — 품목관리/입출고/판매/대시보드/정산리포트 5개 탭 UI로 연결
- [x] pytest 전체 통과 확인 (29개) + 브라우저로 골든 패스 실전 확인

## 완료 기준 (PRD 4-1 참조)
품목 등록 → 입고 → 출고 → 폐기/손실 반영 → 매출 정산 → 대시보드 확인 시나리오가 오류 없이 1회 정상 동작. — chrome-devtools로 실제 브라우저에서 전 과정 확인 완료.
추가 기능(커스텀 속성, 엑셀 Export, 기간별 정산 리포트)도 각각 오류 없이 1회 동작. — 정산 리포트 엑셀 + 전체 데이터 백업 엑셀 다운로드 후 openpyxl로 내용 검증 완료.

## 브라우저 검증 중 발견 및 수정한 버그
- `sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread.`
  Streamlit이 재실행마다 다른 스레드를 쓰는데 `st.cache_resource`로 커넥션을 재사용해 발생.
  → `src/core/db.py`의 `get_connection()`에 `check_same_thread=False` 추가로 해결.
  (pytest/AppTest는 단일 스레드에서 실행되어 이 문제를 잡지 못했음 — 실브라우저 검증의 필요성을 보여준 사례)
