use crate::db::{DbClient, QueryExecution, QueryTable};
use anyhow::Result;

pub struct ToolSection {
    pub key: &'static str,
    pub title: &'static str,
    pub table: QueryTable,
}

impl ToolSection {
    fn new(key: &'static str, title: &'static str, table: QueryTable) -> Self {
        Self { key, title, table }
    }
}

pub async fn execute_sql(db: &DbClient, sql: &str) -> Result<QueryExecution> {
    db.simple_query(sql).await
}

pub async fn get_query_plan(db: &DbClient, sql: &str, analyze: bool) -> Result<QueryTable> {
    db.query(&format!("{} {sql}", query_plan_prefix(analyze)))
        .await
}

pub fn query_plan_prefix(analyze: bool) -> &'static str {
    if analyze {
        "EXPLAIN (ANALYZE, VERBOSE, COSTS, BUFFERS, FORMAT JSON)"
    } else {
        "EXPLAIN (VERBOSE, COSTS, FORMAT JSON)"
    }
}

pub async fn database_overview(db: &DbClient) -> Result<Vec<ToolSection>> {
    Ok(vec![
        ToolSection::new(
            "database",
            "Database",
            db.query("select current_database() as database, current_user as user_name, coalesce(inet_server_addr()::text, 'local') as host, coalesce(inet_server_port()::text, '') as port, current_setting('server_version') as server_version, pg_size_pretty(pg_database_size(current_database())) as database_size, current_setting('TimeZone') as timezone, current_setting('search_path') as search_path;").await?,
        ),
        ToolSection::new(
            "object_counts",
            "Object Counts",
            db.query("with user_schemas as (select oid, nspname from pg_namespace where nspname <> 'information_schema' and nspname not like 'pg_%') select 'schemas' as object_type, count(*)::text as count from user_schemas union all select 'tables', count(*)::text from pg_class c join user_schemas n on n.oid = c.relnamespace where c.relkind in ('r', 'p', 'f') union all select 'views', count(*)::text from pg_class c join user_schemas n on n.oid = c.relnamespace where c.relkind in ('v', 'm') union all select 'indexes', count(*)::text from pg_class c join user_schemas n on n.oid = c.relnamespace where c.relkind = 'i' union all select 'sequences', count(*)::text from pg_class c join user_schemas n on n.oid = c.relnamespace where c.relkind = 'S' union all select 'triggers', count(*)::text from pg_trigger t join pg_class c on c.oid = t.tgrelid join user_schemas n on n.oid = c.relnamespace where not t.tgisinternal union all select 'installed_extensions', count(*)::text from pg_extension order by object_type;").await?,
        ),
        ToolSection::new(
            "activity",
            "Activity",
            db.query("select 'connections_total' as metric, count(*)::text as value from pg_stat_activity where datname = current_database() union all select 'connections_active', count(*)::text from pg_stat_activity where datname = current_database() and state = 'active' union all select 'connections_idle', count(*)::text from pg_stat_activity where datname = current_database() and state = 'idle' union all select 'max_connections', setting from pg_settings where name = 'max_connections';").await?,
        ),
        ToolSection::new(
            "settings",
            "Key Settings",
            db.query("select name, setting, unit, vartype, context from pg_settings where name in ('max_connections', 'shared_buffers', 'effective_cache_size', 'work_mem', 'maintenance_work_mem', 'statement_timeout', 'lock_timeout', 'idle_in_transaction_session_timeout', 'autovacuum', 'track_counts') order by name;").await?,
        ),
    ])
}

pub async fn list_active_queries(db: &DbClient, limit: u32) -> Result<QueryTable> {
    db.query(&format!("select pid, usename as user_name, datname as database, state, wait_event_type, wait_event, now() - query_start as query_age, now() - xact_start as transaction_age, left(query, 300) as query from pg_stat_activity where pid <> pg_backend_pid() and state = 'active' order by query_start asc nulls last limit {limit};")).await
}

pub async fn list_tables(db: &DbClient) -> Result<QueryTable> {
    db.query("select n.nspname as table_schema, c.relname as table_name, case c.relkind when 'r' then 'base table' when 'p' then 'partitioned table' when 'f' then 'foreign table' else c.relkind::text end as table_type, pg_get_userbyid(c.relowner) as owner from pg_class c join pg_namespace n on n.oid = c.relnamespace where c.relkind in ('r', 'p', 'f') and n.nspname <> 'information_schema' and n.nspname not like 'pg_%' order by n.nspname, c.relname;").await
}

pub async fn list_views(db: &DbClient) -> Result<QueryTable> {
    db.query("select schemaname as view_schema, viewname as view_name, viewowner as owner, left(definition, 400) as definition from pg_views where schemaname <> 'information_schema' and schemaname not like 'pg_%' order by schemaname, viewname;").await
}

pub async fn list_schemas(db: &DbClient) -> Result<QueryTable> {
    db.query("select n.nspname as schema_name, pg_get_userbyid(n.nspowner) as owner, has_schema_privilege(n.oid, 'USAGE') as has_usage from pg_namespace n where n.nspname <> 'information_schema' and n.nspname not like 'pg_%' order by n.nspname;").await
}

