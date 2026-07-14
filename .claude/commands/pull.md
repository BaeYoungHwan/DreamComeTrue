# /pull — main/master 최신 변경사항 동기화

원격 저장소의 최신 `main`(또는 `master`) 브랜치 변경사항을 현재 작업 브랜치로 가져옵니다.

---

## 실행 흐름

### 1단계 — 현재 상태 확인

```bash
git branch --show-current
git status
```

현재 브랜치가 `main` 또는 `master`이면 병합이 아닌 단순 fast-forward pull만 수행하고 종료:
```bash
git pull origin [현재 브랜치]
```

작업 트리에 커밋되지 않은 변경사항(unstaged/staged)이 있으면 충돌 위험을 안내하고, stash 여부를 사용자에게 확인한다:
```
⚠️  커밋되지 않은 변경사항이 있습니다.
계속 진행하면 병합 중 충돌이 발생할 수 있습니다.
git stash로 임시 저장 후 진행할까요?
```

### 2단계 — 원격 최신화

```bash
git fetch origin
```

### 3단계 — base 브랜치 감지

```bash
git rev-parse --verify origin/main 2>/dev/null && echo main || echo master
```

`origin/main`이 존재하면 `main`, 없으면 `master`를 base로 사용한다.

### 4단계 — 병합 실행 (merge, 자동 실행)

```bash
git merge origin/[base 브랜치] --no-edit
```

- 히스토리 보존을 위해 기본은 **merge**를 사용한다 (rebase는 이미 push된 커밋을 재작성할 수 있어 기본값으로 쓰지 않음).
- 사용자가 명시적으로 rebase를 요청하면 `git rebase origin/[base 브랜치]`로 대체한다.

**충돌 발생 시**: 자동으로 해결하지 않고 즉시 중단, 충돌 파일 목록을 보여준다.
```bash
git status --porcelain | grep "^UU\|^AA\|^DD"
```
```
⛔ 병합 충돌이 발생했습니다. 아래 파일을 직접 해결해주세요:
[충돌 파일 목록]

해결 후:
  git add <파일>
  git commit
```

### 5단계 — 완료 안내

충돌 없이 완료되면:
```
✅ [base 브랜치] → [현재 브랜치] 동기화 완료
[git log --oneline HEAD@{1}..HEAD 로 새로 반영된 커밋 요약]
```

---

## 주의사항

- 원격이 아니라 로컬 `main`/`master`를 기준으로 병합하지 않는다 — 항상 `git fetch` 후 `origin/[base]`를 사용해 최신 상태를 보장한다.
- 충돌은 절대 자동 해결하지 않는다.
- `--no-verify` 등 훅 우회 옵션은 사용하지 않는다.
