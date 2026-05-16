#!/usr/bin/env bash
# pre-bash-guard.sh — 위험한 Bash 명령 실행 전 차단
# PreToolUse(Bash) 훅: exit 1이면 명령 실행 자체를 막음

source "$(dirname "$0")/lib/parse-json.sh"

INPUT=$(cat)
COMMAND=$(get_tool_input_field "$INPUT" "command")

block() {
  local reason="$1"
  echo "❌ [보안 차단] $reason" >&2
  echo "   명령: $COMMAND" >&2
  echo "   이 명령은 실행되지 않았습니다." >&2
  exit 1
}

# 1. 훅 우회 시도 차단
if echo "$COMMAND" | grep -q -- '--no-verify'; then
  block "--no-verify 플래그는 허용되지 않습니다 (훅 우회 금지)"
fi

# 2. 자격증명 노출 패턴 차단
if echo "$COMMAND" | grep -qiE 'password\s*=|api_key\s*=|secret\s*=|token\s*='; then
  block "자격증명(password/api_key/secret/token)을 명령어에 직접 포함하지 마세요. .env를 사용하세요."
fi

# 3. 원격 스크립트 직접 실행 차단 (curl/wget | sh/bash)
if echo "$COMMAND" | grep -qE '(curl|wget).*(sh|bash)|sh\s*<\s*\(curl'; then
  block "원격 스크립트 직접 실행(curl|sh)은 차단됩니다. 먼저 내용을 확인하세요."
fi

# 4. 강제 푸시 차단 (settings.json deny와 이중 방어)
if echo "$COMMAND" | grep -qE 'git\s+push\s+.*--force|git\s+push\s+-f'; then
  block "강제 푸시(git push --force)는 차단됩니다."
fi

# 5. 재귀 삭제 차단
if echo "$COMMAND" | grep -iqE 'rm\s+-[a-zA-Z]*r[a-zA-Z]*f|rm\s+-[a-zA-Z]*f[a-zA-Z]*r'; then
  block "재귀 강제 삭제(rm -rf)는 차단됩니다."
fi

# 6. DB 파괴 명령 및 위험 권한 변경 차단
if echo "$COMMAND" | grep -iqE 'DROP\s+TABLE|DROP\s+DATABASE'; then
  block "DROP TABLE/DROP DATABASE는 차단됩니다. 되돌릴 수 없는 DB 파괴 명령입니다."
fi

if echo "$COMMAND" | grep -iqE '\bTRUNCATE\b'; then
  block "TRUNCATE는 차단됩니다. 테이블 전체 삭제 명령입니다."
fi

if echo "$COMMAND" | grep -iqE 'chmod\s+777'; then
  block "chmod 777은 차단됩니다. 전체 권한 부여는 보안 취약점입니다."
fi

exit 0
