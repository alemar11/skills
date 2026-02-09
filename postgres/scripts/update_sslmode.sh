#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ROOT_OVERRIDE="${DB_PROJECT_ROOT:-${PROJECT_ROOT:-}}"
PROJECT_ROOT="$ROOT_OVERRIDE"
if [[ -z "$PROJECT_ROOT" && -x "$(command -v git)" ]]; then
  PROJECT_ROOT="$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null || true)"
fi
if [[ -z "$PROJECT_ROOT" ]]; then
  PROJECT_ROOT="$PWD"
fi
if [[ -z "$ROOT_OVERRIDE" ]]; then
  case "$PROJECT_ROOT" in
    "$SKILL_ROOT"|"$SKILL_ROOT"/*)
      echo "Project root resolved to the postgres skill directory: $SKILL_ROOT" >&2
      echo "Run this from the postgres skill directory with DB_PROJECT_ROOT/PROJECT_ROOT set (or run from your project root)." >&2
      exit 1
      ;;
  esac
fi

TOML_PATH="$PROJECT_ROOT/.skills/postgres/postgres.toml"

PROFILE="${1:-}"
NEW_SSLMODE="${2:-}"

if [[ -z "$PROFILE" || -z "$NEW_SSLMODE" ]]; then
  echo "Usage: update_sslmode.sh <profile> <true|false>" >&2
  exit 1
fi

normalize_sslmode() {
  case "${1,,}" in
    true|t|1|yes|y|on|enable|enabled|require|required|verify-ca|verify-full)
      echo "true"
      ;;
    false|f|0|no|n|off|disable|disabled)
      echo "false"
      ;;
    *)
      return 1
      ;;
  esac
}

SSL_VALUE="$(normalize_sslmode "$NEW_SSLMODE")" || {
  echo "Invalid sslmode '$NEW_SSLMODE'. Use true/false (or require/disable)." >&2
  exit 1
}

if [[ ! -f "$TOML_PATH" ]]; then
  echo "postgres.toml not found at $TOML_PATH" >&2
  exit 1
fi

if command -v git >/dev/null 2>&1 \
  && git -C "$PROJECT_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1 \
  && ! git -C "$PROJECT_ROOT" check-ignore -q ".skills/postgres/postgres.toml" 2>/dev/null; then
  echo "Warning: .skills/postgres/postgres.toml is not ignored by git. Add it to .gitignore to avoid committing credentials." >&2
fi

tmp_file="$(mktemp)"

awk -v profile="$PROFILE" -v sslmode="$SSL_VALUE" '
  BEGIN { in_profile=0; found=0; updated=0 }
  /^[[:space:]]*\[database\.[a-z0-9_]+\][[:space:]]*$/ {
    if (in_profile && !updated) {
      print "sslmode = " sslmode
      updated=1
    }
    in_profile=0
    if (match($0, /^[[:space:]]*\[database\.([a-z0-9_]+)\][[:space:]]*$/, m)) {
      if (m[1] == profile) {
        in_profile=1
        found=1
      }
    }
    print
    next
  }
  {
    if (in_profile && $0 ~ /^[[:space:]]*sslmode[[:space:]]*=/) {
      print "sslmode = " sslmode
      updated=1
      next
    }
    print
  }
  END {
    if (in_profile && !updated) {
      print "sslmode = " sslmode
      updated=1
    }
    if (!found) {
      exit 2
    }
  }
' "$TOML_PATH" > "$tmp_file"

status=$?
if [[ $status -eq 2 ]]; then
  rm -f "$tmp_file"
  echo "Profile '$PROFILE' not found in postgres.toml." >&2
  exit 1
fi

mv "$tmp_file" "$TOML_PATH"
