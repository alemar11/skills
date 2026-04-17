use anyhow::{Context, Result, anyhow, bail};
use clap::Parser;
use postgres_skill_cli::cli::*;
use postgres_skill_cli::config::{
    RuntimeOptions, application_name, bootstrap_profile, canonical_config_path,
    load_and_migrate_config, runtime_context, update_sslmode,
};
use postgres_skill_cli::db::{
    DbClient, QueryTable, escape_literal, expect_non_empty, table_to_json,
};
use postgres_skill_cli::docs;
use postgres_skill_cli::migration::{apply_release, build_release_plan};
use postgres_skill_cli::output::{print_json, render_table};
use postgres_skill_cli::tooling::{ToolBackend, ensure_backend};
use postgresql_commands::pg_dump::PgDumpBuilder;
use postgresql_commands::pg_restore::PgRestoreBuilder;
use postgresql_commands::{CommandBuilder, CommandExecutor};
use serde_json::{Value, json};
use std::env;
use std::fs;
use std::io::{self, IsTerminal, Read, Write};
use std::path::{Path, PathBuf};

#[tokio::main]
async fn main() {
    let cli = Cli::parse();
    if let Err(error) = run(&cli).await {
        if cli.json {
            let payload = json!({
                "error": {
                    "message": sanitize_error_message(&format!("{error:#}")),
                }
            });
            if let Err(json_error) = print_json(&payload) {
                eprintln!("{json_error:#}");
            }
        } else {
            eprintln!("{}", sanitize_error_message(&format!("{error:#}")));
        }
        std::process::exit(1);
    }
}

async fn run(cli: &Cli) -> Result<()> {
    let manifest_dir = Path::new(env!("CARGO_MANIFEST_DIR"));
    let skill_root = manifest_dir
        .parent()
        .and_then(|path| path.parent())
        .ok_or_else(|| anyhow!("Failed to resolve postgres skill root from project layout."))?;

    match &cli.command {
        Command::Doctor => doctor(&cli, skill_root).await,
        Command::Profile(command) => profile(&cli, command, skill_root).await,
        Command::Query(command) => query(&cli, command, skill_root).await,
        Command::Activity(command) => activity(&cli, command, skill_root).await,
        Command::Schema(command) => schema(&cli, command, skill_root).await,
        Command::Dump(command) => dump(&cli, command, skill_root).await,
        Command::Migration(command) => migration(&cli, command, skill_root).await,
        Command::Docs(command) => docs_command(&cli, command).await,
    }
}

fn sanitize_error_message(message: &str) -> String {
    let postgres_url =
        regex::Regex::new(r"(?i)(postgres(?:ql)?://[^:/\s?#]+:)([^@/\s?#]+)@").unwrap();
    let key_value_password =
        regex::Regex::new(r"(?i)\b(password|pgpassword)\s*=\s*([^ \n\r\t;]+)").unwrap();

    let masked_url = postgres_url.replace_all(message, "$1***@");
    let masked_password = key_value_password.replace_all(&masked_url, "$1=***");
    masked_password.into_owned()
}

#[cfg(test)]
mod tests {
    use super::sanitize_error_message;

    #[test]
    fn masks_password_in_postgres_url() {
        let message = "Failed to connect to postgresql://postgres:secret@localhost:5432/app";
        assert_eq!(
            sanitize_error_message(message),
            "Failed to connect to postgresql://postgres:***@localhost:5432/app"
        );
    }

    #[test]
    fn masks_password_key_value_pairs() {
        let message = "password=secret PGPASSWORD=hunter2";
        assert_eq!(
            sanitize_error_message(message),
            "password=*** PGPASSWORD=***"
        );
    }
}

async fn doctor(cli: &Cli, skill_root: &Path) -> Result<()> {
    let runtime = runtime_context(
        &RuntimeOptions {
            project_root_override: cli.project_root.clone(),
            profile_override: cli.profile.clone(),
            url_override: cli.url.clone(),
        },
        skill_root,
    );
    let runtime_info = match runtime {
        Ok(ctx) => Some(ctx),
        Err(_) => None,
    };

    let tools = if let Some(ctx) = &runtime_info {
        Some(ensure_backend(ctx, skill_root).await?.status())
    } else {
        None
    };

    let output = json!({
        "application_name": application_name(),
        "runtime": runtime_info,
        "managed_tools": tools,
    });
    if cli.json {
        print_json(&output)
    } else {
        println!("{}", serde_json::to_string_pretty(&output)?);
        Ok(())
    }
}

