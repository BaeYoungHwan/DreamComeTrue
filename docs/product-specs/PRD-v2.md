# local-farm-inventory PRD v2 — 정산/리포트 확장

> 버전: v2 | 작성일: 2026-07-18 | 상태: Draft | 기반 문서: [`PRD-v1.md`](PRD-v1.md)

---

## 1. 개요

v1에서 구현된 품목·재고·판매 관리 위에, 실제 농가가 수기 장부(로컬푸드 위탁판매 수수료 정산, 직거래 택배 고객 관리, 규격별 판매 집계)로 관리해온 업무를 시스템 리포트로 옮긴다.

## 2. 문제 정의

v1 MVP는 품목·재고·판매의 기본 흐름을 다루지만, 실제 농장주가 사용 중인 수기 장부 3종(2026-07-18 촬영)을 분석한 결과 다음 업무가 시스템에 반영되어 있지 않다.

- **로컬푸드 매장 위탁판매 정산**: 어양점·평화점·모현점·인화점 등 매장별로 판매누계를 집계하고, 매장 수수료(10~12%, 시기별 변동)를 차감해 예상입금액을 계산한 뒤, 실제 통장입금액과 대조해 오차(예: "6/22 입금분 -880원 오류")를 잡아낸다. 현재 시스템은 이 계산·대사 과정을 전혀 지원하지 않는다.
- **직거래 택배 고객 관리**: 고객명별로 주문일·배송일·규격별 수량(kg)·택배비·입금일을 기록하고 입금 여부를 추적한다. 현재 `sales.buyer`는 자유입력 TEXT일 뿐, 고객 단위 주문 이력이나 입금 상태 개념이 없다.
- **품목 변형(크기×무게)과 가격 관리**: 블루베리 같은 품목은 크기(특/대/중)로 먼저 선별되고, 그 다음 무게(포장단위: 1kg/500g/2kg 등)로 출하되어 하나의 품목이 크기×무게 조합의 여러 "변형"으로 판매된다. 같은 품목이라도 변형에 따라 단가·판매량이 구분되어야 하는데, 현재 시스템은 품목을 단일 규격(unit)으로만 관리하고 판매 시 단가를 매번 수기로 입력해야 해, 변형별 재고 추적과 반복적인 단가 입력 부담을 해결하지 못한다.
- **선입금 주문출하**: 고객에게 선입금을 먼저 받고, 이후 재고가 준비되면 출고하는 주문 방식이 존재한다. 이는 "출고 후 입금을 사후 확인"하는 직거래 택배 흐름과 순서가 반대이며, 현재 시스템에는 이 사전 주문 상태(출고 대기)를 표현할 방법이 없다.

품목이 다양하고 출하 채널이 여러 곳인 다품종 소량 생산 농가 특성상, 이 정산 업무가 여전히 수기로 이루어져 v1이 목표한 "정산 시간 70% 단축"이 실제로는 달성되지 못하고 있다.

## 3. 타겟 유저

v1과 동일 (농장주 본인 및 가족, 단일 사용자).

## 4. 성공 지표 (KPI)

- 채널별 수수료·예상입금액이 자동 계산되어, 정산 시 수기 계산이 불필요
- 예상입금액과 실입금액 차이가 있으면 시스템이 자동으로 표시 (수기 대사 불필요)
- 미입금 직거래 고객을 리스트에서 즉시 확인 가능
- 품목 × 변형(크기×무게)별 판매 현황을 매트릭스로 즉시 확인 가능 (사진1 상단 표 재현)
- 변형별 가격 마스터 설정 후 판매 입력 시 수량만 입력하면 단가·합계가 자동 계산됨

## 5. 완료 기준 (Definition of Done)

