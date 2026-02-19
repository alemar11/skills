#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIMIT="${1:-20}"
QUERY_CHARS="${DB_QUERY_TEXT_MAX_CHARS:-300}"

if ! [[ "$LIMIT" =~ ^[0-9]+$ ]]; then
  echo "Invalid limit: $LIMIT" >&2
  exit 1
fi

if ! [[ "$QUERY_CHARS" =~ ^[0-9]+$ ]]; then
  echo "Invalid DB_QUERY_TEXT_MAX_CHARS value: $QUERY_CHARS" >&2
  exit 1
fi

"$SCRIPT_DIR/psql_with_ssl_fallback.sh" \
  -X \
  -v ON_ERROR_STOP=1 \
  -P pager=off \
  <<SQL
select
  exists(select 1 from pg_extension where extname = 'pg_stat_statements')::int as has_ext
\gset
\if :has_ext
select
  case
    when exists (
      select 1 from information_schema.columns
      where table_name = 'pg_stat_statements' and column_name = 'total_exec_time'
    ) then 'total_exec_time'
    else 'total_time'
  end as total_col,
  case
    when exists (
      select 1 from information_schema.columns
      where table_name = 'pg_stat_statements' and column_name = 'mean_exec_time'
    ) then 'mean_exec_time'
    else 'mean_time'
  end as mean_col
\gset
select
  calls,
  round(:"total_col"::numeric, 2) as total_ms,
  round(:"mean_col"::numeric, 2) as mean_ms,
  rows,
  left(query, ${QUERY_CHARS}) as query
from pg_stat_statements
where dbid = (select oid from pg_database where datname = current_database())
order by :"total_col" desc
limit ${LIMIT};
\else
do \$\$
begin
  raise exception 'pg_stat_statements extension is not enabled in this database.';
end
\$\$;
\endif
SQL
