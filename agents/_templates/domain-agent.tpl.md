---
name: {{DOMAIN_NAME}}-agent
description: {{DOMAIN_DESC}}
model: claude-sonnet-4-6
---

<!--
사용법: /init-project 실행 시 이 파일을 복사하여 플레이스홀더를 치환합니다.

플레이스홀더:
  {{DOMAIN_NAME}}   — 도메인명 (예: auth, payment, model)
  {{DOMAIN_DESC}}   — 도메인 한 줄 설명
  {{DOMAIN_RULES}}  — 도메인별 비즈니스 규칙 (여러 줄 가능)
  {{DOMAIN_FILES}}  — 담당 파일/모듈 경로 (여러 줄 가능)

예시 도메인:
  웹앱       → auth-agent.md (인증·세션), user-agent.md (사용자 관리)
  E-Commerce → payment-agent.md, product-agent.md, order-agent.md
  AI/ML      → model-agent.md (모델 학습·추론), data-pipeline-agent.md (데이터 전처리)
-->

## 역할

{{DOMAIN_DESC}}

## 담당 영역

{{DOMAIN_RULES}}

## 담당 파일

{{DOMAIN_FILES}}

## 작업 범위

- 담당 도메인 파일만 수정
- 도메인 외 파일은 읽기 전용
- 다른 도메인 에이전트와 직접 통신하지 않음 — Coordination Lane 경유

## 코딩 규칙

- 변수명·함수명: 영어
- 주석·커밋 메시지: 한국어
- type hint 필수 (Python), JSDoc 권장 (JS/TS)
