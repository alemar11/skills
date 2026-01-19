#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIMIT="${1:-20}"

echo "Missing index candidates (seq_scan >> idx_scan):"
"$SCRIPT_DIR/psql_with_ssl_fallback.sh" \
  -v ON_ERROR_STOP=1 \
  -P pager=off \
  -c "
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
limit ${LIMIT};"

echo ""
echo "Unused indexes (non-unique, non-primary, zero scans):"
"$SCRIPT_DIR/psql_with_ssl_fallback.sh" \
  -v ON_ERROR_STOP=1 \
  -P pager=off \
  -c "
select
  s.schemaname,
  s.relname,
  s.indexrelname,
  s.idx_scan,
  pg_size_pretty(pg_relation_size(s.indexrelid)) as index_size
from pg_stat_user_indexes s
join pg_index i on i.indexrelid = s.indexrelid
where s.idx_scan = 0
  and i.indisprimary = false
  and i.indisunique = false
order by pg_relation_size(s.indexrelid) desc
limit ${LIMIT};"
