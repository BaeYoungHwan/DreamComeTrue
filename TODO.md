# TODO — claude-code-template 유지보수

> 범례: [ ] 미착수  [🔄] 진행 중  [x] 완료
> 재시작 시: docs/ref/session-state.md 확인 후 [🔄] 항목부터 재개
> 자세한 워크플로우: [docs/ref/todo-workflow.md](docs/ref/todo-workflow.md)

---

## 당장 첫 단계

- [ ] /init-project 실행 후 CLAUDE.md 플레이스홀더 채우기 + PRD 작성 시작

---

## P0 — 분석 & 피드백 [최우선 작업]

- [x] [섹션1] 8개 스킬 사용처 및 분석 완료 — skill-guide.md 불필요 확인

### 2. 에이전트 시스템 재설계

- [ ] [에이전트1] agents/security-reviewer.md 신규 작성
      레인: Review Lane | 모델: sonnet
      역할:
        - OWASP Top 10 체크리스트 (SQLi, XSS, IDOR, 인증 취약점 등)
        - 비밀키/자격증명 하드코딩 탐지 (.env 누락, API 키 직접 삽입)
        - code-reviewer와 역할 분리: code-reviewer=로직·품질, security-reviewer=보안만
      생성 조건: /init-project 인터뷰에서 "배포 예정" or "민감 데이터 처리" 선택 시
      출력 형식: 🔴 위험 (즉시 수정) / 🟡 경고 (권장) / 🟢 통과

- [ ] [에이전트2] agents/_templates/ 폴더 + domain-agent.tpl.md 작성
      위치: agents/_templates/domain-agent.tpl.md (신규 폴더 포함)
      역할: /init-project가 프로젝트 테마에 맞게 복사+치환하여 실제 도메인 에이전트 생성
      플레이스홀더:
        {{DOMAIN_NAME}}   — 도메인명 (auth, payment 등)
        {{DOMAIN_DESC}}   — 도메인 한 줄 설명
        {{DOMAIN_RULES}}  — 도메인별 비즈니스 규칙
        {{DOMAIN_FILES}}  — 담당 파일/모듈 경로
      예시 도메인 주석 포함 (웹앱/E-Commerce/AI-ML 매핑)

- [ ] [에이전트3] agents/example-agent.md 삭제
      삭제 사유: _templates/ 방식으로 역할 이전됨
      선행 조건: [에이전트4] LANES.md 갱신 완료 후 진행

- [ ] [에이전트4] agents/LANES.md 갱신
      수정 내용:
        1. 에이전트 생성 기준 섹션 추가 (인터뷰 기반, SCALE 비종속)
           "code-reviewer: 항상 / security-reviewer: 배포·민감데이터 시 / 도메인: 테마 선택 시"
           "SCALE이 결정하는 것: 브랜치 전략, PR 워크플로우, 훅 강도"
        2. _templates/ 폴더 사용법 설명 추가
        3. 에이전트 현황 표 갱신
             추가: security-reviewer, step-validator
             삭제: example-agent
             code-reviewer + step-validator: 모든 SCALE 항상 생성 명시

