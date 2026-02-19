#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIMIT="${1:-20}"
SCHEMA_FILTER="${DB_TABLE_SIZES_SCHEMA:-}"
MIN_BYTES="${DB_TABLE_SIZES_MIN_BYTES:-0}"
SCHEMA_FILTER_ENABLED=0
if [[ -n "$SCHEMA_FILTER" ]]; then
  SCHEMA_FILTER_ENABLED=1
fi

if ! [[ "$LIMIT" =~ ^[0-9]+$ ]]; then
  echo "Invalid limit: $LIMIT" >&2
  exit 1
fi

if ! [[ "$MIN_BYTES" =~ ^[0-9]+$ ]]; then
  echo "Invalid DB_TABLE_SIZES_MIN_BYTES: $MIN_BYTES" >&2
  exit 1
fi

"$SCRIPT_DIR/psql_with_ssl_fallback.sh" \
  -X \
  -v ON_ERROR_STOP=1 \
  -P pager=off \
  -v "schema_filter=${SCHEMA_FILTER}" \
  -v "schema_filter_enabled=${SCHEMA_FILTER_ENABLED}" \
  -v "min_bytes=${MIN_BYTES}" \
  <<SQL
with sized_tables as (
  select
    schemaname,
    relname,
    relid,
    pg_total_relation_size(relid) as total_bytes,
    pg_relation_size(relid) as table_bytes
  from pg_stat_user_tables
)
select
  schemaname,
  relname,
  pg_size_pretty(total_bytes) as total_size,
  pg_size_pretty(table_bytes) as table_size,
  pg_size_pretty(total_bytes - table_bytes) as index_size
from sized_tables
where total_bytes >= :min_bytes::bigint
  and (:schema_filter_enabled::int = 0 or schemaname = :'schema_filter')
order by total_bytes desc
limit ${LIMIT};
SQL
