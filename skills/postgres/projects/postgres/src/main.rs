use anyhow::{Context, Result, anyhow, bail};
use clap::Parser;
use postgres_skill_cli::cli::*;
use postgres_skill_cli::config::{
    AccessMode, RuntimeOptions, application_name, bootstrap_profile, canonical_config_path,
    migrate_config_file, parse_legacy_ssl_mode, parse_ssl_mode, redact_connection_url,
    runtime_context, update_ssl_mode,
};
use postgres_skill_cli::db::{
    DbClient, QueryExecution, QueryTable, escape_literal, execution_to_json, expect_non_empty,
    table_to_json,
};
use postgres_skill_cli::docs;
use postgres_skill_cli::migration::{apply_release, build_release_plan};
use postgres_skill_cli::output::{print_json, render_table};
use postgres_skill_cli::tools::{self, ToolSection};
use serde_json::{Value, json};
use sqlparser::dialect::{Dialect, PostgreSqlDialect};
use sqlparser::tokenizer::{Token, Tokenizer};
use std::env;
use std::fs;
use std::io::{self, IsTerminal, Read, Write};
use std::path::{Path, PathBuf};

#[tokio::main]
async fn main() {
    let cli = Cli::parse_from(std::iter::once("postgres".to_string()).chain(env::args().skip(1)));
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
    let skill_root = resolve_skill_root()?;

    match &cli.command {
        Command::Doctor => doctor(&cli, &skill_root).await,
        Command::Profile(command) => profile(&cli, command, &skill_root).await,
        Command::Query(command) => query(&cli, command, &skill_root).await,
        Command::Activity(command) => activity(&cli, command, &skill_root).await,
        Command::Schema(command) => schema(&cli, command, &skill_root).await,
        Command::Migration(command) => migration(&cli, command, &skill_root).await,
        Command::Docs(command) => docs_command(&cli, command).await,
    }
}

fn resolve_skill_root() -> Result<PathBuf> {
    let executable = env::current_exe().context("Failed to resolve postgres executable path")?;
    resolve_skill_root_from(&executable)
}

fn resolve_skill_root_from(executable: &Path) -> Result<PathBuf> {
    executable
        .ancestors()
        .skip(1)
        .find(|path| path.join("SKILL.md").is_file() && path.join("scripts/postgres").is_file())
        .map(Path::to_path_buf)
        .ok_or_else(|| {
            anyhow!(
                "Failed to resolve postgres skill root from executable path {}.",
                executable.display()
            )
        })
}

fn sanitize_error_message(message: &str) -> String {
    let postgres_url =
        regex::Regex::new(r"(?i)(postgres(?:ql)?://[^:/\s?#]+:)([^@/\s?#]+)@").unwrap();
    let key_value_password =
        regex::Regex::new(r"(?i)\b(password|pgpassword)\s*=\s*([^ \n\r\t;?&#]+)").unwrap();
    let query_password =
        regex::Regex::new(r"(?i)([?&](?:password|sslpassword)=)([^&#\s]+)").unwrap();

    let masked_url = postgres_url.replace_all(message, "$1***@");
    let masked_query = query_password.replace_all(&masked_url, "$1***");
    let masked_password = key_value_password.replace_all(&masked_query, "$1=***");
    masked_password.into_owned()
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum AccessRequirement {
    Read,
    Write,
    ReadWrite,
}

impl AccessRequirement {
    fn as_str(&self) -> &'static str {
        match self {
            AccessRequirement::Read => "read",
            AccessRequirement::Write => "write",
            AccessRequirement::ReadWrite => "read-write",
        }
    }
}

fn require_db_access(db: &DbClient, requirement: AccessRequirement, operation: &str) -> Result<()> {
    ensure_access(
        &db.context().profile_name,
        db.context().access_mode,
        requirement,
        operation,
    )
}

