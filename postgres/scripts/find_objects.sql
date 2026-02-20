\pset pager off
\pset format aligned
\pset border 2
\pset null '(null)'

-- Required: psql variable `pattern` (ILIKE pattern, e.g. %user%).
-- Optional: psql variable `types` (comma-separated object_type filter).
-- This query searches common schema objects by name.

WITH p AS (
  SELECT
    :'pattern'::text AS pat,
    regexp_replace(lower(COALESCE(:'types', '')), '\s+', '', 'g')::text AS raw_types
),
f AS (
  SELECT
    CASE
      WHEN p.raw_types = '' THEN NULL::text[]
      ELSE regexp_split_to_array(p.raw_types, ',')
    END AS types
  FROM p
),
results AS (
  -- Schemas
  SELECT
    'schema'::text AS object_type,
    n.nspname::text AS object_schema,
    n.nspname::text AS object_name,
    'schema'::text AS details
  FROM pg_namespace n
  WHERE n.nspname <> 'information_schema'
    AND n.nspname NOT LIKE 'pg_%'
    AND (SELECT types IS NULL OR 'schema' = ANY(types) FROM f)
    AND n.nspname ILIKE (SELECT pat FROM p)

  UNION ALL

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
    AND (SELECT types IS NULL OR 'table' = ANY(types) FROM f)
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
    AND (
      SELECT types IS NULL OR 'view' = ANY(types) OR 'matview' = ANY(types)
      FROM f
    )
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
    AND (SELECT types IS NULL OR 'sequence' = ANY(types) FROM f)
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
    AND (SELECT types IS NULL OR 'index' = ANY(types) FROM f)
    AND c.relname ILIKE (SELECT pat FROM p)

  UNION ALL

  -- Constraints
  SELECT
    'constraint'::text AS object_type,
    n.nspname::text AS object_schema,
    con.conname::text AS object_name,
    (
      CASE con.contype
        WHEN 'p' THEN 'primary key'
        WHEN 'f' THEN 'foreign key'
        WHEN 'u' THEN 'unique'
        WHEN 'c' THEN 'check'
        WHEN 'x' THEN 'exclusion'
        ELSE con.contype::text
      END
      || COALESCE(' on ' || nr.nspname || '.' || cr.relname, '')
    )::text AS details
  FROM pg_constraint con
  JOIN pg_namespace n ON n.oid = con.connamespace
  LEFT JOIN pg_class cr ON cr.oid = con.conrelid
  LEFT JOIN pg_namespace nr ON nr.oid = cr.relnamespace
  WHERE n.nspname <> 'information_schema'
    AND n.nspname NOT LIKE 'pg_%'
    AND (SELECT types IS NULL OR 'constraint' = ANY(types) FROM f)
    AND (
      con.conname ILIKE (SELECT pat FROM p)
      OR cr.relname ILIKE (SELECT pat FROM p)
    )

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
    AND (SELECT types IS NULL OR 'column' = ANY(types) FROM f)
    AND (
      cols.table_name ILIKE (SELECT pat FROM p)
      OR cols.column_name ILIKE (SELECT pat FROM p)
    )

  UNION ALL

  -- Functions / procedures (search by name only; print signature)
  SELECT
    CASE proc.prokind
      WHEN 'p' THEN 'procedure'
      ELSE 'function'
    END AS object_type,
    n.nspname::text AS object_schema,
    proc.proname::text AS object_name,
    (
      proc.proname
      || '('
      || pg_get_function_identity_arguments(proc.oid)
      || ') returns '
      || pg_get_function_result(proc.oid)
    )::text AS details
  FROM pg_proc proc
  JOIN pg_namespace n ON n.oid = proc.pronamespace
  WHERE n.nspname <> 'information_schema'
    AND n.nspname NOT LIKE 'pg_%'
    AND (
      SELECT types IS NULL OR 'function' = ANY(types) OR 'procedure' = ANY(types)
      FROM f
    )
    AND proc.proname ILIKE (SELECT pat FROM p)

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
    AND (SELECT types IS NULL OR 'trigger' = ANY(types) FROM f)
    AND (
      t.tgname ILIKE (SELECT pat FROM p)
      OR c.relname ILIKE (SELECT pat FROM p)
    )

  UNION ALL

  -- Rules
  SELECT
    'rule'::text AS object_type,
    n.nspname::text AS object_schema,
    r.rulename::text AS object_name,
    left(pg_get_ruledef(r.oid, true), 200)::text AS details
  FROM pg_rewrite r
  JOIN pg_class c ON c.oid = r.ev_class
  JOIN pg_namespace n ON n.oid = c.relnamespace
  WHERE r.rulename <> '_RETURN'
    AND n.nspname <> 'information_schema'
    AND n.nspname NOT LIKE 'pg_%'
    AND (SELECT types IS NULL OR 'rule' = ANY(types) FROM f)
    AND (
      r.rulename ILIKE (SELECT pat FROM p)
      OR c.relname ILIKE (SELECT pat FROM p)
    )

  UNION ALL

  -- RLS policies
  SELECT
    'policy'::text AS object_type,
    n.nspname::text AS object_schema,
    pol.polname::text AS object_name,
    (
      'on '
      || n.nspname
      || '.'
      || c.relname
      || COALESCE(' using ' || pg_get_expr(pol.polqual, pol.polrelid), '')
      || COALESCE(' check ' || pg_get_expr(pol.polwithcheck, pol.polrelid), '')
    )::text AS details
  FROM pg_policy pol
  JOIN pg_class c ON c.oid = pol.polrelid
  JOIN pg_namespace n ON n.oid = c.relnamespace
  WHERE n.nspname <> 'information_schema'
    AND n.nspname NOT LIKE 'pg_%'
    AND (SELECT types IS NULL OR 'policy' = ANY(types) FROM f)
    AND (
      pol.polname ILIKE (SELECT pat FROM p)
      OR c.relname ILIKE (SELECT pat FROM p)
    )

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
    AND (SELECT types IS NULL OR 'enum' = ANY(types) FROM f)
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
    AND (SELECT types IS NULL OR 'type' = ANY(types) FROM f)
    AND t.typname ILIKE (SELECT pat FROM p)

  UNION ALL

  -- Extensions
  SELECT
    'extension'::text AS object_type,
    n.nspname::text AS object_schema,
    ext.extname::text AS object_name,
    ('version=' || ext.extversion || ', relocatable=' || ext.extrelocatable)::text AS details
  FROM pg_extension ext
  JOIN pg_namespace n ON n.oid = ext.extnamespace
  WHERE n.nspname <> 'information_schema'
    AND n.nspname NOT LIKE 'pg_%'
    AND (SELECT types IS NULL OR 'extension' = ANY(types) FROM f)
    AND ext.extname ILIKE (SELECT pat FROM p)

  UNION ALL

  -- Collations
  SELECT
    'collation'::text AS object_type,
    n.nspname::text AS object_schema,
    coll.collname::text AS object_name,
    (
      'provider='
      || CASE coll.collprovider
        WHEN 'c' THEN 'libc'
        WHEN 'i' THEN 'icu'
        WHEN 'd' THEN 'default'
        ELSE coll.collprovider::text
      END
      || ', locale='
      || COALESCE(coll.collcollate, coll.collctype, '(default)')
    )::text AS details
  FROM pg_collation coll
  JOIN pg_namespace n ON n.oid = coll.collnamespace
  WHERE n.nspname <> 'information_schema'
    AND n.nspname NOT LIKE 'pg_%'
    AND (SELECT types IS NULL OR 'collation' = ANY(types) FROM f)
    AND coll.collname ILIKE (SELECT pat FROM p)

  UNION ALL

  -- Operators
  SELECT
    'operator'::text AS object_type,
    n.nspname::text AS object_schema,
    op.oprname::text AS object_name,
    (
      CASE WHEN op.oprleft = 0 THEN 'none' ELSE format_type(op.oprleft, NULL) END
      || ' ' || op.oprname || ' '
      || CASE WHEN op.oprright = 0 THEN 'none' ELSE format_type(op.oprright, NULL) END
      || ' -> '
      || format_type(op.oprresult, NULL)
    )::text AS details
  FROM pg_operator op
  JOIN pg_namespace n ON n.oid = op.oprnamespace
  WHERE n.nspname <> 'information_schema'
    AND n.nspname NOT LIKE 'pg_%'
    AND (SELECT types IS NULL OR 'operator' = ANY(types) FROM f)
    AND op.oprname ILIKE (SELECT pat FROM p)

  UNION ALL

  -- Operator classes
  SELECT
    'operator_class'::text AS object_type,
    n.nspname::text AS object_schema,
    opc.opcname::text AS object_name,
    am.amname::text AS details
  FROM pg_opclass opc
  JOIN pg_namespace n ON n.oid = opc.opcnamespace
  JOIN pg_am am ON am.oid = opc.opcmethod
  WHERE n.nspname <> 'information_schema'
    AND n.nspname NOT LIKE 'pg_%'
    AND (SELECT types IS NULL OR 'operator_class' = ANY(types) FROM f)
    AND opc.opcname ILIKE (SELECT pat FROM p)

  UNION ALL

  -- Operator families
  SELECT
    'operator_family'::text AS object_type,
    n.nspname::text AS object_schema,
    opf.opfname::text AS object_name,
    am.amname::text AS details
  FROM pg_opfamily opf
  JOIN pg_namespace n ON n.oid = opf.opfnamespace
  JOIN pg_am am ON am.oid = opf.opfmethod
  WHERE n.nspname <> 'information_schema'
    AND n.nspname NOT LIKE 'pg_%'
    AND (SELECT types IS NULL OR 'operator_family' = ANY(types) FROM f)
    AND opf.opfname ILIKE (SELECT pat FROM p)

  UNION ALL

  -- Foreign data wrappers
  SELECT
    'fdw'::text AS object_type,
    '(global)'::text AS object_schema,
    fdw.fdwname::text AS object_name,
    COALESCE(array_to_string(fdw.fdwoptions, ', '), 'fdw')::text AS details
  FROM pg_foreign_data_wrapper fdw
  WHERE (SELECT types IS NULL OR 'fdw' = ANY(types) FROM f)
    AND fdw.fdwname ILIKE (SELECT pat FROM p)

  UNION ALL

  -- Foreign servers
  SELECT
    'foreign_server'::text AS object_type,
    '(global)'::text AS object_schema,
    srv.srvname::text AS object_name,
    (
      'fdw='
      || fdw.fdwname
      || COALESCE(', options=' || array_to_string(srv.srvoptions, ', '), '')
    )::text AS details
  FROM pg_foreign_server srv
  JOIN pg_foreign_data_wrapper fdw ON fdw.oid = srv.srvfdw
  WHERE (SELECT types IS NULL OR 'foreign_server' = ANY(types) FROM f)
    AND srv.srvname ILIKE (SELECT pat FROM p)

  UNION ALL

  -- User mappings
  SELECT
    'user_mapping'::text AS object_type,
    '(global)'::text AS object_schema,
    (COALESCE(um.usename, 'PUBLIC') || '@' || um.srvname)::text AS object_name,
    COALESCE(array_to_string(um.umoptions, ', '), 'user mapping')::text AS details
  FROM pg_user_mappings um
  WHERE (SELECT types IS NULL OR 'user_mapping' = ANY(types) FROM f)
    AND (
    um.srvname ILIKE (SELECT pat FROM p)
    OR um.usename ILIKE (SELECT pat FROM p)
    )

  UNION ALL

  -- Event triggers
  SELECT
    'event_trigger'::text AS object_type,
    '(global)'::text AS object_schema,
    et.evtname::text AS object_name,
    ('event=' || et.evtevent)::text AS details
  FROM pg_event_trigger et
  WHERE (SELECT types IS NULL OR 'event_trigger' = ANY(types) FROM f)
    AND et.evtname ILIKE (SELECT pat FROM p)

  UNION ALL

  -- Publications
  SELECT
    'publication'::text AS object_type,
    '(global)'::text AS object_schema,
    pub.pubname::text AS object_name,
    (
      'all_tables=' || pub.puballtables
      || ', insert=' || pub.pubinsert
      || ', update=' || pub.pubupdate
      || ', delete=' || pub.pubdelete
      || ', truncate=' || pub.pubtruncate
    )::text AS details
  FROM pg_publication pub
  WHERE (SELECT types IS NULL OR 'publication' = ANY(types) FROM f)
    AND pub.pubname ILIKE (SELECT pat FROM p)
)
SELECT r.object_type, r.object_schema, r.object_name, r.details
FROM results r
ORDER BY r.object_type, r.object_schema, r.object_name;
