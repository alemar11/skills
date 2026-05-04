use clap::{ArgAction, Args, Parser, Subcommand};
use std::path::PathBuf;

#[derive(Debug, Parser)]
#[command(name = "postgres", version, about = "Rust-first Postgres skill CLI")]
pub struct Cli {
    #[arg(
        long,
        global = true,
        action = ArgAction::SetTrue,
        help = "Print machine-readable JSON output"
    )]
    pub json: bool,

    #[arg(long, global = true, help = "Use a saved profile from config.toml")]
    pub profile: Option<String>,

    #[arg(long, global = true, help = "Resolve config from this project root")]
    pub project_root: Option<PathBuf>,

    #[arg(long, global = true, help = "Use a one-off PostgreSQL connection URL")]
    pub url: Option<String>,

    #[command(subcommand)]
    pub command: Command,
}

#[derive(Debug, Subcommand)]
pub enum Command {
    #[command(about = "Report config resolution and runtime readiness")]
    Doctor,
    #[command(about = "Manage and inspect connection profiles")]
    Profile(ProfileCommand),
    #[command(about = "Run SQL, explain queries, and search database objects")]
    Query(QueryCommand),
    #[command(about = "Inspect runtime activity and control matching sessions")]
    Activity(ActivityCommand),
    #[command(about = "Inspect schema, indexes, roles, and vacuum state")]
    Schema(SchemaCommand),
    #[command(about = "Run SQL-backed MCP Toolbox-style Postgres commands")]
    Toolbox(ToolboxCommand),
    #[command(about = "Release pending migration files into released migrations")]
    Migration(MigrationCommand),
    #[command(about = "Search official PostgreSQL documentation")]
    Docs(DocsCommand),
}

#[derive(Debug, Args)]
pub struct ProfileCommand {
    #[command(subcommand)]
    pub command: ProfileSubcommand,
}

#[derive(Debug, Subcommand)]
pub enum ProfileSubcommand {
    #[command(about = "Show the active connection URL, profile, and source")]
    Resolve,
    #[command(about = "Prompt for a profile and optionally save it")]
    Bootstrap(BootstrapArgs),
    #[command(about = "Verify that the active profile can connect")]
    Test,
    #[command(about = "Print connection details and key server settings")]
    Info,
    #[command(about = "Show the PostgreSQL server version")]
    Version,
    #[command(about = "Migrate legacy postgres.toml to config.toml")]
    MigrateToml,
    #[command(about = "Persist sslmode for a saved profile")]
    SetSsl(SetSslArgs),
}

#[derive(Debug, Args)]
pub struct BootstrapArgs {
    #[arg(long, help = "Write the prompted profile to config.toml")]
    pub save: bool,
}

#[derive(Debug, Args)]
pub struct SetSslArgs {
    #[arg(help = "Profile name to update")]
    pub profile: String,
    #[arg(help = "SSL mode value: true/require or false/disable")]
    pub sslmode: String,
}

#[derive(Debug, Args)]
pub struct QueryCommand {
    #[command(subcommand)]
    pub command: QuerySubcommand,
}

#[derive(Debug, Subcommand)]
pub enum QuerySubcommand {
    #[command(about = "Execute SQL from -c, -f, or stdin")]
    Run(SqlInputArgs),
    #[command(about = "Run EXPLAIN for SQL, defaulting to ANALYZE")]
    Explain(ExplainArgs),
    #[command(about = "Search schemas, tables, columns, views, and routines by name")]
    Find(FindArgs),
}

#[derive(Debug, Args, Clone)]
pub struct SqlInputArgs {
    #[arg(short = 'c', long, help = "SQL text to execute")]
    pub command: Option<String>,

    #[arg(short = 'f', long, help = "Path to a SQL file to execute")]
    pub file: Option<PathBuf>,
}

#[derive(Debug, Args)]
pub struct ExplainArgs {
    #[command(flatten)]
    pub sql: SqlInputArgs,

    #[arg(long, action = ArgAction::SetTrue, help = "Run EXPLAIN without ANALYZE")]
    pub no_analyze: bool,
}