사진1·2에 기록된 실제 숫자(모현점 판매누계 293,400원 → 수수료 10% 32,600원 → 입금액 260,800원)를 시스템에 입력했을 때 동일한 정산 결과가 재현되면 Phase 1 완료로 간주한다. Phase 2·3·4도 각각 사진3(직거래 고객 리스트), 사진1 상단(품목×변형 매트릭스), 선입금 주문 접수→출고 완료 전환 시나리오의 실제 데이터로 동일하게 검증한다.

## 6. 기술 스택

변경 없음. Python 3.12 + Streamlit + SQLite (CLAUDE.md 고정 스택 준수, 신규 라이브러리 도입 없음).

## 7. MVP 핵심 기능

### 7-A. 채널·수수료 정산
- [ ] 채널 마스터 관리: 채널명, 유형(위탁판매/직거래), 수수료율(%) 등록·수정
- [ ] 판매 입력 시 채널 선택 (기존 `buyer` 자유입력 대체)
- [ ] 정산 리포트: 채널·기간 선택 → 판매누계 자동 집계 → 수수료율 적용해 수수료·예상입금액 자동 계산
- [ ] 실입금액 수기 입력 필드 → 예상입금액과 차액이 0이 아니면 "입금 오류" 경고 표시

### 7-B. 직거래 택배 고객 관리
- [ ] 직거래 판매 입력 시 고객명, 택배비, 입금 여부, 입금일 기록
- [ ] 고객별 주문 리스트 리포트, "미입금만 보기" 필터, 택배비 합계 표시

### 7-C. 품목 변형(크기×무게) 및 가격 마스터 ✅ 구현 완료
- [x] 품목 마스터에 "변형(variant)" 등록·수정·삭제: 품목 하나에 크기×무게 조합을 여러 개 등록 가능 (예: 블루베리-특-1kg / 블루베리-특-500g / 블루베리-대-2kg)
- [x] 가격 마스터: 변형별 기준 단가 등록·수정
- [x] 입출고(수확) 시 변형 단위로 기록 → 변형별 재고 추적 (품목 전체 합산이 아닌 변형별 재고)
- [x] 판매/출하 시 변형 선택 → 가격 마스터의 단가가 자동으로 채워짐, 수량만 입력하면 합계 자동 계산 (필요 시 그 자리에서 단가 직접 수정 가능 — 가격 변동 대응)
- [x] 품목 × 변형 매트릭스 리포트 (판매량·매출 교차 집계) — 대시보드에 표시
- [ ] 대시보드 품목별 판매 순위에 변형 세분화 옵션 (품목×변형 매트릭스로 대체 — 별도 세분화 옵션은 범위 밖)

### 7-D. 선입금 주문출하 관리 ✅ 구현 완료
- [x] 주문 접수: 고객명, 품목 변형, 수량, 선입금 확인일 기록 → "출고대기" 상태로 저장
- [x] 재고 준비되면 출고 처리 → 재고 차감 및 주문 "출고완료" 전환
- [x] 7-B(직거래 후불 확인, 출고 → 입금 확인 순서)와는 반대 흐름(입금 확인 → 출고 대기 → 출고)이므로 별도 개념으로 구분 관리

> 구현 상세: `docs/exec-plans/active/phase3-4-variants-orders.md` 참조. pytest 88개 통과(AppTest 골든패스 포함), 브라우저 실증은 다른 세션의 브라우저 점유로 보류 중.

## 8. MVP 제외 사항 ⚠️

> Claude는 아래 항목을 임의로 구현하지 않습니다.

- 은행 계좌 자동 연동/실시간 입금 확인 (v2에서도 실입금액은 수기 입력 유지)
- 매장별 프로모션 조건 등 수수료율 자동 판정 로직 (고정 수수료율 필드만 지원)
- 수수료율 변경 이력 관리 (최신 수수료율만 유지, 이력 추적은 v3 이후 검토)
- 변형(variant) 대량 일괄등록 UI (엑셀 업로드 등) — 변형은 한 번에 하나씩 수동 등록
- 변형별 가격 이력 관리 (과거 가격 변동 추적은 제외, 최신 기준 단가만 유지)
- 주문 취소·부분출고 등 복잡한 주문 상태 전이 (주문일·입금일·출고일 정도만 기록, 상태는 "출고대기"/"출고완료" 2단계만 지원)
- v1 제외 사항 전체 유지: 회원권한 관리, 바코드/QR, 세무증빙 자동발급, 외부 쇼핑몰 연동, 한글(.hwp) Export