pub async fn list_triggers(db: &DbClient) -> Result<QueryTable> {
    db.query("select n.nspname as table_schema, c.relname as table_name, t.tgname as trigger_name, pg_get_triggerdef(t.oid, true) as definition, t.tgenabled as enabled from pg_trigger t join pg_class c on c.oid = t.tgrelid join pg_namespace n on n.oid = c.relnamespace where not t.tgisinternal and n.nspname <> 'information_schema' and n.nspname not like 'pg_%' order by n.nspname, c.relname, t.tgname;").await
}

pub async fn list_indexes(db: &DbClient) -> Result<QueryTable> {
    db.query("select schemaname as table_schema, tablename as table_name, indexname as index_name, indexdef as definition from pg_indexes where schemaname <> 'information_schema' and schemaname not like 'pg_%' order by schemaname, tablename, indexname;").await
}

pub async fn list_sequences(db: &DbClient) -> Result<QueryTable> {
    db.query("select schemaname as sequence_schema, sequencename as sequence_name, sequenceowner as owner, data_type, start_value, min_value, max_value, increment_by, cycle, cache_size, last_value from pg_sequences where schemaname <> 'information_schema' and schemaname not like 'pg_%' order by schemaname, sequencename;").await
}

pub async fn list_available_extensions(db: &DbClient) -> Result<QueryTable> {
    db.query("select available.name, available.default_version, installed.extversion as installed_version, installed.extname is not null as installed, available.comment from pg_available_extensions available left join pg_extension installed on installed.extname = available.name order by available.name;").await
}

pub async fn list_installed_extensions(db: &DbClient) -> Result<QueryTable> {
    db.query("select ext.extname as extension_name, ext.extversion as version, ns.nspname as schema_name, ext.extrelocatable as relocatable from pg_extension ext join pg_namespace ns on ns.oid = ext.extnamespace order by ext.extname;").await
}

pub async fn list_autovacuum_configurations(db: &DbClient) -> Result<Vec<ToolSection>> {
    Ok(vec![
        ToolSection::new(
            "settings",
            "Autovacuum Settings",
            db.query("select name, setting, unit, vartype, context, short_desc from pg_settings where name like 'autovacuum%' or name in ('track_counts', 'vacuum_cost_delay', 'vacuum_cost_limit') order by name;").await?,
        ),
        ToolSection::new(
            "table_overrides",
            "Table Autovacuum Overrides",
            db.query("select n.nspname as table_schema, c.relname as table_name, array_to_string(c.reloptions, ', ') as reloptions from pg_class c join pg_namespace n on n.oid = c.relnamespace where c.relkind in ('r', 'p') and c.reloptions is not null and array_to_string(c.reloptions, ',') ilike '%autovacuum%' and n.nspname <> 'information_schema' and n.nspname not like 'pg_%' order by n.nspname, c.relname;").await?,
        ),
    ])
}

pub async fn list_memory_configurations(db: &DbClient) -> Result<QueryTable> {
    db.query("select name, setting, unit, vartype, context, short_desc from pg_settings where category ilike '%resource usage / memory%' or name in ('shared_buffers', 'effective_cache_size', 'work_mem', 'maintenance_work_mem', 'autovacuum_work_mem', 'temp_buffers', 'wal_buffers', 'logical_decoding_work_mem', 'max_stack_depth', 'hash_mem_multiplier') order by name;").await
}

pub async fn list_top_bloated_tables(db: &DbClient, limit: u32) -> Result<QueryTable> {
    db.query(&format!("select schemaname as table_schema, relname as table_name, n_live_tup, n_dead_tup, case when n_live_tup + n_dead_tup > 0 then round((100.0 * n_dead_tup / (n_live_tup + n_dead_tup))::numeric, 2) else 0 end as dead_tuple_pct, pg_size_pretty(pg_total_relation_size(relid)) as total_size, pg_total_relation_size(relid) as total_bytes from pg_stat_user_tables where n_dead_tup > 0 order by n_dead_tup desc, pg_total_relation_size(relid) desc limit {limit};")).await
}

pub async fn list_replication_slots(db: &DbClient) -> Result<QueryTable> {
    db.query("select slot_name, plugin, slot_type, database, temporary, active, active_pid, xmin, catalog_xmin, restart_lsn, confirmed_flush_lsn from pg_replication_slots order by slot_name;").await
}

pub async fn list_invalid_indexes(db: &DbClient) -> Result<QueryTable> {
    db.query("select ns.nspname as table_schema, tbl.relname as table_name, idx.relname as index_name, pg_get_indexdef(idx.oid) as definition, i.indisvalid as is_valid, i.indisready as is_ready, i.indislive as is_live from pg_index i join pg_class idx on idx.oid = i.indexrelid join pg_class tbl on tbl.oid = i.indrelid join pg_namespace ns on ns.oid = tbl.relnamespace where (not i.indisvalid or not i.indisready or not i.indislive) and ns.nspname <> 'information_schema' and ns.nspname not like 'pg_%' order by ns.nspname, tbl.relname, idx.relname;").await
}

#[cfg(test)]
mod tests {
    use super::query_plan_prefix;

    #[test]
    fn default_query_plan_does_not_execute_query() {
        assert_eq!(
            query_plan_prefix(false),
            "EXPLAIN (VERBOSE, COSTS, FORMAT JSON)"
        );
    }

    #[test]
    fn analyze_query_plan_includes_runtime_buffers() {
        assert_eq!(
            query_plan_prefix(true),
            "EXPLAIN (ANALYZE, VERBOSE, COSTS, BUFFERS, FORMAT JSON)"
        );
    }
}