async fn profile(cli: &Cli, command: &ProfileCommand, skill_root: &Path) -> Result<()> {
    match &command.command {
        ProfileSubcommand::Bootstrap(args) => {
            let project_root = postgres_skill_cli::config::resolve_project_root(
                cli.project_root.clone(),
                skill_root,
            )?;
            let config_path = canonical_config_path(&project_root);
            let resolved = bootstrap_profile(&config_path, args.save)?;
            let output = json!({
                "profile": resolved.name,
                "url": resolved.url,
                "saved": args.save,
                "config_path": config_path,
                "toml_path": config_path,
            });
            if cli.json {
                print_json(&output)
            } else {
                println!("{}", serde_json::to_string_pretty(&output)?);
                Ok(())
            }
        }
        ProfileSubcommand::MigrateToml => {
            let project_root = postgres_skill_cli::config::resolve_project_root(
                cli.project_root.clone(),
                skill_root,
            )?;
            let config_path = canonical_config_path(&project_root);
            let config = load_and_migrate_config(&config_path)?;
            let output = json!({
                "config_path": config_path,
                "toml_path": config_path,
                "schema_version": config.schema_version,
            });
            if cli.json {
                print_json(&output)
            } else {
                println!("{}", serde_json::to_string_pretty(&output)?);
                Ok(())
            }
        }
        ProfileSubcommand::SetSsl(args) => {
            let project_root = postgres_skill_cli::config::resolve_project_root(
                cli.project_root.clone(),
                skill_root,
            )?;
            let config_path = canonical_config_path(&project_root);
            let enabled = postgres_skill_cli::config::parse_sslmode_bool(&args.sslmode)?;
            update_sslmode(&config_path, &args.profile, enabled)?;
            let output = json!({
                "config_path": config_path,
                "toml_path": config_path,
                "profile": args.profile,
                "sslmode": if enabled { "require" } else { "disable" },
            });
            if cli.json {
                print_json(&output)
            } else {
                println!("{}", serde_json::to_string_pretty(&output)?);
                Ok(())
            }
        }
        ProfileSubcommand::Resolve => {
            let ctx = runtime_context(
                &RuntimeOptions {
                    project_root_override: cli.project_root.clone(),
                    profile_override: cli.profile.clone(),
                    url_override: cli.url.clone(),
                },
                skill_root,
            )?;
            if cli.json {
                print_json(&ctx)
            } else {
                println!("DB_URL={:?}", ctx.url);
                println!("DB_SSLMODE={}", ctx.sslmode);
                println!("DB_PROFILE={}", ctx.profile_name);
                println!("DB_URL_SOURCE={}", ctx.url_source);
                if let Some(path) = ctx.config_path {
                    println!("DB_CONFIG_PATH={}", path.display());
                }
                Ok(())
            }
        }
        ProfileSubcommand::Test => {
            let db = db_client(cli, skill_root).await?;
            db.execute("select 1;").await?;
            let output = json!({
                "status": "ok",
                "profile": db.context().profile_name,
            });
            if cli.json {
                print_json(&output)
            } else {
                println!("Connection OK (profile: {})", db.context().profile_name);
                Ok(())
            }
        }
        ProfileSubcommand::Info => {
            let db = db_client(cli, skill_root).await?;
            let table = db
                .query(
                    "select 'database' as key, current_database() as value
union all select 'user', current_user
union all select 'host', coalesce(inet_server_addr()::text, 'local')
union all select 'port', coalesce(inet_server_port()::text, '')
union all select 'server_version', current_setting('server_version')
union all select 'search_path', current_setting('search_path')
union all select 'default_transaction_read_only', current_setting('default_transaction_read_only')
union all select 'timezone', current_setting('TimeZone')
union all select 'application_name', current_setting('application_name');",
                )
                .await?;
            render(
                cli.json,
                json!({"info": table_to_json(&table)}),
                &[("Connection Info", table)],
            )
        }
        ProfileSubcommand::Version => {
            let db = db_client(cli, skill_root).await?;
            let table = db.query("show server_version;").await?;
            expect_non_empty(&table, "No version returned.")?;
            let version = table.rows[0][0].clone().unwrap_or_default();
            if cli.json {
                print_json(&json!({ "server_version": version }))
            } else {
                println!("{version}");
                Ok(())
            }
        }
    }
}