fn ensure_access(
    profile_name: &str,
    access_mode: AccessMode,
    requirement: AccessRequirement,
    operation: &str,
) -> Result<()> {
    let allowed = match (access_mode, requirement) {
        (AccessMode::ReadWrite, _) => true,
        (AccessMode::Read, AccessRequirement::Read) => true,
        (AccessMode::Write, AccessRequirement::Write) => true,
        _ => false,
    };
    if allowed {
        return Ok(());
    }

    if requirement == AccessRequirement::ReadWrite {
        bail!(
            "{operation} requires access_mode = \"read-write\" because the SQL access intent is ambiguous or mixes reads and writes; profile '{profile_name}' has access_mode = \"{}\". Use a read-write profile or rely on PostgreSQL roles/grants for authoritative enforcement.",
            access_mode.as_str()
        );
    }

    bail!(
        "{operation} requires {} access; profile '{profile_name}' has access_mode = \"{}\". Use a profile with access_mode = \"{}\" or \"read-write\", and keep PostgreSQL roles/grants as the authoritative enforcement boundary.",
        requirement.as_str(),
        access_mode.as_str(),
        requirement.as_str()
    )
}

// Tokenization only: forward PostgreSQL lexical rules but leave U& literals
// opaque. Decoding their surrogate pairs/custom UESCAPE is the server's job.
#[derive(Debug)]
struct AccessDialect;

impl Dialect for AccessDialect {
    fn dialect(&self) -> std::any::TypeId {
        std::any::TypeId::of::<PostgreSqlDialect>()
    }

    fn is_delimited_identifier_start(&self, ch: char) -> bool {
        PostgreSqlDialect {}.is_delimited_identifier_start(ch)
    }

    fn is_identifier_start(&self, ch: char) -> bool {
        PostgreSqlDialect {}.is_identifier_start(ch)
    }

    fn is_identifier_part(&self, ch: char) -> bool {
        PostgreSqlDialect {}.is_identifier_part(ch)
    }

    fn is_custom_operator_part(&self, ch: char) -> bool {
        PostgreSqlDialect {}.is_custom_operator_part(ch)
    }

    fn supports_nested_comments(&self) -> bool {
        PostgreSqlDialect {}.supports_nested_comments()
    }

    fn supports_string_escape_constant(&self) -> bool {
        PostgreSqlDialect {}.supports_string_escape_constant()
    }

    fn supports_numeric_literal_underscores(&self) -> bool {
        PostgreSqlDialect {}.supports_numeric_literal_underscores()
    }

    fn supports_geometric_types(&self) -> bool {
        PostgreSqlDialect {}.supports_geometric_types()
    }

    fn supports_unicode_string_literal(&self) -> bool {
        false
    }
}

fn classify_sql_access(sql: &str) -> AccessRequirement {
    let Ok(mut tokens) = Tokenizer::new(&AccessDialect, sql)
        .with_unescape(false)
        .tokenize()
    else {
        return AccessRequirement::ReadWrite;
    };
    tokens.retain(|token| !matches!(token, Token::Whitespace(_)));
    let mut requirement = None;
    for statement in tokens.split(|token| *token == Token::SemiColon) {
        if statement.is_empty() {
            continue;
        }
        let statement_requirement = classify_sql_statement_access(statement);
        requirement = Some(match requirement {
            None => statement_requirement,
            Some(existing) if existing == statement_requirement => existing,
            Some(_) => AccessRequirement::ReadWrite,
        });
        if requirement == Some(AccessRequirement::ReadWrite) {
            return AccessRequirement::ReadWrite;
        }
    }
    requirement.unwrap_or(AccessRequirement::ReadWrite)
}

fn classify_sql_statement_access(statement: &[Token]) -> AccessRequirement {
    let Some(Token::Word(word)) = statement.first() else {
        return AccessRequirement::ReadWrite;
    };
    if word.quote_style.is_some() {
        return AccessRequirement::ReadWrite;
    }
    match word.value.to_ascii_lowercase().as_str() {
        "select" | "show" | "values" | "table" => AccessRequirement::Read,
        "explain" => classify_explain_access(&statement[1..]),
        "insert" | "update" | "delete" | "merge" | "create" | "alter" | "drop" | "truncate"
        | "grant" | "revoke" | "call" | "do" | "refresh" | "reindex" | "vacuum" | "analyze" => {
            AccessRequirement::Write
        }
        _ => AccessRequirement::ReadWrite,
    }
}

