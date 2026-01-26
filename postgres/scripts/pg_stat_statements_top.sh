#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/pg_env.sh"

eval "$("$SCRIPT_DIR/resolve_db_url.sh")"

limit="${1:-10}"
if ! [[ "$limit" =~ ^[0-9]+$ ]]; then
  echo "Usage: pg_stat_statements_top.sh [limit]" >&2
  exit 1
fi

psql "$DB_URL" -v ON_ERROR_STOP=1 -X -c "
select
  calls,
  round(total_exec_time::numeric, 2) as total_time_ms,
  round(mean_exec_time::numeric, 2) as mean_time_ms,
  query
from pg_stat_statements
order by total_exec_time desc
limit $limit;
"
