#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  cat <<'EOF'
Usage: pg_stat_statements_top.sh [limit] [--all-dbs] [--full-query] [--query-chars N]

Defaults:
  - scope to current database only
  - truncate query text to 300 chars
EOF
}

limit="10"
all_dbs=0
full_query=0
query_chars="${DB_QUERY_TEXT_MAX_CHARS:-300}"

if [[ $# -gt 0 && "$1" =~ ^[0-9]+$ ]]; then
  limit="$1"
  shift
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --all-dbs)
      all_dbs=1
      ;;
    --full-query)
      full_query=1
      ;;
    --query-chars)
      query_chars="${2:-}"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
  shift
done

if ! [[ "$limit" =~ ^[0-9]+$ ]]; then
  echo "Invalid limit: $limit" >&2
  exit 1
fi

if ! [[ "$query_chars" =~ ^[0-9]+$ ]]; then
  echo "Invalid --query-chars value: $query_chars" >&2
  exit 1
fi

scope_clause="where dbid = (select oid from pg_database where datname = current_database())"
if [[ $all_dbs -eq 1 ]]; then
  scope_clause=""
fi

query_select="left(query, ${query_chars}) as query"
if [[ $full_query -eq 1 ]]; then
  query_select="query"
fi

"$SCRIPT_DIR/psql_with_ssl_fallback.sh" -v ON_ERROR_STOP=1 -X -P pager=off <<SQL
select
  exists(select 1 from pg_extension where extname = 'pg_stat_statements')::int as has_ext
\gset
\if :has_ext
select
  case
    when exists (
      select 1
      from information_schema.columns
      where table_name = 'pg_stat_statements'
        and column_name = 'total_exec_time'
    ) then 'total_exec_time'
    else 'total_time'
  end as total_col,
  case
    when exists (
      select 1
      from information_schema.columns
      where table_name = 'pg_stat_statements'
        and column_name = 'mean_exec_time'
    ) then 'mean_exec_time'
    else 'mean_time'
  end as mean_col
\gset
select
  calls,
  round(:"total_col"::numeric, 2) as total_time_ms,
  round(:"mean_col"::numeric, 2) as mean_time_ms,
  ${query_select}
from pg_stat_statements
${scope_clause}
order by :"total_col" desc
limit ${limit};
\else
do \$\$
begin
  raise exception 'pg_stat_statements extension is not enabled in this database.';
end
\$\$;
\endif
SQL