fn classify_explain_access(mut tokens: &[Token]) -> AccessRequirement {
    while let Some(token) = tokens.first() {
        if *token == Token::LParen {
            let Some(close_index) = tokens.iter().position(|token| *token == Token::RParen) else {
                return AccessRequirement::ReadWrite;
            };
            tokens = &tokens[close_index + 1..];
            continue;
        }
        let Token::Word(word) = token else {
            return AccessRequirement::ReadWrite;
        };
        if word.quote_style.is_some() {
            return AccessRequirement::ReadWrite;
        }
        match word.value.to_ascii_lowercase().as_str() {
            "analyze" | "analyse" | "verbose" | "costs" | "buffers" | "format" | "settings"
            | "wal" | "timing" | "summary" | "memory" | "serialize" | "generic_plan" | "true"
            | "false" | "text" | "json" | "yaml" | "xml" => {
                tokens = &tokens[1..];
            }
            _ => return classify_sql_statement_access(tokens),
        }
    }
    AccessRequirement::ReadWrite
}

#[cfg(test)]
mod tests {
    use super::{
        AccessRequirement, classify_sql_access, ensure_access, parse_query_text_max_chars,
        resolve_skill_root_from, sanitize_error_message,
    };
    use postgres_skill_cli::config::AccessMode;
    use std::fs;
    use tempfile::tempdir;

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

    #[test]
    fn masks_password_query_parameters_in_errors() {
        let message = "postgresql://postgres@localhost/app?password=secret&sslpassword=tls-secret";
        assert_eq!(
            sanitize_error_message(message),
            "postgresql://postgres@localhost/app?password=***&sslpassword=***"
        );
    }

    #[test]
    fn resolves_skill_root_from_the_shipped_executable_layout() {
        let temp = tempdir().unwrap();
        let skill_root = temp.path().join("postgres-skill");
        let executable = skill_root.join("scripts/bin/postgres-linux-x86_64");
        fs::create_dir_all(executable.parent().unwrap()).unwrap();
        fs::write(skill_root.join("SKILL.md"), "# Postgres").unwrap();
        fs::write(skill_root.join("scripts/postgres"), "#!/bin/sh").unwrap();
        fs::write(&executable, "binary").unwrap();

        assert_eq!(resolve_skill_root_from(&executable).unwrap(), skill_root);
    }

    #[test]
    fn query_text_max_chars_defaults_and_validates() {
        assert_eq!(parse_query_text_max_chars(None).unwrap(), 300);
        assert_eq!(parse_query_text_max_chars(Some("512")).unwrap(), 512);
        assert!(parse_query_text_max_chars(Some("bad")).is_err());
    }

    #[test]
    fn sql_access_classifier_detects_obvious_read_write_and_ambiguous_sql() {
        assert_eq!(classify_sql_access("select 1"), AccessRequirement::Read);
        assert_eq!(
            classify_sql_access("-- comment\nshow server_version"),
            AccessRequirement::Read
        );
        assert_eq!(
            classify_sql_access("insert into users(id) values (1)"),
            AccessRequirement::Write
        );
        assert_eq!(
            classify_sql_access("create table example(id int)"),
            AccessRequirement::Write
        );
        assert_eq!(
            classify_sql_access("explain (analyze, buffers) update users set active = true"),
            AccessRequirement::Write
        );
        assert_eq!(
            classify_sql_access("explain select * from users"),
            AccessRequirement::Read
        );
        assert_eq!(
            classify_sql_access("select 1; update users set active = true"),
            AccessRequirement::ReadWrite
        );
        assert_eq!(
            classify_sql_access("with x as (select 1) select * from x"),
            AccessRequirement::ReadWrite
        );
    }

