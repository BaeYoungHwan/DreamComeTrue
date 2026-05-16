# exec-plan: P0 전체 구현

> 생성일: 2026-05-15
> 범례: [ ] 미착수 | [🔄] 진행 중 | [x] 완료
> 실행: `python executor.py --plan docs/exec-plans/active/p0-implementation.md`

---

## Phase 1 — 독립 작업 (병렬 가능)

의존성 없는 항목. ultrawork로 병렬 실행 권장.

- [x] [문제1] git rm --cached docs/ref/session-state.md 실행하여 session-state.md를 git 추적에서 제거. 파일은 로컬 유지. .gitignore에 docs/ref/ 추가.

- [x] [문제2] docs/ref/quality-guide.md 신규 작성. QUALITY_SCORE.md(Phase 완료 후 테스트 커버리지 기반 A~F 등급), RELIABILITY.md(배포 후 런타임 지표, 미배포 시 비워도 됨), tech-debt-tracker.md(doc-gardener 자동 추가)의 작성 시점·방법 설명. 세 파일 상단에 usage 섹션 + quality-guide.md 링크 추가.

- [x] [문제3] CLAUDE.md 프로젝트 구조 섹션에 skills/(루트, 마켓플레이스 배포용)와 .claude/skills/(하네스 내부 실행 스크립트) 역할 차이 한 줄씩 추가.

- [x] [문제5] .claude/deny-patterns.json과 .claude/hooks/deny-list-guard.sh 삭제. .claude/hooks/pre-bash-guard.sh에 DROP TABLE, DROP DATABASE, TRUNCATE, chmod 777 패턴 추가.

- [x] [스킬7] .claude/commands/ai-readiness-cartography.md에 캐시 로직 추가. 마지막 실행 이후 파일 변경이 없으면 재스캔 생략하고 캐시된 결과 반환.

- [x] [스킬8] .claude/commands/improve-token-efficiency.md에 캐시 로직 추가. 마지막 분석 이후 새 세션이 없으면 재분석 생략하고 캐시된 결과 반환.

- [x] [연결] ultrawork.md 마지막 단계에 step-validator 자동 호출 구문 추가. CLAUDE.md에 "독립 태스크 3개+ → /ultrawork / 1~2개 → /ralph / 단순 작업 → 직접 실행" Plan 모드 실행 흐름 명시.

- [x] [에이전트1] agents/security-reviewer.md 신규 작성. 레인: Review Lane, 모델: sonnet. OWASP Top 10 체크리스트(SQLi, XSS, IDOR, 인증 취약점), 비밀키·자격증명 하드코딩 탐지. 출력: 🔴 위험(즉시 수정) / 🟡 경고(권장) / 🟢 통과.

- [x] [에이전트2] agents/_templates/ 폴더 생성 후 domain-agent.tpl.md 작성. 플레이스홀더: {{DOMAIN_NAME}}, {{DOMAIN_DESC}}, {{DOMAIN_RULES}}, {{DOMAIN_FILES}}. 웹앱/E-Commerce/AI-ML 예시 도메인 주석 포함.

- [x] [에이전트4] agents/LANES.md 갱신. 에이전트 생성 기준 섹션 추가(code-reviewer 항상 / security-reviewer 배포·민감데이터 시 / 도메인 테마 선택 시). _templates/ 폴더 사용법 설명. 에이전트 현황 표에 security-reviewer·step-validator 추가, example-agent 삭제 예정 표시. code-reviewer + step-validator 모든 SCALE 항상 생성 명시.

---

## Phase 2 — Phase 1 완료 후

- [x] [에이전트3] agents/example-agent.md 삭제. 삭제 사유: _templates/ 방식으로 역할 이전. 선행조건: [에이전트4] 완료.

- [x] [에이전트6] agents/step-validator.md 신규 작성. 레인: Review Lane, 모델: sonnet. 트리거: ultrawork 병렬 태스크 완료 후 자동 호출. 실행 순서: (1)git diff 분석 (2)lint 실행 (3)테스트 실행 (4)code-reviewer 호출(게이트 아님). 결과: 1~3 통과→성공 리포트+이메일, 실패→ultrawork 피드백→재시도(최대 3회), 최종 실패→이메일+사용자 전달.

- [x] [스킬新] .claude/commands/PR.md 신규 작성. staged 변경사항 → /commit → push → gh pr create 자동화. push 전 confirm 필수.

- [x] [주의3] /init-project에 H항목 추가: lint-test-build.sh / sub-agent-review.sh SCALE 기반 활성화. SCALE=1→두 훅 비활성, SCALE=2→인터뷰로 선택, SCALE=3→자동 활성.

- [x] [주의4] architecture-guard.sh에 엄격 모드 추가. hooks-strict.flag 존재 시 레이어 위반으로 저장 차단, 없으면 경고만 출력. docs/ref/architecture-guide.md 신규 작성(레이어 구조, 활성화·비활성화 방법). /init-project에 I항목 추가: SCALE=1→경고, SCALE=2→인터뷰, SCALE=3→자동 엄격.

---

## Phase 3 — /init-project 통합 (가장 복잡)

Phase 1·2 완료 후 진행. /init-project는 모든 에이전트·훅·SCALE 로직이 집결하는 핵심 파일.

- [x] [에이전트5 + 스킬1-A/B/C] .claude/commands/init-project.md 전면 고도화. 추가 내용:
      0. SCALE 인터뷰(개인1/스타트업2/회사3) — 브랜치 전략·훅 강도 결정
      A. 신규/기존 프로젝트 분기 — 기존 시 .claude/ 충돌 처리(덮어쓰기/병합/건너뜀)
      B. 팀/개인 인터뷰 — CONTRIBUTING.md 자동 생성(SCALE 기반 내용)
      C. 하네스 파일 gitignore 자동 적용 + git rm --cached 처리
      D. 보안 에이전트 조건부 생성 — 배포 예정·민감 데이터 시 security-reviewer.md 생성
      E. 도메인 테마 인터뷰 + 에이전트 생성 — _templates/domain-agent.tpl.md 복사·치환
      F. 이메일 알림 설정 — .env에 SMTP 설정 추가
      H. lint-test-build.sh / sub-agent-review.sh SCALE 기반 활성화
      I. architecture-guard.sh SCALE 기반 엄격 모드 설정
      스킬1-A: git 전략 섹션(브랜치 전략·원격 저장소·.gitignore 자동 생성)
      스킬1-B: 양식 제출 후 모호·빈 항목 자동 감지 → 소크라테스식 보완 인터뷰 → PRD 초안
      스킬1-C: SCALE별 차별화(SCALE=1: code-reviewer+step-validator, SCALE=2: feature/* 브랜치, SCALE=3: 3단계 브랜치·ADR 강제)

- [x] [문제4] tdd-enforcer.sh SCALE 기반 활성화 완성. SCALE=1→비강제, SCALE=2→인터뷰 Y 시 hooks-strict.flag 생성, SCALE=3→자동 생성. 차단 시 예상 테스트 파일 경로 출력 + 비활성화 방법 안내. docs/ref/tdd-guide.md 작성.
