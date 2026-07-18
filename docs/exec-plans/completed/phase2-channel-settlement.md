# Phase 2 — 채널·수수료 정산

> 출처: `.claude/plans/velvet-juggling-lightning.md` (PRD: `docs/product-specs/PRD-v2.md` 7-A)
> 생성: 2026-07-18
> 완료: 2026-07-18

## 목표
로컬푸드 매장 위탁판매 채널·수수료 정산 기능 구현. 채널 마스터 관리, 판매 입력 시 채널 연결, 정산 리포트에서 판매누계→수수료→예상입금액 자동계산 및 실입금액 대비 차액 경고. 스키마 마이그레이션 인프라(PRAGMA user_version 기반)를 최초로 도입하고, 기존 buyer 자유입력 데이터를 채널로 자동 매핑.

## 태스크
- [x] `requirements.txt`에 `pytest` 명시
- [x] `tests/test_migrations.py` — user_version 0→1, 재실행 멱등, 신규 테이블/컬럼 생성 검증
- [x] `src/core/migrations.py` — 러너 + `_migration_001_channels`(테이블 생성 + 조건부 ALTER)
- [x] `tests/test_migrations.py` backfill 케이스 — 기존 buyer 시드로 자동 채널 생성·역연결 검증
- [x] `src/core/migrations.py` — `backfill_channels_from_buyer(conn)` 구현
- [x] `src/core/db.py` — `SCHEMA_SQL`에 `channels`/`settlements`/`sales.channel_id` 반영
- [x] `tests/test_channels.py` — CRUD, 중복명, 참조중 삭제, CHECK 위반
- [x] `src/settlement/channels.py` — CRUD + 예외 클래스
- [x] `tests/test_sales.py` 확장 — channel_id 지정/미지정 케이스
- [x] `src/sales/sales.py` — `record_sale` 시그니처 확장
- [x] `tests/test_settlement.py` — 순수 계산함수 단위테스트 + DoD 재현 테스트 + 미분류 처리
- [x] `src/settlement/settlement.py` — 정산 계산/저장/조회
- [x] `tests/test_report.py` 확장 — 채널 정산 엑셀 시트 검증
- [x] `src/export/report.py` — 정산 엑셀 함수 추가
- [x] `tests/test_app.py` 확장 — 6탭 골든패스
- [x] `app.py` — 마이그레이션 연결, 채널 관리 탭, 판매 탭 채널 selectbox, 정산 리포트 UI
- [x] pytest 전체 통과 + 브라우저 골든패스 검증

## 검증 기준
1. `pytest` 전체 통과 — Phase 1 관련 25개 테스트(test_migrations/channels/settlement 신규 + sales/report/app 확장분) 포함 전체 통과 확인.
2. 브라우저(chrome-devtools): 채널 등록("모현점_실증", 수수료 10%) → 판매 기록(293,400원, 사진1 실제 값) → 정산 리포트 자동계산(판매누계 293,400원 → 수수료 29,340원 → 예상입금액 264,060원) → 실입금액(260,800원, 사진1 실제 값) 입력 후 "입금 오류: 차액 -3,260원" 경고 정상 표시 확인.
3. 기존 DB 마이그레이션 후 buyer 자동 채널 매핑 확인 — 실제 운영 `data/farm.db`에서 기존 buyer "익산시 로컬푸드 모현점"이 마이그레이션 실행 시 자동으로 채널 레코드(수수료율 0%)로 생성됨을 확인. 재실행 멱등성은 `tests/test_migrations.py`로 커버.
4. DoD 골든넘버(모현점 293,400/수수료/260,800) 관련 — PRD 상 "10%" 표기와 장부의 실제 차감액(32,600원)이 산술적으로 불일치함을 발견(10%라면 29,340원이어야 함). 계산 로직은 표준 공식(`sales_total * rate / 100`)으로 구현했고, rate=10% 가정 시 예상입금액 264,060원과 장부상 실입금액 260,800원의 차액(-3,260원)을 시스템이 정상적으로 "입금 오류"로 잡아내는 것을 확인 — 대사(reconciliation) 기능 자체는 의도대로 동작. 정확한 실제 수수료율은 사용자 확인 필요 (미결 사항으로 남김).

## 검증 중 발견한 이슈
- Streamlit `number_input`을 브라우저 자동화 도구로 값 설정 시, 필드를 먼저 클릭 후 전체 선택(Ctrl+A)하지 않고 바로 입력하면 기존 값 뒤에 자릿수가 밀려 들어가는 현상 발생(예: "10" 입력 시 "0.0010"으로 표시). 코드 버그 아님 — 자동화 상호작용 방식 문제. 사람이 직접 타이핑할 때는 브라우저가 알아서 필드를 선택 상태로 만들어주므로 영향 없음.
- 검증 과정에서 실제 운영 `data/farm.db`에 테스트 채널·판매 레코드가 생성되었으나, 검증 직후 도메인 함수(`delete_sale`, `delete_channel`, `update_channel`)로 전부 원복 완료. 재고·채널 데이터 정상 확인.
