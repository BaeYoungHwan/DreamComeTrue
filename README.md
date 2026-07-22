# 로컬 팜 인벤토리 (local-farm-inventory)

> 1000평 규모 다품종 소량 생산 농가를 위한 로컬 출하용 재고 관리 및 매출 정산 시스템.
> 인터넷 연결이 불안정한 농장 환경에서도 동작하도록 **로컬 PC 실행 + SQLite** 구조로 만들었습니다.

---

## 무엇을 하는 앱인가

- 다품종 농작물의 **품목/변형(크기·무게)별 재고**를 수확·출고·폐기 단위로 추적
- 출하처(로컬푸드 매장, 직거래 등)별 **판매·매출 기록** 및 수수료 정산
- 선입금 주문(고객명·품목·입금확인 → 출고대기 → 출고완료) 관리
- 오늘 출하 현황, 이달 누적 매출, 품목별 판매 순위를 보여주는 대시보드
- 기간별 정산 리포트 + 엑셀(.xlsx) Export

단일 사용자(농장주 본인) 전용으로 설계되었으며, 회원가입/권한 관리, 바코드 스캔, 외부 쇼핑몰 연동 같은 기능은 MVP 범위에서 의도적으로 제외했습니다.

---

## 기술 스택

- **Python 3.12**
- **Streamlit** — UI
- **SQLite** — 로컬 DB (`data/farm.db`, 외부 서버 전송 없음)
- **openpyxl** — 엑셀 Export
- **pytest** — 테스트

다른 라이브러리·프레임워크는 도입하지 않습니다 (`requirements.txt` 고정).

---

## 실행 방법

### 농장 PC (배포 대상, 권장)

Python·Git 설치 후 저장소를 내려받고 `앱_업데이트.bat` → `앱_실행.bat`을 더블클릭하면 됩니다.
상세 절차는 [`docs/deployment/farm-pc-guide.md`](docs/deployment/farm-pc-guide.md) 참고.

```
git clone https://github.com/BaeYoungHwan/DreamComeTrue.git 로컬팜인벤토리
```

### 개발 환경

```bash
pip install -r requirements.txt
streamlit run app.py
```

브라우저가 자동으로 열리지 않으면 `http://localhost:8501`로 접속하세요.

---

## 데이터 & 백업

- 실제 데이터: `data/farm.db` (이 PC에만 저장, 외부 전송 없음)
- 실행할 때마다 `backups/` 폴더에 시점별 자동 백업 생성 (`src/core/backup.py`)
- DB 스키마 변경은 `PRAGMA user_version` 기반 마이그레이션으로 관리 (`src/core/migrations.py`)

---

## 프로젝트 구조

```
DreamComeTrue/
├── app.py                     # Streamlit 진입점 (탭 구성)
├── 앱_실행.bat / 앱_업데이트.bat  # 농장 PC용 실행/업데이트 스크립트
├── src/
│   ├── core/                  # DB 연결, 스키마, 마이그레이션, 백업
│   ├── inventory/             # 품목·변형·재고(입출고/폐기)
│   ├── sales/                 # 판매·매출 기록
│   ├── settlement/            # 채널(출하처) 관리, 수수료 정산
│   ├── orders/                # 선입금 주문 관리
│   ├── dashboard/             # 대시보드 집계
│   └── export/                # 엑셀 리포트 Export
├── tests/                     # pytest (AppTest 골든패스 포함)
└── docs/
    ├── product-specs/         # PRD-v1, PRD-v2
    ├── design-docs/           # 아키텍처·ARD
    ├── deployment/            # 농장 PC 배포 가이드
    └── exec-plans/            # Phase별 실행 계획 (completed/)
```

---

## 테스트

```bash
pytest
```

품목 등록 → 입고 → 출고 → 폐기 → 판매 → 정산 리포트 → 대시보드로 이어지는 골든패스 E2E를 포함해 전체 스위트가 통과해야 합니다.

---

## 개발 현황

현재 P0(기반 구축)~P2(검증 및 배포)까지 완료된 상태입니다. 세부 진행 내역은 [`TODO.md`](TODO.md), 기획 배경은 [`docs/product-specs/PRD-v1.md`](docs/product-specs/PRD-v1.md) / [`docs/product-specs/PRD-v2.md`](docs/product-specs/PRD-v2.md)를 참고하세요.

이 프로젝트는 Claude Code 하네스 템플릿을 기반으로 개발되었습니다 — 보안 훅, 자동화 스킬, 에이전트 구성은 [`CLAUDE.md`](CLAUDE.md)를 참고하세요.
