use clap::{ArgAction, Args, Parser, Subcommand};
use std::path::PathBuf;

#[derive(Debug, Parser)]
#[command(name = "postgres", version, about = "Rust-first Postgres skill CLI")]
pub struct Cli {
    #[arg(long, global = true, action = ArgAction::SetTrue)]
    pub json: bool,

    #[arg(long, global = true)]
    pub profile: Option<String>,

    #[arg(long, global = true)]
    pub project_root: Option<PathBuf>,

    #[arg(long, global = true)]
    pub url: Option<String>,

    #[command(subcommand)]
    pub command: Command,
}

#[derive(Debug, Subcommand)]
pub enum Command {
    Doctor,
    Profile(ProfileCommand),
    Query(QueryCommand),
    Activity(ActivityCommand),
    Schema(SchemaCommand),
    Dump(DumpCommand),
    Migration(MigrationCommand),
    Docs(DocsCommand),
}

#[derive(Debug, Args)]
pub struct ProfileCommand {
    #[command(subcommand)]
    pub command: ProfileSubcommand,
}

#[derive(Debug, Subcommand)]
pub enum ProfileSubcommand {
    Resolve,
    Bootstrap(BootstrapArgs),
    Test,
    Info,
    Version,
    MigrateToml,
    SetSsl(SetSslArgs),
}

#[derive(Debug, Args)]
pub struct BootstrapArgs {
    #[arg(long)]
    pub save: bool,
}

#[derive(Debug, Args)]
pub struct SetSslArgs {
    pub profile: String,
    pub sslmode: String,
}

#[derive(Debug, Args)]
pub struct QueryCommand {
    #[command(subcommand)]
    pub command: QuerySubcommand,
}

#[derive(Debug, Subcommand)]
pub enum QuerySubcommand {
    Run(SqlInputArgs),
    Explain(ExplainArgs),
    Find(FindArgs),
}

#[derive(Debug, Args, Clone)]
pub struct SqlInputArgs {
    #[arg(short = 'c', long)]
    pub command: Option<String>,

    #[arg(short = 'f', long)]
    pub file: Option<PathBuf>,
}

#[derive(Debug, Args)]
pub struct ExplainArgs {
    #[command(flatten)]
    pub sql: SqlInputArgs,

    #[arg(long, action = ArgAction::SetTrue)]
    pub no_analyze: bool,
}

#[derive(Debug, Args)]
pub struct FindArgs {
    pub pattern: String,

    #[arg(long)]
    pub types: Option<String>,
}

#[derive(Debug, Args)]
pub struct ActivityCommand {
    #[command(subcommand)]
    pub command: ActivitySubcommand,
}

#[derive(Debug, Subcommand)]
pub enum ActivitySubcommand {
    Overview(LimitArgs),
    Locks,
    Slow(LimitArgs),
    LongRunning(LongRunningArgs),
    Cancel(ActivityActionArgs),
    Terminate(ActivityActionArgs),
    CancelPid(PidArgs),
    TerminatePid(PidArgs),
    PgStatTop(LimitArgs),
}

#[derive(Debug, Args)]
pub struct LimitArgs {
    #[arg(default_value_t = 20)]
    pub limit: u32,
}

#[derive(Debug, Args)]
pub struct LongRunningArgs {
    #[arg(default_value_t = 5)]
    pub minutes: u32,

    #[arg(default_value_t = 20)]
    pub limit: u32,
}

#[derive(Debug, Args)]
pub struct ActivityActionArgs {
    #[arg(long)]
    pub query: Option<String>,

    #[arg(long)]
    pub user: Option<String>,

    #[arg(long)]
    pub pid: Vec<i32>,

    #[arg(long, default_value_t = 20)]
    pub limit: u32,

    #[arg(long, action = ArgAction::SetTrue)]
    pub yes: bool,
}

#[derive(Debug, Args)]
pub struct PidArgs {
    #[arg(long, value_delimiter = ',')]
    pub pid: Vec<i32>,

    #[arg(long, action = ArgAction::SetTrue)]
    pub yes: bool,
}

#[derive(Debug, Args)]
pub struct SchemaCommand {
    #[command(subcommand)]
    pub command: SchemaSubcommand,
}

#[derive(Debug, Subcommand)]
pub enum SchemaSubcommand {
    Inspect,
    Diff(SchemaDiffArgs),
    Dump(DumpOutputArgs),
    TableSizes(LimitArgs),
    IndexHealth(LimitArgs),
    MissingFkIndexes,
    VacuumStatus,
    Roles,
}

#[derive(Debug, Args)]
pub struct SchemaDiffArgs {
    pub profile_a: Option<String>,
    pub profile_b: Option<String>,

    #[arg(long)]
    pub url_a: Option<String>,

    #[arg(long)]
    pub url_b: Option<String>,
}

#[derive(Debug, Args)]
pub struct DumpOutputArgs {
    pub output: Option<PathBuf>,
}

#[derive(Debug, Args)]
pub struct DumpCommand {
    #[command(subcommand)]
    pub command: DumpSubcommand,
}

#[derive(Debug, Subcommand)]
pub enum DumpSubcommand {
    Schema(DumpOutputArgs),
    Data(DumpOutputArgs),
    Restore(RestoreArgs),
}

#[derive(Debug, Args)]
pub struct RestoreArgs {
    pub input: PathBuf,
}

#[derive(Debug, Args)]
pub struct MigrationCommand {
    #[command(subcommand)]
    pub command: MigrationSubcommand,
}

#[derive(Debug, Subcommand)]
pub enum MigrationSubcommand {
    Release(MigrationReleaseArgs),
}

#[derive(Debug, Args, Clone)]
pub struct MigrationReleaseArgs {
    #[arg(long)]
    pub summary: Option<String>,

    #[arg(long, default_value = "prerelease.sql")]
    pub pending_file: String,

    #[arg(long)]
    pub migrations_path: Option<PathBuf>,

    #[arg(long)]
    pub slug: Option<String>,

    #[arg(long)]
    pub timestamp: Option<String>,

    #[arg(long, action = ArgAction::SetTrue)]
    pub dry_run: bool,
}

#[derive(Debug, Args)]
pub struct DocsCommand {
    #[command(subcommand)]
    pub command: DocsSubcommand,
}

#[derive(Debug, Subcommand)]
pub enum DocsSubcommand {
    Search(DocsSearchArgs),
}

#[derive(Debug, Args)]
pub struct DocsSearchArgs {
    pub query: String,

    #[arg(default_value_t = 10)]
    pub limit: usize,
}
