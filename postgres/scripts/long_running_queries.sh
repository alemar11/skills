#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MINUTES="${1:-5}"
LIMIT="${2:-20}"

if ! [[ "$MINUTES" =~ ^[0-9]+$ && "$LIMIT" =~ ^[0-9]+$ ]]; then
  echo "Usage: long_running_queries.sh [minutes] [limit]" >&2
  exit 1
fi

"$SCRIPT_DIR/psql_with_ssl_fallback.sh" \
  -v ON_ERROR_STOP=1 \
  -P pager=off \
  -c "
select
  pid,
  usename as user,
  datname as db,
  state,
  now() - query_start as query_age,
  left(query, 200) as query
from pg_stat_activity
where state = 'active'
  and query_start is not null
  and now() - query_start > interval '${MINUTES} minutes'
order by query_start asc
limit ${LIMIT};"