    #[test]
    fn sql_access_classifier_ignores_semicolons_inside_strings_and_comments() {
        for sql in [
            "SELECT 'hello;world' AS message",
            "SELECT 'it''s; still a string'",
            r"SELECT E'it\'s; still a string'",
            r#"SELECT 1 AS "quoted;identifier""#,
            "SELECT $$hello;world$$",
            "SELECT $tag$hello;world$tag$",
            "SELECT $tag$hello;$other$world$tag$",
            "SELECT 'hello;世界'",
            r"SELECT U&'\D83D\DE00;hello'",
            r"SELECT U&'\path;hello' UESCAPE '!'",
            "-- ignored; DELETE FROM users\nSELECT 1",
            "/* outer; /* nested; */ still a comment; */ SELECT 1",
            "SELECT 1 /* ignored; DELETE FROM users */; SELECT 2",
            "SELECT 1; -- ignored; DELETE FROM users",
            "EXPLAIN /* ignored; */ (FORMAT JSON) SELECT ';'",
        ] {
            assert_eq!(classify_sql_access(sql), AccessRequirement::Read, "{sql}");
            let mixed = format!("{sql}\n; DELETE FROM users");
            assert_eq!(
                classify_sql_access(&mixed),
                AccessRequirement::ReadWrite,
                "{mixed}"
            );
        }
    }

    #[test]
    fn sql_access_classifier_treats_unterminated_tokens_as_ambiguous() {
        for sql in [
            "SELECT 'hello;world",
            "SELECT $$hello;world",
            "SELECT 1 /* open",
        ] {
            assert_eq!(
                classify_sql_access(sql),
                AccessRequirement::ReadWrite,
                "{sql}"
            );
        }
    }

