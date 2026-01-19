#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"$SCRIPT_DIR/psql_with_ssl_fallback.sh" \
  -v ON_ERROR_STOP=1 \
  -P pager=off \
  -c "
select
  blocked.pid as blocked_pid,
  blocked.usename as blocked_user,
  blocking.pid as blocking_pid,
  blocking.usename as blocking_user,
  now() - blocked.query_start as blocked_duration,
  blocked.query as blocked_query,
  blocking.query as blocking_query
from pg_stat_activity blocked
join pg_stat_activity blocking
  on blocking.pid = any(pg_blocking_pids(blocked.pid))
order by blocked_duration desc;"
