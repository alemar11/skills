#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIMIT="${1:-20}"

EXT_CHECK="$("$SCRIPT_DIR/psql_with_ssl_fallback.sh" -v ON_ERROR_STOP=1 -Atc "select 1 from pg_extension where extname = 'pg_stat_statements';")"
if [[ -z "$EXT_CHECK" ]]; then
  echo "pg_stat_statements extension is not enabled in this database." >&2
  exit 1
fi

HAS_TOTAL_EXEC_TIME="$("$SCRIPT_DIR/psql_with_ssl_fallback.sh" -v ON_ERROR_STOP=1 -Atc \
  "select 1 from information_schema.columns where table_name='pg_stat_statements' and column_name='total_exec_time';")"

if [[ -n "$HAS_TOTAL_EXEC_TIME" ]]; then
  TOTAL_COL="total_exec_time"
  MEAN_COL="mean_exec_time"
else
  TOTAL_COL="total_time"
  MEAN_COL="mean_time"
fi

"$SCRIPT_DIR/psql_with_ssl_fallback.sh" \
  -v ON_ERROR_STOP=1 \
  -P pager=off \
  -c "
select
  calls,
  round(${TOTAL_COL}::numeric, 2) as total_ms,
  round(${MEAN_COL}::numeric, 2) as mean_ms,
  rows,
  left(query, 300) as query
from pg_stat_statements
where dbid = (select oid from pg_database where datname = current_database())
order by ${TOTAL_COL} desc
limit ${LIMIT};"