async fn query(cli: &Cli, command: &QueryCommand, skill_root: &Path) -> Result<()> {
    let db = db_client(cli, skill_root).await?;
    match &command.command {
        QuerySubcommand::Run(args) => {
            let sql = read_sql_input(args)?;
            let table = db.query(&sql).await?;
            render(
                cli.json,
                json!({"query": sql, "result": table_to_json(&table)}),
                &[("Result", table)],
            )
        }
        QuerySubcommand::Explain(args) => {
            let sql = read_sql_input(&args.sql)?;
            let prefix = if args.no_analyze {
                "EXPLAIN (VERBOSE, COSTS, BUFFERS, FORMAT TEXT)"
            } else {
                "EXPLAIN (ANALYZE, VERBOSE, COSTS, BUFFERS, FORMAT TEXT)"
            };
            let table = db.query(&format!("{prefix} {sql}")).await?;
            render(
                cli.json,
                json!({"plan": table_to_json(&table)}),
                &[("Explain", table)],
            )
        }
        QuerySubcommand::Find(args) => {
            let pattern = escape_literal(&format!("%{}%", args.pattern));
            let types = args.types.clone().unwrap_or_default();
            let table = db
                .query(&format!(
                    "with p as (
  select '{pattern}'::text as pat,
         regexp_replace(lower('{types}'), '\\s+', '', 'g')::text as raw_types
),
f as (
  select case when p.raw_types = '' then null::text[] else regexp_split_to_array(p.raw_types, ',') end as types from p
),
results as (
  select 'schema'::text as object_type, n.nspname::text as object_schema, n.nspname::text as object_name, 'schema'::text as details
  from pg_namespace n
  where n.nspname <> 'information_schema' and n.nspname not like 'pg_%'
    and (select types is null or 'schema' = any(types) from f)
    and n.nspname ilike (select pat from p)
  union all
  select 'table', n.nspname::text, c.relname::text,
         case c.relkind when 'r' then 'table' when 'p' then 'partitioned table' else c.relkind::text end
  from pg_class c join pg_namespace n on n.oid = c.relnamespace
  where c.relkind in ('r', 'p')
    and n.nspname <> 'information_schema' and n.nspname not like 'pg_%'
    and (select types is null or 'table' = any(types) from f)
    and c.relname ilike (select pat from p)
  union all
  select 'column', cols.table_schema::text, (cols.table_name || '.' || cols.column_name)::text,
         (cols.data_type || coalesce(' ' || cols.udt_name, ''))::text
  from information_schema.columns cols
  where cols.table_schema <> 'information_schema' and cols.table_schema not like 'pg_%'
    and (select types is null or 'column' = any(types) from f)
    and (cols.table_name ilike (select pat from p) or cols.column_name ilike (select pat from p))
  union all
  select case proc.prokind when 'p' then 'procedure' else 'function' end,
         n.nspname::text,
         proc.proname::text,
         (proc.proname || '(' || pg_get_function_identity_arguments(proc.oid) || ') returns ' || pg_get_function_result(proc.oid))::text
  from pg_proc proc
  join pg_namespace n on n.oid = proc.pronamespace
  where n.nspname <> 'information_schema' and n.nspname not like 'pg_%'
    and (select types is null or 'function' = any(types) or 'procedure' = any(types) from f)
    and proc.proname ilike (select pat from p)
)
select object_type, object_schema, object_name, details
from results
order by object_type, object_schema, object_name;"
                ))
                .await?;
            render(
                cli.json,
                json!({"matches": table_to_json(&table)}),
                &[("Matches", table)],
            )
        }
    }
}

