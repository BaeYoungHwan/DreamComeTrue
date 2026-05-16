# /PR — PR 자동화

Staged 변경사항을 커밋하고 GitHub PR을 자동으로 생성합니다.
**push 전 반드시 사용자 확인을 받습니다.**

---

## 실행 흐름

### 1단계 — 브랜치 및 staged 변경사항 확인

```bash
git branch --show-current
git status
git diff --staged --stat
```

현재 브랜치가 `main` 또는 `master`이면 즉시 중단:
```
⛔ main/master 브랜치에서는 PR을 생성할 수 없습니다.
작업 브랜치로 전환 후 다시 시도하세요:
  git checkout -b feature/[작업명]
```

staged 변경사항이 없으면 중단:
```
⚠️  staged 변경사항이 없습니다.
git add <파일> 로 스테이징 후 다시 시도하세요.
```

### 2단계 — 커밋 (`/commit` 스킬 호출)

`.claude/commands/commit.md` 의 `/commit` 스킬을 실행한다.
커밋 메시지 생성 로직·컨벤션 준수는 `/commit` 스킬에 위임한다.
(`/commit` 스킬 업데이트 시 이 단계에 자동 반영됨)

### 3단계 — push 확인 (필수 — 건너뛸 수 없음)

아래 메시지를 출력하고 명시적 확인을 받는다:

```
📤 Push 준비 완료

브랜치: [현재 브랜치명]
원격:   origin/[브랜치명]
커밋:   [해시 7자리] [커밋 메시지]

push 하시겠습니까? (yes / no):
```

- `no` → 커밋은 로컬 유지, PR 생성 중단
- `yes` → 4단계 진행

### 4단계 — push

```bash
git push origin [현재 브랜치]
# 업스트림 없는 경우:
git push -u origin [현재 브랜치]
```

### 5단계 — PR 생성

```bash
gh pr create \
  --title "[자동 생성된 제목]" \
  --body "$(cat <<'PREOF'
## 변경 내용
[커밋 메시지 요약]

## 변경 파일
[git diff --name-only 목록]

## 테스트 방법
[변경 타입에 따른 검증 제안]

🤖 /PR 스킬로 자동 생성
PREOF
)"
```

`gh` CLI가 없으면 이 단계에서 중단하고 수동 PR 생성 안내 출력.

### 6단계 — 완료 안내

```
✅ PR 생성 완료
URL: [PR URL]
```

---

## 주의사항

- main/master 브랜치에서 실행 불가 (settings.json deny 규칙)
- `sub-agent-review.sh` 훅 활성화 시 push 전 자동 diff 리뷰 실행
