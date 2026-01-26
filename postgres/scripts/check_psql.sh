#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/pg_env.sh"

if ! command -v psql >/dev/null 2>&1; then
  echo "psql not found on PATH. If installed, set [configuration].pg_bin_path in postgres.toml or install PostgreSQL client tools." >&2
  exit 1
fi

psql --version