    #[test]
    fn access_guard_allows_only_matching_access_modes() {
        assert!(ensure_access("local", AccessMode::Read, AccessRequirement::Read, "query").is_ok());
        assert!(
            ensure_access("local", AccessMode::Read, AccessRequirement::Write, "query").is_err()
        );
        assert!(
            ensure_access(
                "local",
                AccessMode::Write,
                AccessRequirement::Write,
                "query"
            )
            .is_ok()
        );
        assert!(
            ensure_access("local", AccessMode::Write, AccessRequirement::Read, "query").is_err()
        );
        assert!(
            ensure_access(
                "local",
                AccessMode::ReadWrite,
                AccessRequirement::ReadWrite,
                "query"
            )
            .is_ok()
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

    let output = json!({
        "application_name": application_name(),
        "runtime": runtime_info,
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
                "url": redact_connection_url(&resolved.url),
                "access_mode": resolved.access_mode,
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
        ProfileSubcommand::MigrateConfig => {
            let project_root = postgres_skill_cli::config::resolve_project_root(
                cli.project_root.clone(),
                skill_root,
            )?;
            let config_path = canonical_config_path(&project_root);
            let migration = migrate_config_file(&config_path)?;
            let output = json!({
                "config_path": config_path,
                "toml_path": config_path,
                "source_path": migration.source_path,
                "backup_path": migration.backup_path,
                "schema_version": migration.config.schema_version,
                "migration_outcome": migration.migration_outcome,
            });
            if cli.json {
                print_json(&output)
            } else {
                println!("{}", serde_json::to_string_pretty(&output)?);
                Ok(())
            }
        }
        ProfileSubcommand::SetSslMode(args) => {
            let project_root = postgres_skill_cli::config::resolve_project_root(
                cli.project_root.clone(),
                skill_root,
            )?;
            let config_path = canonical_config_path(&project_root);
            let ssl_mode = parse_ssl_mode(&args.ssl_mode)?;
            update_ssl_mode(&config_path, &args.profile, ssl_mode)?;
            let output = json!({
                "config_path": config_path,
                "toml_path": config_path,
                "profile": args.profile,
                "ssl_mode": ssl_mode,
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
            let ssl_mode = parse_legacy_ssl_mode(&args.sslmode)?;
            update_ssl_mode(&config_path, &args.profile, ssl_mode)?;
            let output = json!({
                "config_path": config_path,
                "toml_path": config_path,
                "profile": args.profile,
                "ssl_mode": ssl_mode,
                "compatibility_alias": "set-ssl",
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
                println!("DB_URL={:?}", redact_connection_url(&ctx.url));
                println!("DB_SSL_MODE={}", ctx.ssl_mode.as_str());
                println!("DB_ACCESS_MODE={}", ctx.access_mode.as_str());
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
            db.query("select 1;").await?;
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
            require_db_access(&db, AccessRequirement::Read, "profile info")?;
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
        ProfileSubcommand::Overview => {
            let db = db_client(cli, skill_root).await?;
            require_db_access(&db, AccessRequirement::Read, "profile overview")?;
            let sections = tools::database_overview(&db).await?;
            render_named_sections(cli.json, "overview", &sections)
        }
        ProfileSubcommand::Settings(args) => {
            let db = db_client(cli, skill_root).await?;
            require_db_access(&db, AccessRequirement::Read, "profile settings")?;
            match &args.command {
                ProfileSettingsSubcommand::Autovacuum => {
                    let sections = tools::list_autovacuum_configurations(&db).await?;
                    render_named_sections(cli.json, "autovacuum_settings", &sections)
                }
                ProfileSettingsSubcommand::Memory => {
                    let table = tools::list_memory_configurations(&db).await?;
                    render_named_table(cli.json, "memory_settings", "Memory Settings", table)
                }
            }
        }
        ProfileSubcommand::Version => {
            let db = db_client(cli, skill_root).await?;
            require_db_access(&db, AccessRequirement::Read, "profile version")?;
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
            require_db_access(&db, classify_sql_access(&sql), "query run")?;
            let execution = tools::execute_sql(&db, &sql).await?;
            render_query_run(cli.json, &sql, &execution)
        }
        QuerySubcommand::Explain(args) => {
            let sql = read_sql_input(&args.sql)?;
            require_db_access(&db, classify_sql_access(&sql), "query explain")?;
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
        QuerySubcommand::Plan(args) => {
            let sql = read_sql_input(&args.sql)?;
            require_db_access(&db, classify_sql_access(&sql), "query plan")?;
            let table = tools::get_query_plan(&db, &sql, args.analyze).await?;
            render_named_table(cli.json, "plan", "Query Plan", table)
        }
        QuerySubcommand::Find(args) => {
            require_db_access(&db, AccessRequirement::Read, "query find")?;
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
    let requirement = match &command.command {
        ActivitySubcommand::Cancel(_)
        | ActivitySubcommand::Terminate(_)
        | ActivitySubcommand::CancelPid(_)
        | ActivitySubcommand::TerminatePid(_) => AccessRequirement::Write,
        _ => AccessRequirement::Read,
    };
    require_db_access(&db, requirement, "activity command")?;
    match &command.command {
        ActivitySubcommand::Overview(args) => {
            let table = db.query(&format!("select pid, usename as user_name, datname as db, state, wait_event_type, wait_event, now() - query_start as query_age, now() - xact_start as xact_age, left(query, 200) as query from pg_stat_activity where pid <> pg_backend_pid() and state <> 'idle' order by query_start desc nulls last limit {};", args.limit)).await?;
            render(
                cli.json,
                json!({"activity": table_to_json(&table)}),
                &[("Activity", table)],
            )
        }
        ActivitySubcommand::ActiveQueries(args) => {
            let table = tools::list_active_queries(&db, args.limit).await?;
            render_named_table(cli.json, "active_queries", "Active Queries", table)
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
            let chars = query_text_max_chars()?;
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
        ActivitySubcommand::ReplicationSlots => {
            let table = tools::list_replication_slots(&db).await?;
            render_named_table(cli.json, "replication_slots", "Replication Slots", table)
        }
    }
}

async fn schema(cli: &Cli, command: &SchemaCommand, skill_root: &Path) -> Result<()> {
    let db = db_client(cli, skill_root).await?;
    require_db_access(&db, AccessRequirement::Read, "schema command")?;
    match &command.command {
        SchemaSubcommand::Inspect => schema_inspect(cli, &db).await,
        SchemaSubcommand::List(args) => match &args.command {
            SchemaListSubcommand::Tables => {
                let table = tools::list_tables(&db).await?;
                render_named_table(cli.json, "tables", "Tables", table)
            }
            SchemaListSubcommand::Views => {
                let table = tools::list_views(&db).await?;
                render_named_table(cli.json, "views", "Views", table)
            }
            SchemaListSubcommand::Schemas => {
                let table = tools::list_schemas(&db).await?;
                render_named_table(cli.json, "schemas", "Schemas", table)
            }
            SchemaListSubcommand::Triggers => {
                let table = tools::list_triggers(&db).await?;
                render_named_table(cli.json, "triggers", "Triggers", table)
            }
            SchemaListSubcommand::Indexes => {
                let table = tools::list_indexes(&db).await?;
                render_named_table(cli.json, "indexes", "Indexes", table)
            }
            SchemaListSubcommand::Sequences => {
                let table = tools::list_sequences(&db).await?;
                render_named_table(cli.json, "sequences", "Sequences", table)
            }
        },
        SchemaSubcommand::Extensions(args) => {
            if args.available {
                let table = tools::list_available_extensions(&db).await?;
                render_named_table(
                    cli.json,
                    "available_extensions",
                    "Available Extensions",
                    table,
                )
            } else {
                let table = tools::list_installed_extensions(&db).await?;
                render_named_table(
                    cli.json,
                    "installed_extensions",
                    "Installed Extensions",
                    table,
                )
            }
        }
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
        SchemaSubcommand::InvalidIndexes => {
            let table = tools::list_invalid_indexes(&db).await?;
            render_named_table(cli.json, "invalid_indexes", "Invalid Indexes", table)
        }
        SchemaSubcommand::TopBloatedTables(args) => {
            let table = tools::list_top_bloated_tables(&db, args.limit).await?;
            render_named_table(cli.json, "top_bloated_tables", "Top Bloated Tables", table)
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
            ensure_access(
                &ctx.profile_name,
                ctx.access_mode,
                AccessRequirement::Write,
                "migration release",
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

fn render_named_table(json_mode: bool, key: &str, title: &str, table: QueryTable) -> Result<()> {
    let mut payload = serde_json::Map::new();
    payload.insert(key.to_string(), table_to_json(&table));
    render(json_mode, Value::Object(payload), &[(title, table)])
}

fn render_named_sections(json_mode: bool, key: &str, sections: &[ToolSection]) -> Result<()> {
    if json_mode {
        let sections_payload = sections
            .iter()
            .map(|section| (section.key.to_string(), table_to_json(&section.table)))
            .collect::<serde_json::Map<_, _>>();
        let mut payload = serde_json::Map::new();
        payload.insert(key.to_string(), Value::Object(sections_payload));
        print_json(&Value::Object(payload))
    } else {
        for (index, section) in sections.iter().enumerate() {
            if index > 0 {
                println!();
            }
            println!("{}", render_table(&section.table, Some(section.title)));
        }
        Ok(())
    }
}

fn render_query_run(json_mode: bool, sql: &str, execution: &QueryExecution) -> Result<()> {
    if json_mode {
        print_json(&json!({
            "query": sql,
            "statements": execution_to_json(execution)["statements"].clone(),
        }))
    } else {
        for (index, statement) in execution.statements.iter().enumerate() {
            if index > 0 {
                println!();
            }
            if statement.columns.is_empty() {
                println!(
                    "Statement {}: {} row{} affected",
                    statement.statement,
                    statement.row_count,
                    if statement.row_count == 1 { "" } else { "s" }
                );
            } else {
                let title = format!(
                    "Statement {} ({} row{})",
                    statement.statement,
                    statement.row_count,
                    if statement.row_count == 1 { "" } else { "s" }
                );
                println!(
                    "{}",
                    render_table(
                        &QueryTable {
                            columns: statement.columns.clone(),
                            rows: statement.rows.clone(),
                        },
                        Some(&title),
                    )
                );
            }
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

fn query_text_max_chars() -> Result<u32> {
    parse_query_text_max_chars(env::var("DB_QUERY_TEXT_MAX_CHARS").ok().as_deref())
}

fn parse_query_text_max_chars(value: Option<&str>) -> Result<u32> {
    let Some(value) = value.map(str::trim).filter(|value| !value.is_empty()) else {
        return Ok(300);
    };

    value
        .parse::<u32>()
        .with_context(|| "DB_QUERY_TEXT_MAX_CHARS must be a non-negative integer.".to_string())
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
