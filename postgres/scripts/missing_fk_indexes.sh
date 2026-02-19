#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$SCRIPT_DIR/psql_with_ssl_fallback.sh" -v ON_ERROR_STOP=1 -X -c "
with fk_columns as (
  select
    c.conrelid,
    unnest(c.conkey) as attnum
  from pg_constraint c
  where c.contype = 'f'
),
indexed_columns as (
  select
    i.indrelid as conrelid,
    idx_col.attnum
  from pg_index i
  cross join lateral unnest(i.indkey) as idx_col(attnum)
  where idx_col.attnum > 0
)
select
  fk.conrelid::regclass as table_name,
  a.attname as fk_column
from fk_columns fk
join pg_attribute a
  on a.attrelid = fk.conrelid
 and a.attnum = fk.attnum
 and a.attisdropped = false
left join indexed_columns ic
  on ic.conrelid = fk.conrelid
 and ic.attnum = fk.attnum
where ic.attnum is null
order by table_name, fk_column;
"
