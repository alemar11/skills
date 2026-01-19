#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/pg_env.sh"
eval "$("$SCRIPT_DIR/resolve_db_url.sh")"

timestamp="$(date +%Y%m%d_%H%M%S)"
profile="${DB_PROFILE:-local}"
output="${1:-data_${profile}_${timestamp}.dump}"

args=(--data-only --no-owner --no-acl)

if [[ "$output" == *.sql ]]; then
  pg_dump "${args[@]}" "$DB_URL" > "$output"
else
  pg_dump --format=custom "${args[@]}" "$DB_URL" -f "$output"
fi

echo "Wrote $output"