#[derive(Debug, Args)]
pub struct FindArgs {
    #[arg(help = "Case-insensitive object-name search pattern")]
    pub pattern: String,

    #[arg(long, help = "Comma-separated object types to search")]
    pub types: Option<String>,
}

#[derive(Debug, Args)]
pub struct ActivityCommand {
    #[command(subcommand)]
    pub command: ActivitySubcommand,
}

#[derive(Debug, Subcommand)]
pub enum ActivitySubcommand {
    #[command(about = "List non-idle sessions in pg_stat_activity")]
    Overview(LimitArgs),
    #[command(about = "Show blocked and blocking sessions")]
    Locks,
    #[command(about = "List top pg_stat_statements entries by total time")]
    Slow(LimitArgs),
    #[command(about = "List active queries older than a minute threshold")]
    LongRunning(LongRunningArgs),
    #[command(about = "Cancel matching active queries after confirmation")]
    Cancel(ActivityActionArgs),
    #[command(about = "Terminate matching active sessions after confirmation")]
    Terminate(ActivityActionArgs),
    #[command(about = "Cancel specific backend PIDs after confirmation")]
    CancelPid(PidArgs),
    #[command(about = "Terminate specific backend PIDs after confirmation")]
    TerminatePid(PidArgs),
    #[command(about = "Alias for top pg_stat_statements entries")]
    PgStatTop(LimitArgs),
}

#[derive(Debug, Args)]
pub struct LimitArgs {
    #[arg(default_value_t = 20, help = "Maximum rows to return")]
    pub limit: u32,
}

#[derive(Debug, Args)]
pub struct LongRunningArgs {
    #[arg(default_value_t = 5, help = "Minimum active-query age in minutes")]
    pub minutes: u32,

    #[arg(default_value_t = 20, help = "Maximum rows to return")]
    pub limit: u32,
}

#[derive(Debug, Args)]
pub struct ActivityActionArgs {
    #[arg(long, help = "Match active queries containing this text")]
    pub query: Option<String>,

    #[arg(long, help = "Match sessions owned by this database user")]
    pub user: Option<String>,

    #[arg(long, help = "Backend PID to target; repeat for multiple PIDs")]
    pub pid: Vec<i32>,

    #[arg(long, default_value_t = 20, help = "Maximum candidate rows to inspect")]
    pub limit: u32,

    #[arg(long, action = ArgAction::SetTrue, help = "Skip interactive confirmation")]
    pub yes: bool,
}

#[derive(Debug, Args)]
pub struct PidArgs {
    #[arg(long, value_delimiter = ',', help = "Comma-separated backend PID list")]
    pub pid: Vec<i32>,

    #[arg(long, action = ArgAction::SetTrue, help = "Skip interactive confirmation")]
    pub yes: bool,
}

#[derive(Debug, Args)]
pub struct SchemaCommand {
    #[command(subcommand)]
    pub command: SchemaSubcommand,
}

#[derive(Debug, Subcommand)]
pub enum SchemaSubcommand {
    #[command(
        about = "Inspect tables, columns, constraints, indexes, views, routines, and extensions"
    )]
    Inspect,
    #[command(about = "List largest user tables by total relation size")]
    TableSizes(LimitArgs),
    #[command(about = "Show missing-index candidates and unused indexes")]
    IndexHealth(LimitArgs),
    #[command(about = "Find foreign keys without a supporting leading index")]
    MissingFkIndexes,
    #[command(about = "Show vacuum and analyze status for user tables")]
    VacuumStatus,
    #[command(about = "List roles and key role attributes")]
    Roles,
}

#[derive(Debug, Args)]
pub struct ToolboxCommand {
    #[command(subcommand)]
    pub command: ToolboxSubcommand,
}

