#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/pg_env.sh"

eval "$("$SCRIPT_DIR/resolve_db_url.sh")"

psql "$DB_URL" -v ON_ERROR_STOP=1 -X -c "
select
  relname,
  n_live_tup,
  n_dead_tup,
  last_vacuum,
  last_autovacuum,
  last_analyze,
  last_autoanalyze
from pg_stat_user_tables
order by last_analyze nulls first;
"