async fn activity(cli: &Cli, command: &ActivityCommand, skill_root: &Path) -> Result<()> {
    let db = db_client(cli, skill_root).await?;
    match &command.command {
        ActivitySubcommand::Overview(args) => {
            let table = db.query(&format!("select pid, usename as user_name, datname as db, state, wait_event_type, wait_event, now() - query_start as query_age, now() - xact_start as xact_age, left(query, 200) as query from pg_stat_activity where pid <> pg_backend_pid() and state <> 'idle' order by query_start desc nulls last limit {};", args.limit)).await?;
            render(
                cli.json,
                json!({"activity": table_to_json(&table)}),
                &[("Activity", table)],
            )
        }
        ActivitySubcommand::Locks => {
            let table = db.query("select blocked.pid as blocked_pid, blocked.usename as blocked_user, blocking.pid as blocking_pid, blocking.usename as blocking_user, now() - blocked.query_start as blocked_duration, blocked.query as blocked_query, blocking.query as blocking_query from pg_stat_activity blocked join pg_stat_activity blocking on blocking.pid = any(pg_blocking_pids(blocked.pid)) order by blocked_duration desc;").await?;
            render(
                cli.json,
                json!({"locks": table_to_json(&table)}),
                &[("Locks", table)],
            )
        }
        ActivitySubcommand::Slow(args) | ActivitySubcommand::PgStatTop(args) => {
            let column_choice = db.query("select case when exists (select 1 from information_schema.columns where table_name = 'pg_stat_statements' and column_name = 'total_exec_time') then 'total_exec_time' else 'total_time' end as total_col, case when exists (select 1 from information_schema.columns where table_name = 'pg_stat_statements' and column_name = 'mean_exec_time') then 'mean_exec_time' else 'mean_time' end as mean_col;").await?;
            expect_non_empty(&column_choice, "pg_stat_statements metadata not available.")?;
            let total = column_choice.rows[0][0]
                .clone()
                .unwrap_or_else(|| "total_exec_time".to_string());
            let mean = column_choice.rows[0][1]
                .clone()
                .unwrap_or_else(|| "mean_exec_time".to_string());
            let chars = env::var("DB_QUERY_TEXT_MAX_CHARS").unwrap_or_else(|_| "300".to_string());
            let table = db.query(&format!("select calls, round({total}::numeric, 2) as total_ms, round({mean}::numeric, 2) as mean_ms, rows, left(query, {chars}) as query from pg_stat_statements where dbid = (select oid from pg_database where datname = current_database()) order by {total} desc limit {};", args.limit)).await?;
            render(
                cli.json,
                json!({"slow_queries": table_to_json(&table)}),
                &[("Slow Queries", table)],
            )
        }
        ActivitySubcommand::LongRunning(args) => {
            let table = db.query(&format!("select pid, usename as user_name, datname as db, state, now() - query_start as query_age, left(query, 200) as query from pg_stat_activity where state = 'active' and query_start is not null and now() - query_start > interval '{} minutes' order by query_start asc limit {};", args.minutes, args.limit)).await?;
            render(
                cli.json,
                json!({"long_running": table_to_json(&table)}),
                &[("Long Running Queries", table)],
            )
        }
        ActivitySubcommand::Cancel(args) => {
            destructive_activity(cli, &db, "pg_cancel_backend", args).await
        }
        ActivitySubcommand::Terminate(args) => {
            destructive_activity(cli, &db, "pg_terminate_backend", args).await
        }
        ActivitySubcommand::CancelPid(args) => {
            destructive_pids(cli, &db, "pg_cancel_backend", &args.pid, args.yes).await
        }
        ActivitySubcommand::TerminatePid(args) => {
            destructive_pids(cli, &db, "pg_terminate_backend", &args.pid, args.yes).await
        }
    }
}