#[derive(Debug, Subcommand)]
pub enum ToolboxSubcommand {
    #[command(alias = "execute_sql", about = "Execute SQL from -c, -f, or stdin")]
    ExecuteSql(SqlInputArgs),
    #[command(
        alias = "get_query_plan",
        about = "Return a JSON query plan without executing by default"
    )]
    GetQueryPlan(ToolboxQueryPlanArgs),
    #[command(
        alias = "database_overview",
        about = "Summarize database identity, object counts, activity, and key settings"
    )]
    DatabaseOverview,
    #[command(
        alias = "list_active_queries",
        about = "List active sessions in pg_stat_activity"
    )]
    ListActiveQueries(LimitArgs),
    #[command(
        alias = "list_tables",
        about = "List user-visible base, partitioned, and foreign tables"
    )]
    ListTables,
    #[command(alias = "list_views", about = "List user-visible views")]
    ListViews,
    #[command(alias = "list_schemas", about = "List user-visible schemas")]
    ListSchemas,
    #[command(alias = "list_triggers", about = "List user-defined triggers")]
    ListTriggers,
    #[command(alias = "list_indexes", about = "List user-visible indexes")]
    ListIndexes,
    #[command(alias = "list_sequences", about = "List user-visible sequences")]
    ListSequences,
    #[command(
        alias = "list_available_extensions",
        about = "List extensions available to install"
    )]
    ListAvailableExtensions,
    #[command(
        alias = "list_installed_extensions",
        about = "List installed extensions"
    )]
    ListInstalledExtensions,
    #[command(
        alias = "list_autovacuum_configurations",
        about = "List autovacuum settings and table overrides"
    )]
    ListAutovacuumConfigurations,
    #[command(
        alias = "list_memory_configurations",
        about = "List memory-related PostgreSQL settings"
    )]
    ListMemoryConfigurations,
    #[command(
        alias = "list_top_bloated_tables",
        about = "Estimate top user tables by dead tuples"
    )]
    ListTopBloatedTables(LimitArgs),
    #[command(alias = "list_replication_slots", about = "List replication slots")]
    ListReplicationSlots,
    #[command(
        alias = "list_invalid_indexes",
        about = "List indexes that are invalid, not ready, or not live"
    )]
    ListInvalidIndexes,
}

#[derive(Debug, Args)]
pub struct ToolboxQueryPlanArgs {
    #[command(flatten)]
    pub sql: SqlInputArgs,

    #[arg(long, action = ArgAction::SetTrue, help = "Run EXPLAIN ANALYZE")]
    pub analyze: bool,
}

#[derive(Debug, Args)]
pub struct MigrationCommand {
    #[command(subcommand)]
    pub command: MigrationSubcommand,
}

#[derive(Debug, Subcommand)]
pub enum MigrationSubcommand {
    #[command(about = "Move a pending migration file into released/ and update CHANGELOG.md")]
    Release(MigrationReleaseArgs),
}

#[derive(Debug, Args, Clone)]
pub struct MigrationReleaseArgs {
    #[arg(long, help = "Human summary for the released migration")]
    pub summary: Option<String>,

    #[arg(
        long,
        default_value = "prerelease.sql",
        help = "Pending migration filename"
    )]
    pub pending_file: String,

    #[arg(long, help = "Override migrations directory")]
    pub migrations_path: Option<PathBuf>,

    #[arg(long, help = "Override generated release filename slug")]
    pub slug: Option<String>,

    #[arg(long, help = "Override generated timestamp")]
    pub timestamp: Option<String>,

    #[arg(long, action = ArgAction::SetTrue, help = "Print the release plan without writing files")]
    pub dry_run: bool,
}

#[derive(Debug, Args)]
pub struct DocsCommand {
    #[command(subcommand)]
    pub command: DocsSubcommand,
}

#[derive(Debug, Subcommand)]
pub enum DocsSubcommand {
    #[command(about = "Search official PostgreSQL current documentation")]
    Search(DocsSearchArgs),
}

#[derive(Debug, Args)]
pub struct DocsSearchArgs {
    #[arg(help = "Documentation search query")]
    pub query: String,

    #[arg(default_value_t = 10, help = "Maximum results to return")]
    pub limit: usize,
}