> **v1 결정 변경**: v1에서는 "품목 고정 단가 없음, 출하 시마다 직접 입력"으로 결정했으나(가격 변동이 잦은 로컬 출하 특성 고려), 이번 버전부터는 변형별 기준 단가를 가격 마스터에 미리 설정해 자동으로 채우되 판매 시점에 직접 수정도 허용하는 방식으로 대체한다. 완전히 고정된 단가는 아니며, 반복 입력 부담을 줄이는 것이 목적이다.

## 9. 제약사항

- **DB 스키마 변경 시 마이그레이션 코드 필수 제공** (CLAUDE.md 프로젝트 규칙). 기존 `sales.buyer` 자유입력 데이터는 삭제하지 않고 보존한 채, 신규 채널/변형 컬럼을 추가하는 `ALTER TABLE` 방식으로 진행한다.
- 기존 `sales` 레코드는 채널 미지정(NULL) 상태로 남을 수 있으므로, 리포트 집계 시 "미분류" 그룹으로 별도 표시한다.
- 인터넷 연결 불안정 환경에서도 동작 (로컬 우선), 외부 유료 API 의존성 없음 — v1과 동일.
- UI는 텍스트 큼직하게, 복잡한 디자인 프레임워크 배제.

## 10. DB 스키마 변경안 (초안)

