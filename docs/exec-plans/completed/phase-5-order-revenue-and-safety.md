# Phase 5 — 실배포 전 6개 항목 (선입금 주문 매출 반영·택배비·삭제 안전장치·정산 이력)

> 출처: .claude/plans/1-wobbly-creek.md
> 생성: 2026-07-22
> BASE_COMMIT: 6a71fbb1cfc5b5cbe40636ce3c483d97b069f35b

## 목표

실제 고객(농장주) 배포 전 발견된 두 핵심 갭 — 선입금 주문 출고 매출이 정산 리포트/대시보드에 전혀 반영되지 않는 문제, 택배비 미추적 — 을 해결하고, 삭제 버튼 안전장치와 정산 확정 이력 조회 UI를 추가한다.

## 태스크

- [x] B. 택배비(`shipping_fee`) 필드 추가 (migrations 004, orders.py, app.py 주문 폼)
- [x] A. 선입금 주문 출고 → 매출(sales) 자동 반영 (`_insert_sale_row` 리팩터링, `ship_order` 연결)
- [x] D. 정산 확정 이력 조회 UI (`list_settlements` 화면 노출)
- [x] C. 삭제 시 체크박스 확인 절차 (5곳: 변형/거래/판매/품목/채널)
- [x] E. 실사용 데이터 UI 재입력 검증 (KakaoTalk_20260718_153253473_02.jpg 전체 — 대표 건은 실제 UI 폼으로, 나머지는 UI와 동일한 백엔드 함수로 입력)
- [x] F. 회귀 QA (pytest 105개 통과 + 브라우저 재확인)

## 검증 기준

1. `python -m pytest -q` 전체 통과 (신규 테스트: migrations 004, ship_order의 sales 반영·재고 1회만 차감, record_sale 리팩터링 회귀 없음)
2. `streamlit run app.py` 실행 후 chrome-devtools로: 선입금 주문 출고 처리 → 대시보드/정산리포트에 매출 반영 확인, 정산 리포트 탭 "정산 이력" 섹션 표시, 5곳 삭제 버튼 체크박스 미체크 시 비활성 확인
3. `data/farm.db`를 실제 장부 기준으로 재시딩 후 정산 리포트 합계가 사진 누계와 근사하게 맞는지 육안 대조