async fn schema(cli: &Cli, command: &SchemaCommand, skill_root: &Path) -> Result<()> {
    let db = db_client(cli, skill_root).await?;
    match &command.command {
        SchemaSubcommand::Inspect => schema_inspect(cli, &db).await,
        SchemaSubcommand::Diff(args) => schema_diff(cli, skill_root, args).await,
        SchemaSubcommand::Dump(args) => dump_schema(cli, skill_root, args, true).await,
        SchemaSubcommand::TableSizes(args) => {
            let table = db.query(&format!("with sized_tables as (select schemaname, relname, relid, pg_total_relation_size(relid) as total_bytes, pg_relation_size(relid) as table_bytes from pg_stat_user_tables) select schemaname, relname, pg_size_pretty(total_bytes) as total_size, pg_size_pretty(table_bytes) as table_size, pg_size_pretty(total_bytes - table_bytes) as index_size from sized_tables order by total_bytes desc limit {};", args.limit)).await?;
            render(
                cli.json,
                json!({"table_sizes": table_to_json(&table)}),
                &[("Table Sizes", table)],
            )
        }
        SchemaSubcommand::IndexHealth(args) => {
            let missing = db.query(&format!("select schemaname, relname, seq_scan, idx_scan, n_live_tup from pg_stat_user_tables where seq_scan > idx_scan and n_live_tup > 10000 order by seq_scan desc limit {};", args.limit)).await?;
            let unused = db.query(&format!("with sized_indexes as (select s.schemaname, s.relname, s.indexrelname, s.idx_scan, pg_relation_size(s.indexrelid) as index_bytes from pg_stat_user_indexes s join pg_index i on i.indexrelid = s.indexrelid where s.idx_scan = 0 and i.indisprimary = false and i.indisunique = false) select schemaname, relname, indexrelname, idx_scan, pg_size_pretty(index_bytes) as index_size from sized_indexes order by index_bytes desc limit {};", args.limit)).await?;
            if cli.json {
                print_json(&json!({
                    "missing_index_candidates": table_to_json(&missing),
                    "unused_indexes": table_to_json(&unused)
                }))
            } else {
                println!(
                    "{}",
                    render_table(&missing, Some("Missing Index Candidates"))
                );
                println!();
                println!("{}", render_table(&unused, Some("Unused Indexes")));
                Ok(())
            }
        }
        SchemaSubcommand::MissingFkIndexes => {
            let table = db.query("with fk_constraints as (select c.oid as constraint_oid, c.conrelid, c.conname, c.conkey as fk_attnums, array_agg(a.attname order by cols.ordinality) as fk_columns from pg_constraint c join lateral unnest(c.conkey) with ordinality as cols(attnum, ordinality) on true join pg_attribute a on a.attrelid = c.conrelid and a.attnum = cols.attnum and a.attisdropped = false where c.contype = 'f' group by c.oid, c.conrelid, c.conname, c.conkey), supporting_indexes as (select i.indrelid as conrelid, array_agg(idx_col.attnum order by idx_col.ordinality) filter (where idx_col.ordinality <= i.indnkeyatts and idx_col.attnum > 0) as index_key_attnums from pg_index i cross join lateral unnest(i.indkey::smallint[]) with ordinality as idx_col(attnum, ordinality) where i.indpred is null and i.indisvalid and i.indisready group by i.indrelid, i.indexrelid, i.indnkeyatts) select fk.conrelid::regclass as table_name, fk.conname as constraint_name, array_to_string(fk.fk_columns, ', ') as fk_columns from fk_constraints fk where not exists (select 1 from supporting_indexes si where si.conrelid = fk.conrelid and array_length(si.index_key_attnums, 1) >= array_length(fk.fk_attnums, 1) and si.index_key_attnums[1:array_length(fk.fk_attnums, 1)] = fk.fk_attnums) order by table_name::text, constraint_name;").await?;
            render(
                cli.json,
                json!({"missing_fk_indexes": table_to_json(&table)}),
                &[("Missing FK Indexes", table)],
            )
        }
        SchemaSubcommand::VacuumStatus => {
            let table = db.query("select relname, n_live_tup, n_dead_tup, last_vacuum, last_autovacuum, last_analyze, last_autoanalyze from pg_stat_user_tables order by last_analyze nulls first;").await?;
            render(
                cli.json,
                json!({"vacuum_status": table_to_json(&table)}),
                &[("Vacuum / Analyze Status", table)],
            )
        }
        SchemaSubcommand::Roles => {
            let table = db.query("with roles as (select r.oid, r.rolname, r.rolcanlogin, r.rolsuper, r.rolcreatedb, r.rolcreaterole, r.rolinherit, r.rolreplication, r.rolbypassrls, r.rolconnlimit, r.rolvaliduntil from pg_roles r) select r.rolname as role, r.rolcanlogin as can_login, r.rolsuper as superuser, r.rolcreatedb as createdb, r.rolcreaterole as createrole, r.rolinherit as inherit, r.rolreplication as replication, r.rolbypassrls as bypassrls, r.rolconnlimit as conn_limit, r.rolvaliduntil as valid_until, coalesce(string_agg(m.rolname, ', ' order by m.rolname), '') as member_of from roles r left join pg_auth_members am on am.member = r.oid left join pg_roles m on m.oid = am.roleid group by r.rolname, r.rolcanlogin, r.rolsuper, r.rolcreatedb, r.rolcreaterole, r.rolinherit, r.rolreplication, r.rolbypassrls, r.rolconnlimit, r.rolvaliduntil order by r.rolname;").await?;
            render(
                cli.json,
                json!({"roles": table_to_json(&table)}),
                &[("Roles", table)],
            )
        }
    }
}

async fn dump(cli: &Cli, command: &DumpCommand, skill_root: &Path) -> Result<()> {
    match &command.command {
        DumpSubcommand::Schema(args) => dump_schema(cli, skill_root, args, true).await,
        DumpSubcommand::Data(args) => dump_schema(cli, skill_root, args, false).await,
        DumpSubcommand::Restore(args) => dump_restore(cli, skill_root, args).await,
    }
}

async fn migration(cli: &Cli, command: &MigrationCommand, skill_root: &Path) -> Result<()> {
    match &command.command {
        MigrationSubcommand::Release(args) => {
            let ctx = runtime_context(
                &RuntimeOptions {
                    project_root_override: cli.project_root.clone(),
                    profile_override: cli.profile.clone(),
                    url_override: cli.url.clone(),
                },
                skill_root,
            )?;
            let plan = build_release_plan(&ctx, args)?;
            if !plan.dry_run {
                apply_release(&plan, &args.pending_file)?;
            }
            if cli.json {
                print_json(&plan)
            } else {
                println!("{}", serde_json::to_string_pretty(&plan)?);
                Ok(())
            }
        }
    }
}

