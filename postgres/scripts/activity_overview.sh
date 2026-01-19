#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIMIT="${1:-20}"

if ! [[ "$LIMIT" =~ ^[0-9]+$ ]]; then
  echo "Usage: activity_overview.sh [limit]" >&2
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
  wait_event_type,
  wait_event,
  now() - query_start as query_age,
  now() - xact_start as xact_age,
  left(query, 200) as query
from pg_stat_activity
where pid <> pg_backend_pid()
  and state <> 'idle'
order by query_start desc nulls last
limit ${LIMIT};"
