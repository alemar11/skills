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
      echo "Run this from your project root or set DB_PROJECT_ROOT/PROJECT_ROOT." >&2
      exit 1
      ;;
  esac
fi

TOML_PATH="$PROJECT_ROOT/.skills/postgres/postgres.toml"

PROFILE="${1:-}"
NEW_SSLMODE="${2:-}"

if [[ -z "$PROFILE" || -z "$NEW_SSLMODE" ]]; then
  echo "Usage: update_sslmode.sh <profile> <sslmode>" >&2
  exit 1
fi

if [[ ! -f "$TOML_PATH" ]]; then
  echo "postgres.toml not found at $TOML_PATH" >&2
  exit 1
fi

tmp_file="$(mktemp)"

awk -v profile="$PROFILE" -v sslmode="$NEW_SSLMODE" '
  BEGIN { in_profile=0; found=0; updated=0 }
  /^[[:space:]]*\[database\.[a-z0-9_]+\][[:space:]]*$/ {
    if (in_profile && !updated) {
      print "sslmode = \"" sslmode "\""
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
      print "sslmode = \"" sslmode "\""
      updated=1
      next
    }
    print
  }
  END {
    if (in_profile && !updated) {
      print "sslmode = \"" sslmode "\""
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