async fn docs_command(cli: &Cli, command: &DocsCommand) -> Result<()> {
    match &command.command {
        DocsSubcommand::Search(args) => {
            let results = docs::search(&args.query, args.limit).await?;
            if cli.json {
                print_json(&json!({ "results": results }))
            } else if results.is_empty() {
                println!("No matches found.");
                Ok(())
            } else {
                for (index, result) in results.iter().enumerate() {
                    println!("{}. {}", index + 1, result.title);
                    println!("   {}", result.url);
                    println!("   Snippet: {}", result.snippet);
                }
                Ok(())
            }
        }
    }
}

async fn db_client(cli: &Cli, skill_root: &Path) -> Result<DbClient> {
    let ctx = runtime_context(
        &RuntimeOptions {
            project_root_override: cli.project_root.clone(),
            profile_override: cli.profile.clone(),
            url_override: cli.url.clone(),
        },
        skill_root,
    )?;
    Ok(DbClient::new(ctx))
}

fn render(json_mode: bool, payload: Value, sections: &[(&str, QueryTable)]) -> Result<()> {
    if json_mode {
        print_json(&payload)
    } else {
        for (index, (title, table)) in sections.iter().enumerate() {
            if index > 0 {
                println!();
            }
            println!("{}", render_table(table, Some(title)));
        }
        Ok(())
    }
}

fn read_sql_input(args: &SqlInputArgs) -> Result<String> {
    match (&args.command, &args.file) {
        (Some(_), Some(_)) => bail!("Use either -c/--command or -f/--file, not both."),
        (Some(command), None) => Ok(command.clone()),
        (None, Some(file)) => fs::read_to_string(file)
            .with_context(|| format!("Failed to read SQL file {}", file.display())),
        (None, None) => {
            if io::stdin().is_terminal() {
                bail!("No SQL provided. Pass -c, -f, or pipe SQL through stdin.");
            }
            let mut sql = String::new();
            io::stdin().read_to_string(&mut sql)?;
            Ok(sql)
        }
    }
}

async fn schema_inspect(cli: &Cli, db: &DbClient) -> Result<()> {
    let sections = vec![
        ("Tables", db.query("select table_schema, table_name, table_type from information_schema.tables where table_schema not in ('pg_catalog', 'information_schema') order by table_schema, table_name;").await?),
        ("Columns", db.query("select table_schema, table_name, ordinal_position, column_name, data_type, udt_name, is_nullable, column_default from information_schema.columns where table_schema not in ('pg_catalog', 'information_schema') order by table_schema, table_name, ordinal_position;").await?),
        ("Primary Keys", db.query("select tc.table_schema, tc.table_name, kcu.column_name, kcu.ordinal_position from information_schema.table_constraints tc join information_schema.key_column_usage kcu on tc.constraint_name = kcu.constraint_name and tc.table_schema = kcu.table_schema where tc.constraint_type = 'PRIMARY KEY' and tc.table_schema not in ('pg_catalog', 'information_schema') order by tc.table_schema, tc.table_name, kcu.ordinal_position;").await?),
        ("Foreign Keys", db.query("select tc.table_schema, tc.table_name, kcu.column_name, ccu.table_schema as foreign_table_schema, ccu.table_name as foreign_table_name, ccu.column_name as foreign_column_name, rc.update_rule, rc.delete_rule from information_schema.table_constraints tc join information_schema.key_column_usage kcu on tc.constraint_name = kcu.constraint_name and tc.table_schema = kcu.table_schema join information_schema.constraint_column_usage ccu on ccu.constraint_name = tc.constraint_name and ccu.table_schema = tc.table_schema join information_schema.referential_constraints rc on rc.constraint_name = tc.constraint_name and rc.constraint_schema = tc.table_schema where tc.constraint_type = 'FOREIGN KEY' and tc.table_schema not in ('pg_catalog', 'information_schema') order by tc.table_schema, tc.table_name, kcu.column_name;").await?),
        ("Indexes", db.query("select schemaname, tablename, indexname, indexdef from pg_indexes where schemaname not in ('pg_catalog', 'information_schema') order by schemaname, tablename, indexname;").await?),
        ("Views", db.query("select schemaname, viewname, left(definition, 400) as definition from pg_views where schemaname not in ('pg_catalog', 'information_schema') order by schemaname, viewname;").await?),
        ("Functions", db.query("select n.nspname as function_schema, p.proname as function_name, pg_get_function_identity_arguments(p.oid) as arguments, pg_get_function_result(p.oid) as return_type, l.lanname as language, left(pg_get_functiondef(p.oid), 400) as definition from pg_proc p join pg_namespace n on n.oid = p.pronamespace join pg_language l on l.oid = p.prolang where n.nspname not in ('pg_catalog', 'information_schema') and p.prokind = 'f' order by n.nspname, p.proname;").await?),
        ("Extensions", db.query("select extname, extversion, extrelocatable from pg_extension order by extname;").await?),
    ];
    if cli.json {
        let payload = sections
            .iter()
            .map(|(title, table)| ((*title).to_string(), table_to_json(table)))
            .collect::<serde_json::Map<_, _>>();
        print_json(&Value::Object(payload))
    } else {
        for (index, (title, table)) in sections.iter().enumerate() {
            if index > 0 {
                println!();
            }
            println!("{}", render_table(table, Some(title)));
        }
        Ok(())
    }
}

