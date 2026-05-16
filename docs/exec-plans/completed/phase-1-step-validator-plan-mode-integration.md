# Phase 1 — step-validator Plan 모드 통합

> 출처: .claude/plans/claude-plan-smooth-pascal.md
> 생성: 2026-05-16

## 목표
step-validator를 Plan 모드 Phase 완료 시 자동 호출하고, 이메일 리포트를 1회 발송한다.
SMTP 미설정 시 오류 없이 graceful skip 한다.

## 태스크
- [x] send_notification.py 신규 생성 (stdlib 전용 SMTP 발송 스크립트)
- [x] step-validator.md — CALLER_CONTEXT 파라미터 + §5 Plan 모드 이메일 섹션 추가
- [x] plan-mode-workflow.md — §4 step-validator 호출 명세 추가
- [x] init-project.md — [F] 섹션 설명 문구 업데이트

## 검증 기준
1. .env 없을 때 send_notification.py exit 0 (graceful skip)
2. SMTP_HOST 미설정 시 exit 0 (graceful skip)
3. step-validator.md에 CALLER_CONTEXT=plan 분기 및 §5 존재
4. plan-mode-workflow.md에 §4 존재
