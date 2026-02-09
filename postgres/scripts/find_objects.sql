\pset pager off
\pset format aligned
\pset border 2
\pset null '(null)'

-- Required: psql variable `pattern` (ILIKE pattern, e.g. %user%).
-- This query searches common schema objects by name.

WITH p AS (
  SELECT :'pattern'::text AS pat
)
SELECT *
FROM (
  -- Tables (includes partitioned tables)
  SELECT
    'table'::text AS object_type,
    n.nspname::text AS object_schema,
    c.relname::text AS object_name,
    CASE c.relkind
      WHEN 'r' THEN 'table'
      WHEN 'p' THEN 'partitioned table'
      ELSE c.relkind::text
    END AS details
  FROM pg_class c
  JOIN pg_namespace n ON n.oid = c.relnamespace
  WHERE c.relkind IN ('r', 'p')
    AND n.nspname <> 'information_schema'
    AND n.nspname NOT LIKE 'pg_%'
    AND c.relname ILIKE (SELECT pat FROM p)

  UNION ALL

  -- Views / materialized views
  SELECT
    CASE c.relkind
      WHEN 'v' THEN 'view'
      WHEN 'm' THEN 'matview'
      ELSE 'view'
    END AS object_type,
    n.nspname::text AS object_schema,
    c.relname::text AS object_name,
    left(pg_get_viewdef(c.oid, true), 200)::text AS details
  FROM pg_class c
  JOIN pg_namespace n ON n.oid = c.relnamespace
  WHERE c.relkind IN ('v', 'm')
    AND n.nspname <> 'information_schema'
    AND n.nspname NOT LIKE 'pg_%'
    AND c.relname ILIKE (SELECT pat FROM p)

  UNION ALL

  -- Sequences
  SELECT
    'sequence'::text AS object_type,
    n.nspname::text AS object_schema,
    c.relname::text AS object_name,
    'sequence'::text AS details
  FROM pg_class c
  JOIN pg_namespace n ON n.oid = c.relnamespace
  WHERE c.relkind = 'S'
    AND n.nspname <> 'information_schema'
    AND n.nspname NOT LIKE 'pg_%'
    AND c.relname ILIKE (SELECT pat FROM p)

  UNION ALL

  -- Indexes
  SELECT
    'index'::text AS object_type,
    n.nspname::text AS object_schema,
    c.relname::text AS object_name,
    left(pg_get_indexdef(c.oid), 200)::text AS details
  FROM pg_class c
  JOIN pg_namespace n ON n.oid = c.relnamespace
  WHERE c.relkind = 'i'
    AND n.nspname <> 'information_schema'
    AND n.nspname NOT LIKE 'pg_%'
    AND c.relname ILIKE (SELECT pat FROM p)

  UNION ALL

  -- Columns (table.column)
  SELECT
    'column'::text AS object_type,
    cols.table_schema::text AS object_schema,
    (cols.table_name || '.' || cols.column_name)::text AS object_name,
    (cols.data_type || COALESCE(' ' || cols.udt_name, ''))::text AS details
  FROM information_schema.columns cols
  WHERE cols.table_schema <> 'information_schema'
    AND cols.table_schema NOT LIKE 'pg_%'
    AND (
      cols.table_name ILIKE (SELECT pat FROM p)
      OR cols.column_name ILIKE (SELECT pat FROM p)
    )

  UNION ALL

  -- Functions / procedures (search by name only; print signature)
  SELECT
    CASE p.prokind
      WHEN 'p' THEN 'procedure'
      ELSE 'function'
    END AS object_type,
    n.nspname::text AS object_schema,
    p.proname::text AS object_name,
    (
      p.proname
      || '('
      || pg_get_function_identity_arguments(p.oid)
      || ') returns '
      || pg_get_function_result(p.oid)
    )::text AS details
  FROM pg_proc p
  JOIN pg_namespace n ON n.oid = p.pronamespace
  WHERE n.nspname <> 'information_schema'
    AND n.nspname NOT LIKE 'pg_%'
    AND p.proname ILIKE (SELECT pat FROM p)

  UNION ALL

  -- Triggers (search by trigger name; show table and function)
  SELECT
    'trigger'::text AS object_type,
    n.nspname::text AS object_schema,
    t.tgname::text AS object_name,
    (
      'on '
      || n.nspname
      || '.'
      || c.relname
      || ' -> '
      || pn.nspname
      || '.'
      || pr.proname
    )::text AS details
  FROM pg_trigger t
  JOIN pg_class c ON c.oid = t.tgrelid
  JOIN pg_namespace n ON n.oid = c.relnamespace
  JOIN pg_proc pr ON pr.oid = t.tgfoid
  JOIN pg_namespace pn ON pn.oid = pr.pronamespace
  WHERE NOT t.tgisinternal
    AND n.nspname <> 'information_schema'
    AND n.nspname NOT LIKE 'pg_%'
    AND t.tgname ILIKE (SELECT pat FROM p)

  UNION ALL

  -- Enums (search by type name; show values)
  SELECT
    'enum'::text AS object_type,
    n.nspname::text AS object_schema,
    t.typname::text AS object_name,
    left(string_agg(e.enumlabel, ', ' ORDER BY e.enumsortorder), 200)::text AS details
  FROM pg_type t
  JOIN pg_namespace n ON n.oid = t.typnamespace
  JOIN pg_enum e ON e.enumtypid = t.oid
  WHERE n.nspname <> 'information_schema'
    AND n.nspname NOT LIKE 'pg_%'
    AND t.typname ILIKE (SELECT pat FROM p)
  GROUP BY n.nspname, t.typname

  UNION ALL

  -- Types (domains/composites/ranges/etc, excluding enum which is covered above)
  SELECT
    'type'::text AS object_type,
    n.nspname::text AS object_schema,
    t.typname::text AS object_name,
    t.typtype::text AS details
  FROM pg_type t
  JOIN pg_namespace n ON n.oid = t.typnamespace
  WHERE n.nspname <> 'information_schema'
    AND n.nspname NOT LIKE 'pg_%'
    AND t.typtype <> 'e'
    AND t.typname ILIKE (SELECT pat FROM p)
) s
ORDER BY object_type, object_schema, object_name;
