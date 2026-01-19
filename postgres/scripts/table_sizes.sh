#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIMIT="${1:-20}"

"$SCRIPT_DIR/psql_with_ssl_fallback.sh" \
  -v ON_ERROR_STOP=1 \
  -P pager=off \
  -c "
select
  schemaname,
  relname,
  pg_size_pretty(pg_total_relation_size(relid)) as total_size,
  pg_size_pretty(pg_relation_size(relid)) as table_size,
  pg_size_pretty(pg_total_relation_size(relid) - pg_relation_size(relid)) as index_size
from pg_stat_user_tables
order by pg_total_relation_size(relid) desc
limit ${LIMIT};"
