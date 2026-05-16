# 에이전트 레인 분류

에이전트를 4가지 레인으로 분류합니다. 새 에이전트는 반드시 하나의 레인에 속해야 합니다.

---

## 레인 정의

### 🏗️ Build / Analysis Lane
**역할**: 구현, 분석, 데이터 처리
**특징**: 독립적 코딩 작업, 병렬 처리 최적
**예시 에이전트**: `frontend.md`, `backend.md`, `db.md`, `data-pipeline.md`
**권장 모델**: Sonnet (구현), Haiku (분석/탐색)

```yaml
---
name: [이름]
description: [설명]
model: sonnet
---
```

### 🔍 Review Lane
**역할**: 코드 검토, 보안 분석, 품질 검증
**특징**: 파일 작성 없음. lint·테스트 실행은 허용 (step-validator). 다른 에이전트 결과 검토.
**예시 에이전트**: `code-reviewer.md`
**권장 모델**: Sonnet

```yaml
---
name: code-reviewer
description: 코드 품질 검토 전담. PR 또는 구현 완료 후 호출.
model: sonnet
---
```

### 🌐 Domain Lane
**역할**: 특정 비즈니스 도메인 전담
**특징**: 도메인 규칙과 컨텍스트를 깊이 이해
**예시 에이전트**: `auth-agent.md`, `payment-agent.md`
**권장 모델**: Sonnet ~ Opus

### 🎯 Coordination Lane
**역할**: 다른 에이전트 조율, 결과 통합
**특징**: 직접 구현 안 함 — 에이전트 배분과 결과 취합
**예시 에이전트**: `orchestrator.md` (필요 시)
**권장 모델**: Sonnet

---

## 에이전트 생성 규칙

1. `agents/_templates/domain-agent.tpl.md`를 복사해서 시작
2. 레인 결정 후 `description`에 명시
3. 단일 책임 원칙: 하나의 에이전트는 하나의 역할만
4. 레인 간 의존성 최소화

---

## 에이전트 생성 기준

> SCALE(프로젝트 규모)과 무관하게 인터뷰 기반으로 결정합니다.

| 에이전트 | 생성 조건 |
|---------|---------|
| `code-reviewer` | **항상 생성** (모든 SCALE) |
| `step-validator` | **항상 생성** (모든 SCALE) |
| `security-reviewer` | 배포 예정 또는 민감 데이터(결제·개인정보) 처리 시 |
| 도메인 에이전트 | `/init-project` 도메인 테마 선택 시 (`_templates/` 복사·치환) |

### `_templates/` 폴더 사용법

1. `agents/_templates/domain-agent.tpl.md` 복사
2. 파일명을 `<도메인명>-agent.md` 로 변경
3. 플레이스홀더 4개 치환: `{{DOMAIN_NAME}}`, `{{DOMAIN_DESC}}`, `{{DOMAIN_RULES}}`, `{{DOMAIN_FILES}}`
4. `agents/` 폴더에 배치

---

## 현재 에이전트 목록

| 에이전트 | 레인 | 모델 | 상태 |
|----------|------|------|------|
| `code-reviewer.md` | Review Lane | sonnet | 활성 |
| `doc-gardener.md` | Review Lane | haiku | 활성 |
| `security-reviewer.md` | Review Lane | sonnet | 활성 |
| `step-validator.md` | Review Lane | sonnet | 활성 |