async fn schema_diff(cli: &Cli, skill_root: &Path, args: &SchemaDiffArgs) -> Result<()> {
    let ctx_a = runtime_context(
        &RuntimeOptions {
            project_root_override: cli.project_root.clone(),
            profile_override: args.profile_a.clone().or_else(|| cli.profile.clone()),
            url_override: args.url_a.clone(),
        },
        skill_root,
    )?;
    let ctx_b = runtime_context(
        &RuntimeOptions {
            project_root_override: cli.project_root.clone(),
            profile_override: args.profile_b.clone(),
            url_override: args.url_b.clone(),
        },
        skill_root,
    )?;
    let dump_a = dump_schema_to_string(skill_root, &ctx_a).await?;
    let dump_b = dump_schema_to_string(skill_root, &ctx_b).await?;
    let diff = similar::TextDiff::from_lines(&dump_a, &dump_b)
        .unified_diff()
        .header(&ctx_a.profile_name, &ctx_b.profile_name)
        .to_string();
    if cli.json {
        print_json(&json!({ "diff": diff }))
    } else if diff.trim().is_empty() {
        println!("No structural differences.");
        Ok(())
    } else {
        println!("{diff}");
        Ok(())
    }
}

async fn dump_schema(
    cli: &Cli,
    skill_root: &Path,
    args: &DumpOutputArgs,
    schema_only: bool,
) -> Result<()> {
    let ctx = runtime_context(
        &RuntimeOptions {
            project_root_override: cli.project_root.clone(),
            profile_override: cli.profile.clone(),
            url_override: cli.url.clone(),
        },
        skill_root,
    )?;
    let output = if let Some(output) = args.output.clone() {
        output
    } else {
        let profile = ctx.profile_name.clone();
        let timestamp = timestamp_stub();
        if schema_only {
            PathBuf::from(format!("schema_{profile}_{timestamp}.dump"))
        } else {
            PathBuf::from(format!("data_{profile}_{timestamp}.dump"))
        }
    };
    let backend = ensure_backend(&ctx, skill_root).await?;
    run_dump(&ctx, &backend, &output, schema_only)?;
    if cli.json {
        print_json(&json!({ "output": output, "schema_only": schema_only }))
    } else {
        println!("Wrote {}", output.display());
        Ok(())
    }
}

async fn dump_restore(cli: &Cli, skill_root: &Path, args: &RestoreArgs) -> Result<()> {
    if !args.input.exists() {
        bail!("File not found: {}", args.input.display());
    }
    let ctx = runtime_context(
        &RuntimeOptions {
            project_root_override: cli.project_root.clone(),
            profile_override: cli.profile.clone(),
            url_override: cli.url.clone(),
        },
        skill_root,
    )?;
    if args.input.extension().and_then(|ext| ext.to_str()) == Some("sql") {
        let db = DbClient::new(ctx);
        let sql = fs::read_to_string(&args.input)?;
        db.execute(&sql).await?;
    } else {
        let backend = ensure_backend(&ctx, skill_root).await?;
        run_restore(&ctx, &backend, &args.input)?;
    }
    if cli.json {
        print_json(&json!({ "status": "ok", "input": args.input }))
    } else {
        println!("Restore complete.");
        Ok(())
    }
}

async fn dump_schema_to_string(
    skill_root: &Path,
    ctx: &postgres_skill_cli::config::RuntimeContext,
) -> Result<String> {
    let backend = ensure_backend(ctx, skill_root).await?;
    let builder = pg_dump_builder(ctx, &backend)
        .schema_only()
        .no_owner()
        .no_privileges()
        .no_comments()
        .dbname(&ctx.url);
    let mut command = builder.build();
    let (stdout, _stderr) = command.execute()?;
    Ok(stdout)
}

