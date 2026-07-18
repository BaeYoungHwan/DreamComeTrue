# Phase 0 — 기반 구축

## 목표
local-farm-inventory 앱의 최소 골격(폴더 구조, SQLite 스키마, 자동 백업, Streamlit Hello World)을 TDD로 구축한다.

## 작업 목록

- [x] SQLite 스키마 초안 (`src/core/db.py`) — items/stock_transactions/sales 테이블
- [x] 자동 백업 스크립트 초안 (`src/core/backup.py`)
- [x] Streamlit Hello World (`app.py`)
- [x] pytest 전체 통과 확인 + `streamlit run app.py` 구동 확인

## 완료 기준
- `pytest` 전체 통과 — 8개 테스트 모두 PASSED
- `streamlit run app.py` 실행 시 오류 없이 "로컬 팜 인벤토리" 타이틀 표시 — HTTP 200 확인 완료
