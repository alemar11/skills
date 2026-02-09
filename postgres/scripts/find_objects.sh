#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/pg_env.sh"

pattern="${1:-}"
if [[ -z "$pattern" ]]; then
  echo "Usage: find_objects.sh <pattern>" >&2
  echo "Example: DB_PROFILE=local ./scripts/find_objects.sh users" >&2
  exit 1
fi

# If the user didn't pass an explicit ILIKE wildcard, make it a contains match.
if [[ "$pattern" != *"%"* && "$pattern" != *"_"* ]]; then
  pattern="%${pattern}%"
fi

"$SCRIPT_DIR/psql_with_ssl_fallback.sh" \
  -q \
  -v ON_ERROR_STOP=1 \
  -v "pattern=$pattern" \
  -f "$SCRIPT_DIR/find_objects.sql"