fn run_dump(
    ctx: &postgres_skill_cli::config::RuntimeContext,
    backend: &ToolBackend,
    output: &Path,
    schema_only: bool,
) -> Result<()> {
    if output.extension().and_then(|ext| ext.to_str()) == Some("sql") {
        let mut builder = pg_dump_builder(ctx, backend).dbname(&ctx.url);
        if schema_only {
            builder = builder
                .schema_only()
                .no_owner()
                .no_privileges()
                .no_comments();
        } else {
            builder = builder.data_only().no_owner().no_privileges();
        }
        let mut command = builder.build();
        let (stdout, _stderr) = command.execute()?;
        fs::write(output, stdout)?;
    } else {
        let mut builder = pg_dump_builder(ctx, backend).dbname(&ctx.url).file(output);
        builder = builder.format("custom").no_owner().no_privileges();
        if schema_only {
            builder = builder.schema_only().no_comments();
        } else {
            builder = builder.data_only();
        }
        let mut command = builder.build();
        let _ = command.execute()?;
    }
    Ok(())
}

fn run_restore(
    ctx: &postgres_skill_cli::config::RuntimeContext,
    backend: &ToolBackend,
    input: &Path,
) -> Result<()> {
    let builder = PgRestoreBuilder::new()
        .program_dir(backend.binary_dir())
        .dbname(&ctx.url)
        .file(input)
        .no_owner()
        .no_privileges();
    let mut command = builder.build();
    let _ = command.execute()?;
    Ok(())
}

fn pg_dump_builder(
    ctx: &postgres_skill_cli::config::RuntimeContext,
    backend: &ToolBackend,
) -> PgDumpBuilder {
    PgDumpBuilder::new()
        .program_dir(backend.binary_dir())
        .dbname(&ctx.url)
}

async fn destructive_activity(
    cli: &Cli,
    db: &DbClient,
    function_name: &str,
    args: &ActivityActionArgs,
) -> Result<()> {
    let mut predicates = vec![
        "state <> 'idle'".to_string(),
        "pid <> pg_backend_pid()".to_string(),
    ];
    if let Some(query) = &args.query {
        predicates.push(format!("query ilike '%{}%'", escape_literal(query)));
    }
    if let Some(user) = &args.user {
        predicates.push(format!("usename = '{}'", escape_literal(user)));
    }
    if !args.pid.is_empty() {
        predicates.push(format!(
            "pid = any(array[{}])",
            args.pid
                .iter()
                .map(i32::to_string)
                .collect::<Vec<_>>()
                .join(",")
        ));
    }
    let candidates = db.query(&format!("select pid, usename as user_name, datname as db, state, now() - query_start as query_age, left(query, 200) as query from pg_stat_activity where {} order by query_start desc nulls last limit {};", predicates.join(" and "), args.limit)).await?;
    expect_non_empty(&candidates, "No matching active queries.")?;
    let pids = candidates
        .rows
        .iter()
        .filter_map(|row| {
            row.first()
                .and_then(|value| value.clone())
                .and_then(|value| value.parse::<i32>().ok())
        })
        .collect::<Vec<_>>();
    destructive_pids(cli, db, function_name, &pids, args.yes).await
}

async fn destructive_pids(
    cli: &Cli,
    db: &DbClient,
    function_name: &str,
    pids: &[i32],
    yes: bool,
) -> Result<()> {
    if pids.is_empty() {
        bail!("At least one PID is required.");
    }
    if !yes && env::var("DB_CONFIRM").ok().as_deref() != Some("YES") {
        if !io::stdin().is_terminal() {
            bail!("Confirmation required. Re-run with --yes or DB_CONFIRM=YES.");
        }
        eprint!(
            "Type YES to run {} on PID(s) {}: ",
            function_name,
            pids.iter()
                .map(i32::to_string)
                .collect::<Vec<_>>()
                .join(", ")
        );
        io::stderr().flush()?;
        let mut input = String::new();
        io::stdin().read_line(&mut input)?;
        if input.trim() != "YES" {
            bail!("Aborted.");
        }
    }
    let sql = format!(
        "select pid, {function_name}(pid) as result from unnest(array[{}]) as pid;",
        pids.iter()
            .map(i32::to_string)
            .collect::<Vec<_>>()
            .join(",")
    );
    let table = db.query(&sql).await?;
    render(
        cli.json,
        json!({"result": table_to_json(&table)}),
        &[("Result", table)],
    )
}

fn timestamp_stub() -> String {
    use chrono::{Datelike, Timelike, Utc};
    let now = Utc::now();
    format!(
        "{:04}{:02}{:02}_{:02}{:02}{:02}",
        now.year(),
        now.month(),
        now.day(),
        now.hour(),
        now.minute(),
        now.second()
    )
}
