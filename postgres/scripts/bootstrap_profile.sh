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

python3 "$SCRIPT_DIR/bootstrap_profile.py" "$TOML_PATH" "$PROJECT_ROOT"
