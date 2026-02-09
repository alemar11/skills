#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${1:-}"
TOML_REL_PATH=".skills/postgres/postgres.toml"

if [[ -z "$PROJECT_ROOT" ]]; then
  exit 0
fi

if ! command -v git >/dev/null 2>&1; then
  exit 0
fi

if ! git -C "$PROJECT_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  exit 0
fi

if git -C "$PROJECT_ROOT" check-ignore -q "$TOML_REL_PATH" 2>/dev/null; then
  exit 0
fi

echo "Warning: $TOML_REL_PATH is not ignored by git. Add it to .gitignore to avoid committing credentials." >&2

