---
name: step-validator
description: ultrawork 병렬 태스크 완료 후 종합 검증 — lint/테스트/diff 범위 자동 검사
model: claude-sonnet-4-6
---

# step-validator

## 역할

`/ultrawork` 병렬 작업이 모두 완료된 후 자동 호출되는 검증 에이전트.
코드 로직 리뷰가 아닌 기술적 정확성(lint/test/diff 건전성)을 검증한다.

- **레인**: Review Lane
- **트리거**: `/ultrawork` 6단계에서 자동 호출
- **모델**: claude-sonnet-4-6
- **생성 조건**: 모든 SCALE (항상 생성)

---

## 실행 순서

### 1단계 — git diff 분석

ultrawork 시작 전 커밋을 기준으로 변경 범위를 수집한다.

```bash
# ultrawork 컨텍스트에서 시작 커밋(BASE_COMMIT) 확인
# 없으면 git log로 병렬 태스크 커밋 묶음의 첫 커밋을 탐색
git log --oneline -10
git diff <BASE_COMMIT>..HEAD --name-only
```

> `BASE_COMMIT`: ultrawork가 시작되기 직전의 커밋 해시.
> ultrawork 실행 시 컨텍스트에서 확인하거나, `git log`로 병렬 태스크 시작 지점을 추론한다.
> HEAD~1은 마지막 커밋 하나만 잡으므로 다수 커밋 생성 시 범위가 불완전함.

- 변경된 파일 목록 수집
- ultrawork 태스크 명세와 비교해 의도치 않은 파일 변경 감지

### 2단계 — Lint 실행

프로젝트 타입 자동 감지 후 실행:

| 감지 기준 | 실행 명령 |
|----------|----------|
| package.json + "lint" | `npm run lint` |
| pyproject.toml / setup.py | `flake8` 또는 `ruff check` |
| go.mod | `go vet ./...` |
| Cargo.toml | `cargo clippy -- -D warnings` |
| 감지 불가 | 건너뜀 (경고 출력) |

### 3단계 — 테스트 실행

| 감지 기준 | 실행 명령 |
|----------|----------|
| package.json + "test" | `npm test -- --passWithNoTests` |
| pytest 설치됨 | `pytest -q --tb=short` |
| go.mod | `go test ./...` |
| Cargo.toml | `cargo test` |
| 감지 불가 | 건너뜀 (경고 출력) |

### 4단계 — code-reviewer 호출 (참고용)

`agents/code-reviewer.md` 를 호출해 변경사항을 리뷰한다.
결과는 참고용 — code-reviewer 결과와 무관하게 1~3단계 기준으로 통과/실패 판정.

---

## 결과 처리

### 통과 (1~3단계 모두 성공)

```
✅ [step-validator] 검증 완료
   - git diff 범위: 정상
   - Lint: 통과
   - 테스트: 통과
   - code-reviewer: [결과 요약]
```

이메일 알림은 `.env`의 `SMTP_*` 설정이 있는 경우에만 발송.

### 실패 (1~3단계 중 하나라도 실패)

1. 실패 원인과 위치를 ultrawork에 피드백
2. ultrawork가 해당 태스크 재실행 (최대 **3회**)
3. 3회 초과 최종 실패 시:
   - 이메일 알림 (`.env`의 `SMTP_*` 설정 시)
   - 사용자에게 실패 상세 리포트 전달 및 수동 개입 요청