```sql
-- 신규: 채널(출하처) 마스터
CREATE TABLE IF NOT EXISTS channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    channel_type TEXT NOT NULL CHECK(channel_type IN ('consignment', 'direct')),
    commission_rate REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 기존 sales 테이블 확장 (컬럼 추가, 기존 데이터 보존)
ALTER TABLE sales ADD COLUMN channel_id INTEGER REFERENCES channels(id);
ALTER TABLE sales ADD COLUMN shipping_fee REAL;
ALTER TABLE sales ADD COLUMN payment_status TEXT DEFAULT '미입금' CHECK(payment_status IN ('입금완료', '미입금'));
ALTER TABLE sales ADD COLUMN paid_at TEXT;

-- 신규: 채널별 정산 기록 (기간 단위 대사 결과 저장)
CREATE TABLE IF NOT EXISTS settlements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id INTEGER NOT NULL REFERENCES channels(id),
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,
    sales_total REAL NOT NULL,
    commission_amount REAL NOT NULL,
    expected_deposit REAL NOT NULL,
    actual_deposit REAL,
    deposit_date TEXT,
    memo TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 신규: 품목 변형(크기×무게 조합) 마스터 겸 가격 마스터 (7-C)
CREATE TABLE IF NOT EXISTS item_variants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL REFERENCES items(id),
    size TEXT,               -- 크기/등급 (예: 특, 대, 중)
    weight TEXT,              -- 무게/포장단위 (예: 1kg, 500g, 2kg)
    default_price REAL,       -- 가격 마스터: 변형별 기준 단가
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- stock_transactions/sales에 variant_id 추가 (NULL 허용 — 변형 미사용 기존 데이터 호환)
ALTER TABLE stock_transactions ADD COLUMN variant_id INTEGER REFERENCES item_variants(id);
ALTER TABLE sales ADD COLUMN variant_id INTEGER REFERENCES item_variants(id);

-- 신규: 선입금 주문 (7-D)
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    variant_id INTEGER NOT NULL REFERENCES item_variants(id),
    customer_name TEXT NOT NULL,
    quantity REAL NOT NULL CHECK (quantity > 0),
    deposit_confirmed_at TEXT,
    status TEXT NOT NULL DEFAULT '출고대기' CHECK (status IN ('출고대기', '출고완료')),
    shipped_stock_transaction_id INTEGER REFERENCES stock_transactions(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

기존 `sales.buyer` 컬럼은 유지하되(하위 호환), 신규 입력부터는 `channel_id`를 필수로 받도록 UI에서 유도한다. 기존 레코드의 `buyer` 텍스트를 신규 `channels`로 수동 매핑할지는 13번 미결 사항 참조.

등급(특/대/중)은 당초 `sales.grade` 컬럼으로 검토했으나, 품목 변형(`item_variants.size`)으로 흡수되어 별도 컬럼을 두지 않는다 — 판매 시 `variant_id`를 통해 크기·무게 정보를 얻는다.

## 11. 화면 설계 개요

- **채널 관리 화면** (신규): 채널명·유형·수수료율 등록/수정 리스트
- **정산 리포트 화면** (기존 `src/export/report.py` 확장): 채널 선택 → 기간 지정 → 판매누계/수수료/예상입금액 자동 표시 → 실입금액 입력 → 차액 경고
- **직거래 고객 리포트 화면** (신규): 고객별 주문 리스트, 미입금 필터, 택배비 합계
- **품목 변형·가격 마스터 화면** (신규, 품목 관리 화면 확장): 품목별 변형(크기×무게) 등록/수정/삭제, 변형별 기준 단가 설정
- **품목×변형 매트릭스 화면** (신규 또는 대시보드 확장): 사진1 상단 표 형태의 교차 집계 테이블
- **선입금 주문 관리 화면** (신규): 주문 접수(고객명·변형·수량·입금확인일), 출고대기 목록, 출고 처리 버튼

## 12. Phase 분할

| Phase | 목표 | 예상 산출물 |
|-------|------|-------------|
| Phase 1 | 채널·수수료 정산 (7-A) | `channels`/`settlements` 테이블, 마이그레이션, 정산 리포트 확장 |
| Phase 2 | 직거래 고객 관리 (7-B) | `sales` 컬럼 확장(shipping_fee/payment_status/paid_at), 고객별 리포트 화면 |
| Phase 3 | 품목 변형·가격 마스터 (7-C) | `item_variants` 테이블, `stock_transactions`/`sales.variant_id`, 변형별 재고·가격 자동계산, 품목×변형 매트릭스 |
| Phase 4 | 선입금 주문출하 (7-D) | `orders` 테이블, 주문 접수/출고 처리 화면 |

## 13. 미결 사항

| 질문 | 결정권자 | 기한 |
|------|----------|------|
| 기존 `sales.buyer` 자유입력 데이터를 신규 `channels` 마스터로 자동 매핑할지, 수동 정리할지 | 농장주(사용자) | Phase 1 착수 전 |
| 수수료율이 시기별로 바뀐 이력(사진1: 10%→12%)을 이력 관리할지, 최신값만 유지할지 | 농장주(사용자) | Phase 1 착수 전 |
| Phase 착수 시점 (바로 이어서 진행 vs 별도 세션) | 농장주(사용자) | 미정 |
| `item_variants`/`orders` 마이그레이션을 채널·정산용 마이그레이션과 같은 `migrations.py` 러너에 이어붙일지, 버전 번호를 어떻게 조율할지 | 농장주(사용자) | Phase 3 착수 전 |
| 변형(variant) 없이 등록된 기존 품목/거래 데이터 호환 처리 (variant_id NULL 허용으로 충분한지) | 농장주(사용자) | Phase 3 착수 전 |
| 가격 마스터의 기준 단가를 수정하면 과거 판매 기록에도 영향 주는지, 이후 신규 판매에만 적용되는지 | 농장주(사용자) | Phase 3 착수 전 |
