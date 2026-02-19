#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIMIT="${1:-20}"

if ! [[ "$LIMIT" =~ ^[0-9]+$ ]]; then
  echo "Invalid limit: $LIMIT" >&2
  exit 1
fi

"$SCRIPT_DIR/psql_with_ssl_fallback.sh" \
  -X \
  -v ON_ERROR_STOP=1 \
  -P pager=off \
  <<SQL
\echo Missing index candidates (seq_scan >> idx_scan):
select
  schemaname,
  relname,
  seq_scan,
  idx_scan,
  n_live_tup
from pg_stat_user_tables
where seq_scan > idx_scan
  and n_live_tup > 10000
order by seq_scan desc
limit ${LIMIT};

\echo
\echo Unused indexes (non-unique, non-primary, zero scans):
with sized_indexes as (
  select
    s.schemaname,
    s.relname,
    s.indexrelname,
    s.idx_scan,
    pg_relation_size(s.indexrelid) as index_bytes
  from pg_stat_user_indexes s
  join pg_index i on i.indexrelid = s.indexrelid
  where s.idx_scan = 0
    and i.indisprimary = false
    and i.indisunique = false
)
select
  schemaname,
  relname,
  indexrelname,
  idx_scan,
  pg_size_pretty(index_bytes) as index_size
from sized_indexes
order by index_bytes desc
limit ${LIMIT};
SQL