- [ ] [에이전트5] /init-project — 에이전트 자동 생성 로직 추가
      파일: .claude/commands/init-project.md
      (스킬 고도화 섹션5 [스킬1-C]와 함께 진행)
      추가 내용:
        0. SCALE 인터뷰 (가장 먼저)
           인터뷰: 프로젝트 규모는? (1=개인 / 2=스타트업 / 3=회사)
           SCALE=1 → 브랜치 없음, 훅 기본 강도, PR 없음
           SCALE=2 → feature/* 브랜치, PR 워크플로우, 훅 중간 강도
           SCALE=3 → main/develop/feature 3단계 브랜치, ADR 강제, 훅 최고 강도
           공통 (모든 SCALE): code-reviewer + step-validator 항상 생성
        A. 신규/기존 프로젝트 분기
           - 신규: 전체 구조 생성 (현재 동작 유지)
           - 기존: .claude/ + hooks + agents/ + docs/ref/ + CLAUDE.md 추가, src/ tests/ 건드리지 않음
           충돌 처리 (.claude/ 이미 존재 시):
             인터뷰: 기존 .claude/ 설정을 어떻게 처리하겠습니까? (덮어쓰기 / 병합 / 건너뜀)
             덮어쓰기 → 하네스 파일로 교체
             병합     → 기존 settings.json 유지 + 누락된 훅/커맨드만 추가
             건너뜀   → 해당 파일 변경 없이 나머지만 진행
        B. 팀/개인 인터뷰
           인터뷰: 개인 프로젝트입니까, 팀 프로젝트입니까?
           팀 → CONTRIBUTING.md 자동 생성 (내용은 SCALE 기반)
                  SCALE=1: 커밋 규칙, 기본 코드 스타일
                  SCALE=2: + feature/* 브랜치 전략, PR 절차
                  SCALE=3: + main/develop/feature 3단계 브랜치, ADR 작성 규칙
        C. 하네스 파일 자동 gitignore (인터뷰 없이 항상 적용)
           .gitignore에 추가: .claude/ agents/ docs/ref/ CLAUDE.md logs/ .env
           사유: 하네스는 개인 개발 도구 — 팀원마다 범위가 다르므로 커밋 불필요
           주의: 이미 tracked된 파일은 .gitignore 추가만으로 무시 안 됨
           추가 처리: git rm --cached -r 로 기존 tracked 하네스 파일 언트랙 후 gitignore 적용
        D. 보안 에이전트 조건부 생성
           인터뷰: "배포 예정입니까? 민감 데이터(결제/개인정보)를 처리합니까?"
           Y → security-reviewer.md 생성
        E. 도메인 테마 인터뷰 + 에이전트 생성 (모든 SCALE)
           인터뷰: "주요 도메인은? (웹앱/E-Commerce/AI-ML/API서비스/기타)"
           웹앱 → auth-agent.md, user-agent.md
           E-Commerce → payment-agent.md, product-agent.md, order-agent.md
           AI/ML → model-agent.md, data-pipeline-agent.md
           기타 → 직접 입력
           생성 소스: agents/_templates/domain-agent.tpl.md 복사 후 플레이스홀더 치환
        F. 이메일 알림 설정 인터뷰 (모든 SCALE)
           인터뷰: 이메일 알림을 받으시겠습니까? (Y/N)
           Y → 추가 입력: 수신 이메일 주소를 입력하세요 (예: you@example.com)
               .env에 즉시 추가:
                 SMTP_HOST=
                 SMTP_PORT=587
                 SMTP_USER=
                 SMTP_PASS=
                 NOTIFY_EMAIL=<입력한 주소>
               안내: SMTP_HOST / SMTP_USER / SMTP_PASS는 .env에서 직접 채워야 함
               step-validator 성공/최종 실패 시 NOTIFY_EMAIL로 발송
           N → 이메일 설정 생략

- [ ] [에이전트6] agents/step-validator.md 신규 작성 + ultrawork 연동
      레인: Review Lane | 모델: sonnet
      트리거: ultrawork 모든 병렬 태스크 완료 후 자동 호출 (반자동)
      실행 순서:
        1. git diff 분석 — exec-plan 범위 기준 변경 파일 목록 + 요약
        2. lint 실행 — 프로젝트에 설정된 린터 (언어 불특정)
        3. 테스트 실행 — tests/ 폴더 존재 시
        4. code-reviewer 호출 — 변경 파일 대상 코드 품질 검토 (로직, 명명, 레이어 위반)
           → 게이트 아님: 발견 사항은 리포트에 포함, 흐름 블록 안 함
      결과 처리:
        - 1~3 통과 → 성공 리포트 생성 (code-reviewer 발견 사항 포함) + 이메일 발송 (SMTP 설정 시)
        - 1~3 실패 → 실패 리포트 생성 → ultrawork에 피드백 전달 → 자동 재시도
        - 최대 3회 재시도 후에도 실패 → 최종 실패 리포트 + 이메일 발송 + 사용자 전달
      이메일 조건: /init-project 이메일 인터뷰 Y 선택 시 → 성공/최종 실패 시 모두 발송
      연동 작업: ultrawork.md 마지막 단계에 step-validator 자동 호출 구문 추가

### 3. 실질적 문제점 수정

- [ ] [문제1] docs/ref/session-state.md 언트랙 처리
      현재 상태: git에 tracked + Modified 상태
      처리:
        1. git rm --cached docs/ref/session-state.md 실행 (파일은 로컬 유지, git 추적 제거)
        2. [에이전트5] gitignore 작업 시 docs/ref/ 추가로 이후 변경 무시
      주의: .gitignore 추가만으로는 이미 tracked 파일에 효과 없음

- [ ] [문제2] QUALITY_SCORE.md / RELIABILITY.md / tech-debt-tracker.md 실사용 가이드
      A. docs/ref/quality-guide.md 신규 작성
         내용: 각 문서가 무엇인지, 언제/누가/어떻게 채우는지 상세 설명
           QUALITY_SCORE.md — Phase 완료 후 테스트 커버리지 기반 A~F 등급 기입
           RELIABILITY.md   — 배포 후 런타임 지표 측정 (미배포 프로젝트는 비워도 됨)
           tech-debt-tracker.md — doc-gardener 에이전트가 발견한 부채 자동 추가
      B. 세 파일 각 상단에 usage 섹션 + quality-guide.md 링크 추가

- [ ] [문제3] skills/ vs .claude/skills/ 구조 설명 추가
      현재 구조 유지 (역할이 다름, 통합 불필요):
        skills/ (루트): 마켓플레이스 배포용 SKILL.md — 다른 프로젝트가 설치 가능
        .claude/skills/: 하네스 내부 실행 스크립트 (score.py, analyze_sessions.py 등)
      처리: CLAUDE.md 프로젝트 구조 섹션에 두 폴더 역할 한 줄 설명 추가

- [ ] [문제4] tdd-enforcer.sh 설계 완성
      A. SCALE 기반 활성화 ([에이전트5] /init-project + [스킬1-C]와 연동)
         SCALE=1 → hooks-strict.flag 생성 안 함 (TDD 비강제)
         SCALE=2 → 인터뷰 "TDD 강제 활성화하시겠습니까?" Y → hooks-strict.flag 생성
         SCALE=3 → hooks-strict.flag 자동 생성 (기본 활성)
      B. 메시지 개선
         차단 시 예상 테스트 파일 경로 목록 출력 (언어별 명명 규칙 기반)
         비활성화 방법 안내 (.claude/hooks-strict.flag 삭제)
      C. docs/ref/tdd-guide.md 작성
         내용: 활성화 방법, 테스트 파일 명명 규칙 (언어별), 비활성화 방법

- [ ] [문제5] deny-patterns.json + deny-list-guard.sh 폐지 → pre-bash-guard.sh 통합
      폐지: .claude/deny-patterns.json, .claude/hooks/deny-list-guard.sh
      사유: pre-bash-guard.sh가 이미 rm -rf / --no-verify / curl|sh / git push --force 처리
            JSON 추상화가 복잡성만 추가, 기존 패턴 3개 실효성 없음 (SELECT *, eval(, sleep(0))
      pre-bash-guard.sh에 추가할 패턴:
        DROP TABLE / DROP DATABASE  — DB 파괴 (되돌릴 수 없음)
        TRUNCATE                    — 테이블 전체 삭제
        chmod 777                   — 전체 권한 부여 (보안 취약)

### 4. 주의사항 개선

- [x] [주의1+5] voice 기능 전체 제거 (완료)
      삭제: global-setup/voice/ (voice_input.py, install_voice.ps1, start_voice.ps1, requirements.txt, README.md)
      수정: global-setup/settings.json — SessionStart에서 start_voice.ps1 훅 제거
      수정: global-setup/hooks/context-bar.sh — voice_seg 블록 제거
      수정: global-setup/install.sh — voice 복사 단계 제거

- [x] [주의2] executor.py --timeout 옵션 추가 (완료)
      사용: python executor.py --plan ... --timeout 600  (기본값: 300초)

- [ ] [주의3] lint-test-build.sh / sub-agent-review.sh SCALE 기반 활성화
      step-validator와 역할 분리 (중복 아님):
        lint-test-build.sh → git commit 전 빠른 로컬 가드 (즉시 피드백)
        step-validator     → ultrawork 완료 후 종합 검증 (비동기, 깊은 검토)
      /init-project ([에이전트5] H항목으로 추가):
        SCALE=1 → 두 훅 비활성 (개인 개발, 속도 우선)
        SCALE=2 → 인터뷰: "커밋 전 lint/test 자동 실행? / PR 리뷰 서브에이전트?" Y → 활성
        SCALE=3 → 두 훅 자동 활성 (기본)

- [ ] [주의4] architecture-guard.sh SCALE 기반 엄격 모드 설계
      아키텍처 가드: 파일 저장 시 레이어 의존성 위반 자동 감지
        경고 모드(기본): 위반 감지 시 메시지만 출력, 저장 허용
        엄격 모드: 위반 감지 시 저장 차단 (hooks-strict.flag 존재 시)
      /init-project ([에이전트5] I항목으로 추가):
        SCALE=1 → 경고 모드 (hooks-strict.flag 미생성)
        SCALE=2 → 인터뷰: "레이어 위반 시 저장 차단 활성화?" Y → hooks-strict.flag 생성
        SCALE=3 → 자동 엄격 모드 (hooks-strict.flag 자동 생성)
      문서화: docs/ref/architecture-guide.md 신규 작성
        내용: 레이어 구조 설명, 엄격 모드 활성화(touch .claude/hooks-strict.flag), 비활성화 방법

### 5. 스킬 고도화

- [ ] [스킬1-A] /init-project — git 전략 섹션 추가
      브랜치 전략 선택 (main only / feature / git flow), 원격 저장소 연결, .gitignore 자동 생성

- [ ] [스킬1-B] /init-project — 양식 작성 후 보완 인터뷰 강화
      양식 제출 후 모호/빈 항목 자동 감지 → 소크라테스식 추가 질문 → PRD 초안 생성

- [ ] [스킬1-C] /init-project — 규모별 차별화 고도화
      SCALE=1: code-reviewer + step-validator 생성, 브랜치 전략 없음, PR 없음
      SCALE=2: + feature/* 브랜치, PR 워크플로우, 훅 중간 강도
      SCALE=3: + main/develop/feature 3단계 브랜치, ADR 강제, 훅 최고 강도

- [ ] [스킬新] /PR 스킬 신규 작성
      staged → /commit → push → gh pr create 자동화 (push 전 confirm 필수)

- [ ] [스킬7] ai-readiness-cartography 캐시 로직 추가
      파일 변경 없으면 재스캔 생략

- [ ] [스킬8] improve-token-efficiency 캐시 로직 추가
      새 세션 없으면 재분석 생략

- [ ] [연결] ultrawork.md + CLAUDE.md — Plan 모드 실행 흐름 명시
      독립 태스크 3개+ → /ultrawork / 1~2개 → /ralph / 단순 작업 → 직접 실행

---

## P1 — 고도화 [나중]

### 1. AI-Readiness 주기적 측정 체계 수립

- [ ] [P1-1-A] /init-project — AI-Readiness 추적 인터뷰 추가
      인터뷰: "AI-Readiness 주기 측정을 활성화하시겠습니까? (Y/N)"
      Y → 추가 인터뷰: 측정 주기 선택 (주 1회 / 월 1회)
          /schedule로 주기적 ai-readiness-cartography 실행 등록
          git 비활성 감지: 30일간 커밋 없으면 스케줄 자동 일시정지
      N → 스킵

- [ ] [P1-1-B] /close-project 스킬 신규 작성
      파일: .claude/commands/close-project.md
      작업 순서:
        1. 미커밋 파일 확인 + 최종 커밋 제안
        2. 최종 AI-Readiness 점수 측정
        3. 토큰/비용 효율 최종 분석 (improve-token-efficiency)
        4. TODO.md 미완료 항목 집계
        5. exec-plans/active/ → exec-plans/completed/ 이동
        6. README 정리 (프로젝트 상태 반영)
        7. 최종 HTML 대시보드 생성 (AI-Readiness + 토큰 효율 통합)
        8. 이메일 + 토스트 알림 발송 (SMTP 설정 시)
        9. .project-closed 플래그 생성 (스케줄 재활성화 방지)
        10. 회고 인터뷰 + 회고 문서 생성 (선택)
        11. 주기적 AI-Readiness 스케줄 중단