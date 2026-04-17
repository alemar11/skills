use anyhow::{Context, Result, anyhow, bail};
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::env;
use std::fs;
use std::io::{self, IsTerminal, Write};
use std::path::{Path, PathBuf};
use std::process::Command;
use url::Url;

pub const LATEST_SCHEMA_VERSION: &str = "2.0.0";
const DEFAULT_PROFILE: &str = "local";
const CONFIG_FILENAME: &str = "config.toml";
const LEGACY_CONFIG_FILENAME: &str = "postgres.toml";

#[derive(Debug, Clone, Serialize)]
pub struct RuntimeContext {
    pub project_root: Option<PathBuf>,
    pub config_path: Option<PathBuf>,
    pub toml_path: Option<PathBuf>,
    pub profile_name: String,
    pub url: String,
    pub sslmode: String,
    pub url_source: String,
    pub application_name: String,
}

#[derive(Debug, Clone)]
pub struct RuntimeOptions {
    pub project_root_override: Option<PathBuf>,
    pub profile_override: Option<String>,
    pub url_override: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct SkillConfig {
    #[serde(default)]
    pub schema_version: Option<String>,
    #[serde(default)]
    pub defaults: DefaultsConfig,
    #[serde(default)]
    pub tools: ToolCollection,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct DefaultsConfig {
    #[serde(default)]
    pub profile: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct ToolCollection {
    #[serde(default)]
    pub postgres: PostgresToolConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct PostgresToolConfig {
    #[serde(default)]
    pub host: Option<String>,
    #[serde(default)]
    pub port: Option<u16>,
    #[serde(default)]
    pub database: Option<String>,
    #[serde(default)]
    pub user: Option<String>,
    #[serde(default)]
    pub password: Option<String>,
    #[serde(default)]
    pub sslmode: Option<BoolLike>,
    #[serde(default)]
    pub url: Option<String>,
    #[serde(default)]
    pub description: Option<String>,
    #[serde(default)]
    pub migrations_path: Option<String>,
    #[serde(default)]
    pub profiles: BTreeMap<String, ProfileConfig>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct ProfileConfig {
    #[serde(default)]
    pub project: Option<String>,
    #[serde(default)]
    pub description: Option<String>,
    #[serde(default)]
    pub migrations_path: Option<String>,
    #[serde(default)]
    pub host: Option<String>,
    #[serde(default)]
    pub port: Option<u16>,
    #[serde(default)]
    pub database: Option<String>,
    #[serde(default)]
    pub user: Option<String>,
    #[serde(default)]
    pub password: Option<String>,
    #[serde(default)]
    pub sslmode: Option<BoolLike>,
    #[serde(default)]
    pub url: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
struct LegacySkillConfig {
    #[serde(default)]
    configuration: LegacyConfiguration,
    #[serde(default)]
    database: LegacyDatabaseConfig,
    #[serde(default)]
    migrations: Option<LegacyMigrationsConfig>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
struct LegacyConfiguration {
    #[serde(default)]
    schema_version: Option<String>,
    #[serde(default)]
    pg_bin_dir: Option<String>,
    #[serde(default)]
    pg_bin_path: Option<String>,
    #[serde(default)]
    python_bin: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
struct LegacyMigrationsConfig {
    #[serde(default)]
    path: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
struct LegacyDatabaseConfig {
    #[serde(default)]
    host: Option<String>,
    #[serde(default)]
    port: Option<u16>,
    #[serde(default)]
    database: Option<String>,
    #[serde(default)]
    user: Option<String>,
    #[serde(default)]
    password: Option<String>,
    #[serde(default)]
    sslmode: Option<BoolLike>,
    #[serde(default)]
    url: Option<String>,
    #[serde(default)]
    description: Option<String>,
    #[serde(default)]
    migrations_path: Option<String>,
    #[serde(flatten)]
    profiles: BTreeMap<String, ProfileConfig>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq, Eq)]
#[serde(untagged)]
pub enum BoolLike {
    Bool(bool),
    String(String),
    #[default]
    Empty,
}

impl BoolLike {
    pub fn as_bool(&self) -> Result<Option<bool>> {
        match self {
            BoolLike::Bool(value) => Ok(Some(*value)),
            BoolLike::String(value) => parse_sslmode_bool(value).map(Some),
            BoolLike::Empty => Ok(None),
        }
    }
}

#[derive(Debug, Clone, Serialize)]
pub struct ResolvedProfile {
    pub name: String,
    pub description: Option<String>,
    pub url: String,
    pub sslmode: bool,
    pub migrations_path: Option<String>,
}

pub fn canonical_config_path(project_root: &Path) -> PathBuf {
    project_root.join(".skills/postgres").join(CONFIG_FILENAME)
}

pub fn legacy_config_path(project_root: &Path) -> PathBuf {
    project_root
        .join(".skills/postgres")
        .join(LEGACY_CONFIG_FILENAME)
}

pub fn runtime_context(options: &RuntimeOptions, skill_root: &Path) -> Result<RuntimeContext> {
    if env::var("PROJECT_ROOT").is_ok() {
        bail!("Unsupported environment variable 'PROJECT_ROOT'. Use 'DB_PROJECT_ROOT' instead.");
    }

    let override_project_root = options
        .project_root_override
        .clone()
        .or_else(|| env::var("DB_PROJECT_ROOT").ok().map(PathBuf::from));

    if let Some(url) = options
        .url_override
        .clone()
        .or_else(|| env_url().ok().flatten())
    {
        let sslmode = sslmode_from_url(&url).unwrap_or_else(|| "disable".to_string());
        let profile_name = options
            .profile_override
            .clone()
            .or_else(|| env::var("DB_PROFILE").ok())
            .unwrap_or_else(|| DEFAULT_PROFILE.to_string());
        let config_path = override_project_root
            .as_ref()
            .map(|root| canonical_config_path(root));
        return Ok(RuntimeContext {
            project_root: override_project_root,
            config_path: config_path.clone(),
            toml_path: config_path,
            profile_name,
            url,
            sslmode,
            url_source: "env".to_string(),
            application_name: application_name(),
        });
    }

    let project_root = resolve_project_root(options.project_root_override.clone(), skill_root)?;
    let config_path = canonical_config_path(&project_root);
    if !config_path.exists() && !legacy_config_path(&project_root).exists() {
        bail!(
            "config.toml not found at {}. Set DB_URL for a one-off connection or bootstrap a profile.",
            config_path.display()
        );
    }

    let config = load_and_migrate_config(&config_path)?;
    let profile_name = choose_profile(
        &config,
        options
            .profile_override
            .clone()
            .or_else(|| env::var("DB_PROFILE").ok()),
    )?;
    let resolved = resolve_profile(&config, &profile_name)?;

    Ok(RuntimeContext {
        project_root: Some(project_root),
        config_path: Some(config_path.clone()),
        toml_path: Some(config_path),
        profile_name: resolved.name,
        url: resolved.url,
        sslmode: if resolved.sslmode {
            "require"
        } else {
            "disable"
        }
        .to_string(),
        url_source: "config".to_string(),
        application_name: application_name(),
    })
}

pub fn load_and_migrate_config(path: &Path) -> Result<SkillConfig> {
    let read_path = if path.exists() {
        path.to_path_buf()
    } else if let Some(legacy_path) = sibling_legacy_config_path(path).filter(|p| p.exists()) {
        legacy_path
    } else {
        bail!(
            "config.toml not found at {}. Set DB_URL for a one-off connection or bootstrap a profile.",
            path.display()
        );
    };

    let raw = fs::read_to_string(&read_path)
        .with_context(|| format!("Failed to read postgres config at {}", read_path.display()))?;
    let mut config = parse_config(&raw)?;
    migrate_config_in_place(&mut config)?;
    save_config(path, &config)?;
    Ok(config)
}

pub fn save_config(path: &Path, config: &SkillConfig) -> Result<()> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }
    let content = toml::to_string_pretty(config).context("Failed to serialize postgres config")?;
    fs::write(path, content)
        .with_context(|| format!("Failed to write postgres config at {}", path.display()))
}

fn parse_config(raw: &str) -> Result<SkillConfig> {
    let value: toml::Value = toml::from_str(raw).context("Failed to parse postgres config")?;
    let table = value
        .as_table()
        .ok_or_else(|| anyhow!("Postgres config must be a TOML table."))?;

    if table.contains_key("tools") || table.contains_key("defaults") || table.contains_key("schema_version") {
        value
            .try_into()
            .context("Failed to decode config.toml into the canonical postgres config schema")
    } else {
        let legacy: LegacySkillConfig = value
            .try_into()
            .context("Failed to decode postgres.toml into the legacy postgres config schema")?;
        migrate_legacy_config(legacy)
    }
}

pub fn migrate_config_in_place(config: &mut SkillConfig) -> Result<()> {
    let schema_version = config.schema_version.clone().unwrap_or_default();
    if !schema_version.is_empty() && schema_version != LATEST_SCHEMA_VERSION {
        bail!("Unsupported schema_version: {schema_version}");
    }

    if config.defaults.profile.as_deref() == Some("") {
        config.defaults.profile = None;
    }

    normalize_canonical_sslmodes(config)?;
    config.schema_version = Some(LATEST_SCHEMA_VERSION.to_string());
    Ok(())
}

fn migrate_legacy_config(mut legacy: LegacySkillConfig) -> Result<SkillConfig> {
    let schema_version = legacy.configuration.schema_version.take().unwrap_or_default();
    if !schema_version.is_empty()
        && schema_version != "1"
        && schema_version != "1.0.0"
        && schema_version != "1.1.0"
    {
        bail!("Unsupported schema_version: {schema_version}");
    }

    if let Some(value) = legacy.database.sslmode.clone() {
        legacy.database.sslmode = Some(BoolLike::Bool(value.as_bool()?.unwrap_or(false)));
    } else {
        legacy.database.sslmode = Some(BoolLike::Bool(false));
    }
    for profile in legacy.database.profiles.values_mut() {
        if let Some(value) = profile.sslmode.clone() {
            profile.sslmode = Some(BoolLike::Bool(value.as_bool()?.unwrap_or(false)));
        }
    }

    let default_profile = if legacy.database.profiles.len() == 1 {
        legacy.database.profiles.keys().next().cloned()
    } else if legacy.database.profiles.contains_key(DEFAULT_PROFILE) {
        Some(DEFAULT_PROFILE.to_string())
    } else {
        None
    };

    let mut config = SkillConfig {
        schema_version: Some(LATEST_SCHEMA_VERSION.to_string()),
        defaults: DefaultsConfig {
            profile: default_profile,
        },
        tools: ToolCollection {
            postgres: PostgresToolConfig {
                host: legacy.database.host,
                port: legacy.database.port,
                database: legacy.database.database,
                user: legacy.database.user,
                password: legacy.database.password,
                sslmode: legacy.database.sslmode,
                url: legacy.database.url,
                description: legacy.database.description,
                migrations_path: legacy
                    .database
                    .migrations_path
                    .or_else(|| legacy.migrations.and_then(|migrations| migrations.path)),
                profiles: legacy.database.profiles,
            },
        },
    };
    migrate_config_in_place(&mut config)?;
    Ok(config)
}

fn normalize_canonical_sslmodes(config: &mut SkillConfig) -> Result<()> {
    if config.tools.postgres.sslmode.is_none() {
        config.tools.postgres.sslmode = Some(BoolLike::Bool(false));
    }
    if let Some(sslmode) = config.tools.postgres.sslmode.clone() {
        config.tools.postgres.sslmode = Some(BoolLike::Bool(sslmode.as_bool()?.unwrap_or(false)));
    }

    for profile in config.tools.postgres.profiles.values_mut() {
        if let Some(value) = profile.sslmode.clone() {
            profile.sslmode = Some(BoolLike::Bool(value.as_bool()?.unwrap_or(false)));
        }
    }

    Ok(())
}

fn choose_profile(config: &SkillConfig, requested: Option<String>) -> Result<String> {
    if let Some(requested) = requested {
        if config.tools.postgres.profiles.contains_key(&requested) {
            return Ok(requested);
        }
        bail!("Profile '{requested}' not found in config.toml.");
    }

    if config.tools.postgres.profiles.len() == 1 {
        return Ok(config
            .tools
            .postgres
            .profiles
            .keys()
            .next()
            .expect("profile")
            .to_string());
    }

    if let Some(default_profile) = &config.defaults.profile
        && config.tools.postgres.profiles.contains_key(default_profile)
    {
        return Ok(default_profile.clone());
    }

    if config.tools.postgres.profiles.contains_key(DEFAULT_PROFILE) {
        return Ok(DEFAULT_PROFILE.to_string());
    }

    if io::stdin().is_terminal() {
        eprintln!("Multiple profiles found in config.toml:");
        for (name, profile) in &config.tools.postgres.profiles {
            let description = profile.description.clone().unwrap_or_default();
            let suffix = if description.is_empty() {
                String::new()
            } else {
                format!(" ({description})")
            };
            eprintln!("  - {name}{suffix}");
        }
        let mut input = String::new();
        eprint!("Profile name: ");
        let _ = io::stderr().flush();
        io::stdin().read_line(&mut input)?;
        let selected = input.trim();
        if config.tools.postgres.profiles.contains_key(selected) {
            return Ok(selected.to_string());
        }
    }

    bail!("DB_PROFILE is required when config.toml contains multiple profiles.")
}

pub fn resolve_profile(config: &SkillConfig, name: &str) -> Result<ResolvedProfile> {
    let tool = &config.tools.postgres;
    let profile = tool
        .profiles
        .get(name)
        .ok_or_else(|| anyhow!("Profile '{name}' not found in config.toml."))?;

    let url = if let Some(url) = profile.url.clone().or_else(|| tool.url.clone()) {
        url
    } else {
        let host = profile
            .host
            .clone()
            .or_else(|| tool.host.clone())
            .unwrap_or_else(|| "localhost".to_string());
        let port = profile.port.or(tool.port).unwrap_or(5432);
        let database = profile
            .database
            .clone()
            .or_else(|| tool.database.clone())
            .ok_or_else(|| anyhow!("Profile '{name}' is missing database."))?;
        let user = profile
            .user
            .clone()
            .or_else(|| tool.user.clone())
            .ok_or_else(|| anyhow!("Profile '{name}' is missing user."))?;
        let password = profile
            .password
            .clone()
            .or_else(|| tool.password.clone())
            .ok_or_else(|| anyhow!("Profile '{name}' is missing password."))?;
        let sslmode = profile
            .sslmode
            .clone()
            .or_else(|| tool.sslmode.clone())
            .unwrap_or(BoolLike::Bool(false))
            .as_bool()?
            .unwrap_or(false);

        build_url(
            &host,
            port,
            &database,
            &user,
            &password,
            if sslmode { "require" } else { "disable" },
        )?
    };

    let sslmode = profile
        .sslmode
        .clone()
        .or_else(|| tool.sslmode.clone())
        .unwrap_or(BoolLike::Bool(false))
        .as_bool()?
        .unwrap_or(false);

    Ok(ResolvedProfile {
        name: name.to_string(),
        description: profile
            .description
            .clone()
            .or_else(|| tool.description.clone()),
        url,
        sslmode,
        migrations_path: profile
            .migrations_path
            .clone()
            .or_else(|| tool.migrations_path.clone()),
    })
}

pub fn update_sslmode(path: &Path, profile_name: &str, enabled: bool) -> Result<()> {
    let mut config = load_and_migrate_config(path)?;
    let profile = config
        .tools
        .postgres
        .profiles
        .get_mut(profile_name)
        .ok_or_else(|| anyhow!("Profile '{profile_name}' not found in config.toml."))?;
    profile.sslmode = Some(BoolLike::Bool(enabled));
    save_config(path, &config)
}

pub fn env_url() -> Result<Option<String>> {
    if let Ok(url) = env::var("DB_URL") {
        return Ok(Some(url));
    }
    for key in ["DATABASE_URL", "POSTGRES_URL", "POSTGRESQL_URL"] {
        if let Ok(url) = env::var(key) {
            return Ok(Some(url));
        }
    }
    let host = env::var("PGHOST").ok();
    let port = env::var("PGPORT").ok();
    let database = env::var("PGDATABASE").ok();
    let user = env::var("PGUSER").ok();
    let password = env::var("PGPASSWORD").ok();
    let sslmode = env::var("PGSSLMODE").unwrap_or_else(|_| "disable".to_string());
    match (host, port, database, user, password) {
        (Some(host), Some(port), Some(database), Some(user), Some(password)) => {
            let port = port.parse::<u16>().context("Invalid PGPORT value")?;
            Ok(Some(build_url(
                &host, port, &database, &user, &password, &sslmode,
            )?))
        }
        _ => Ok(None),
    }
}

pub fn resolve_project_root(override_root: Option<PathBuf>, skill_root: &Path) -> Result<PathBuf> {
    if let Some(root) =
        override_root.or_else(|| env::var("DB_PROJECT_ROOT").ok().map(PathBuf::from))
    {
        return Ok(root);
    }

    if let Ok(output) = Command::new("git")
        .arg("-C")
        .arg(env::current_dir()?)
        .arg("rev-parse")
        .arg("--show-toplevel")
        .output()
    {
        if output.status.success() {
            let root = String::from_utf8_lossy(&output.stdout).trim().to_string();
            if !root.is_empty() {
                let root_path = PathBuf::from(root);
                if !root_path.starts_with(skill_root) {
                    return Ok(root_path);
                }
            }
        }
    }

    let cwd = env::current_dir()?;
    if cwd.starts_with(skill_root) {
        bail!(
            "Project root resolved to the postgres skill directory. Set DB_PROJECT_ROOT or run from the target project root."
        );
    }
    Ok(cwd)
}

pub fn build_url(
    host: &str,
    port: u16,
    database: &str,
    user: &str,
    password: &str,
    sslmode: &str,
) -> Result<String> {
    let mut url = Url::parse("postgresql://localhost").context("Failed to initialize URL")?;
    url.set_host(Some(host)).context("Invalid host")?;
    url.set_port(Some(port))
        .map_err(|_| anyhow!("Invalid port"))?;
    url.set_username(user)
        .map_err(|_| anyhow!("Invalid user"))?;
    url.set_password(Some(password))
        .map_err(|_| anyhow!("Invalid password"))?;
    url.set_path(&format!("/{database}"));
    url.query_pairs_mut().append_pair("sslmode", sslmode);
    Ok(url.to_string())
}

pub fn sslmode_from_url(url: &str) -> Option<String> {
    if let Ok(parsed) = Url::parse(url) {
        for (key, value) in parsed.query_pairs() {
            if key == "sslmode" {
                return Some(normalize_sslmode_value(&value));
            }
        }
    }
    None
}

pub fn application_name() -> String {
    env::var("DB_APPLICATION_NAME").unwrap_or_else(|_| "codex-postgres-skill".to_string())
}

pub fn parse_sslmode_bool(value: &str) -> Result<bool> {
    let lowered = value.trim().to_ascii_lowercase();
    match lowered.as_str() {
        "true" | "t" | "1" | "yes" | "y" | "on" | "enable" | "enabled" | "require" | "required"
        | "verify-ca" | "verify-full" => Ok(true),
        "false" | "f" | "0" | "no" | "n" | "off" | "disable" | "disabled" => Ok(false),
        _ => bail!("Unrecognized sslmode value: {value}"),
    }
}

pub fn normalize_sslmode_value(value: &str) -> String {
    if parse_sslmode_bool(value).unwrap_or(false) {
        "require".to_string()
    } else {
        "disable".to_string()
    }
}

pub fn prompt(text: &str, default: Option<&str>, secret: bool) -> Result<String> {
    if secret {
        eprint!("{text}: ");
    } else if let Some(default) = default {
        eprint!("{text} [{default}]: ");
    } else {
        eprint!("{text}: ");
    }
    io::stderr().flush()?;
    let mut value = String::new();
    io::stdin().read_line(&mut value)?;
    let value = value.trim().to_string();
    if value.is_empty() {
        Ok(default.unwrap_or_default().to_string())
    } else {
        Ok(value)
    }
}

pub fn bootstrap_profile(path: &Path, save: bool) -> Result<ResolvedProfile> {
    let mut config = if path.exists() || sibling_legacy_config_path(path).is_some_and(|p| p.exists())
    {
        load_and_migrate_config(path)?
    } else {
        SkillConfig::default()
    };

    let profile_name = prompt("Profile name", Some(DEFAULT_PROFILE), false)?;
    let host = prompt("Host", Some("localhost"), false)?;
    let port = prompt("Port", Some("5432"), false)?
        .parse::<u16>()
        .context("Invalid port")?;
    let database = prompt("Database", None, false)?;
    let user = prompt("User", None, false)?;
    let password = prompt("Password", None, true)?;
    let sslmode = prompt("sslmode (true/false)", Some("false"), false)?;
    let description = prompt("Description", Some(""), false)?;
    let migrations_path = prompt("migrations_path", Some(""), false)?;

    let ssl_enabled = parse_sslmode_bool(&sslmode)?;
    let resolved = ResolvedProfile {
        name: profile_name.clone(),
        description: if description.is_empty() {
            None
        } else {
            Some(description.clone())
        },
        url: build_url(
            &host,
            port,
            &database,
            &user,
            &password,
            if ssl_enabled { "require" } else { "disable" },
        )?,
        sslmode: ssl_enabled,
        migrations_path: if migrations_path.is_empty() {
            None
        } else {
            Some(migrations_path.clone())
        },
    };

    if save {
        config.schema_version = Some(LATEST_SCHEMA_VERSION.to_string());
        config.defaults.profile = Some(profile_name.clone());
        if config.tools.postgres.sslmode.is_none() {
            config.tools.postgres.sslmode = Some(BoolLike::Bool(false));
        }
        if config.tools.postgres.migrations_path.is_none() && !migrations_path.is_empty() {
            config.tools.postgres.migrations_path = Some(migrations_path.clone());
        }
        config.tools.postgres.profiles.insert(
            profile_name.clone(),
            ProfileConfig {
                description: resolved.description.clone(),
                migrations_path: resolved.migrations_path.clone(),
                host: Some(host),
                port: Some(port),
                database: Some(database),
                user: Some(user),
                password: Some(password),
                sslmode: Some(BoolLike::Bool(ssl_enabled)),
                url: None,
                ..ProfileConfig::default()
            },
        );
        save_config(path, &config)?;
    }

    Ok(resolved)
}

fn sibling_legacy_config_path(path: &Path) -> Option<PathBuf> {
    (path.file_name().and_then(|name| name.to_str()) == Some(CONFIG_FILENAME))
        .then(|| path.with_file_name(LEGACY_CONFIG_FILENAME))
}

#[cfg(test)]
mod tests {
    use super::*;
    use pretty_assertions::assert_eq;
    use tempfile::tempdir;

    #[test]
    fn migrates_legacy_schema_to_canonical_config() {
        let temp = tempdir().unwrap();
        let project_root = temp.path();
        let legacy_path = legacy_config_path(project_root);
        fs::create_dir_all(legacy_path.parent().unwrap()).unwrap();
        fs::write(
            &legacy_path,
            r#"[configuration]
schema_version = "1.1.0"
pg_bin_dir = "/tmp/pg"
python_bin = "/usr/bin/python3"

[database]
sslmode = "require"

[database.local]
description = "Local"
host = "127.0.0.1"
port = 5432
database = "app"
user = "postgres"
password = "postgres"
sslmode = "disable"
migrations_path = "db/migrations"

[migrations]
path = "db/migrations"
"#,
        )
        .unwrap();

        let canonical_path = canonical_config_path(project_root);
        let config = load_and_migrate_config(&canonical_path).unwrap();
        let written = fs::read_to_string(&canonical_path).unwrap();

        assert_eq!(config.schema_version.as_deref(), Some(LATEST_SCHEMA_VERSION));
        assert_eq!(config.defaults.profile.as_deref(), Some("local"));
        assert_eq!(
            config.tools.postgres.migrations_path.as_deref(),
            Some("db/migrations")
        );
        assert_eq!(
            config.tools.postgres.profiles["local"].sslmode,
            Some(BoolLike::Bool(false))
        );
        assert!(written.contains("schema_version = \"2.0.0\""));
        assert!(written.contains("[defaults]"));
        assert!(written.contains("[tools.postgres]"));
        assert!(written.contains("[tools.postgres.profiles.local]"));
        assert!(!written.contains("pg_bin_dir"));
        assert!(!written.contains("python_bin"));
    }

    #[test]
    fn migrates_missing_legacy_schema_and_normalizes_sslmode() {
        let temp = tempdir().unwrap();
        let project_root = temp.path();
        let legacy_path = legacy_config_path(project_root);
        fs::create_dir_all(legacy_path.parent().unwrap()).unwrap();
        fs::write(
            &legacy_path,
            r#"[database]
sslmode = "require"

[database.alpha]
database = "app"
user = "postgres"
password = "postgres"
sslmode = "require"
"#,
        )
        .unwrap();

        let config = load_and_migrate_config(&canonical_config_path(project_root)).unwrap();
        assert_eq!(config.schema_version.as_deref(), Some(LATEST_SCHEMA_VERSION));
        assert_eq!(
            config.tools.postgres.sslmode,
            Some(BoolLike::Bool(true))
        );
        assert_eq!(
            config.tools.postgres.profiles["alpha"].sslmode,
            Some(BoolLike::Bool(true))
        );
    }

    #[test]
    fn canonical_config_wins_over_legacy_file() {
        let temp = tempdir().unwrap();
        let project_root = temp.path();
        let canonical_path = canonical_config_path(project_root);
        let legacy_path = legacy_config_path(project_root);
        fs::create_dir_all(canonical_path.parent().unwrap()).unwrap();
        fs::write(
            &canonical_path,
            r#"schema_version = "2.0.0"

[defaults]
profile = "local"

[tools.postgres]
sslmode = false

[tools.postgres.profiles.local]
database = "canonical"
user = "postgres"
password = "postgres"
"#,
        )
        .unwrap();
        fs::write(
            &legacy_path,
            r#"[database]
sslmode = false

[database.local]
database = "legacy"
user = "postgres"
password = "postgres"
"#,
        )
        .unwrap();

        let config = load_and_migrate_config(&canonical_path).unwrap();
        assert_eq!(
            config.tools.postgres.profiles["local"].database.as_deref(),
            Some("canonical")
        );
    }

    #[test]
    fn update_sslmode_rewrites_canonical_config() {
        let temp = tempdir().unwrap();
        let canonical_path = canonical_config_path(temp.path());
        fs::create_dir_all(canonical_path.parent().unwrap()).unwrap();
        fs::write(
            &canonical_path,
            r#"schema_version = "2.0.0"

[defaults]
profile = "local"

[tools.postgres]
sslmode = false

[tools.postgres.profiles.local]
database = "app"
user = "postgres"
password = "postgres"
sslmode = false
"#,
        )
        .unwrap();

        update_sslmode(&canonical_path, "local", true).unwrap();
        let config = load_and_migrate_config(&canonical_path).unwrap();
        assert_eq!(
            config.tools.postgres.profiles["local"].sslmode,
            Some(BoolLike::Bool(true))
        );
    }

    #[test]
    fn builds_url() {
        let url = build_url("localhost", 5432, "db", "user", "pw", "disable").unwrap();
        assert!(url.contains("sslmode=disable"));
        assert!(url.contains("localhost"));
    }
}
