use anyhow::{Context, Result, anyhow, bail};
use serde::{Deserialize, Deserializer, Serialize, Serializer, de};
use std::collections::BTreeMap;
use std::env;
use std::fs;
#[cfg(unix)]
use std::fs::File;
#[cfg(not(unix))]
use std::fs::OpenOptions;
use std::io::{self, IsTerminal, Write};
use std::path::{Path, PathBuf};
use std::process::Command;
use tempfile::NamedTempFile;
use url::Url;

pub const LATEST_SCHEMA_VERSION: &str = "3.0.0";
const DEFAULT_PROFILE: &str = "local";
const CONFIG_FILENAME: &str = "config.toml";
const LEGACY_CONFIG_FILENAME: &str = "postgres.toml";

#[derive(Debug, Clone, Serialize)]
pub struct RuntimeContext {
    pub project_root: Option<PathBuf>,
    pub config_path: Option<PathBuf>,
    pub toml_path: Option<PathBuf>,
    pub profile_name: String,
    #[serde(serialize_with = "serialize_redacted_url")]
    pub url: String,
    pub ssl_mode: SslMode,
    pub access_mode: AccessMode,
    pub url_source: String,
    pub application_name: String,
}

#[derive(Debug, Clone)]
pub struct RuntimeOptions {
    pub project_root_override: Option<PathBuf>,
    pub profile_override: Option<String>,
    pub url_override: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq, Eq)]
pub struct SkillConfig {
    #[serde(default)]
    pub schema_version: Option<String>,
    #[serde(default)]
    pub defaults: DefaultsConfig,
    #[serde(default)]
    pub tools: ToolCollection,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq, Eq)]
pub struct DefaultsConfig {
    #[serde(default)]
    pub profile: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq, Eq)]
pub struct ToolCollection {
    #[serde(default)]
    pub postgres: PostgresToolConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq, Eq)]
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
    #[serde(alias = "sslmode")]
    pub ssl_mode: Option<SslMode>,
    #[serde(default)]
    pub url: Option<String>,
    #[serde(default)]
    pub description: Option<String>,
    #[serde(default)]
    #[serde(alias = "access")]
    pub access_mode: Option<AccessMode>,
    #[serde(default)]
    pub migrations_path: Option<String>,
    #[serde(default)]
    pub profiles: BTreeMap<String, ProfileConfig>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq, Eq)]
pub struct ProfileConfig {
    #[serde(default)]
    pub project: Option<String>,
    #[serde(default)]
    pub description: Option<String>,
    #[serde(default)]
    #[serde(alias = "access")]
    pub access_mode: Option<AccessMode>,
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
    #[serde(alias = "sslmode")]
    pub ssl_mode: Option<SslMode>,
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
    #[serde(alias = "ssl_mode")]
    sslmode: Option<SslMode>,
    #[serde(default)]
    url: Option<String>,
    #[serde(default)]
    description: Option<String>,
    #[serde(default)]
    #[serde(alias = "access_mode")]
    access: Option<AccessMode>,
    #[serde(default)]
    migrations_path: Option<String>,
    #[serde(flatten)]
    profiles: BTreeMap<String, ProfileConfig>,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, Default, PartialEq, Eq)]
pub enum AccessMode {
    #[serde(rename = "read")]
    Read,
    #[serde(rename = "write")]
    Write,
    #[default]
    #[serde(rename = "read-write", alias = "read_write")]
    ReadWrite,
}

impl AccessMode {
    pub fn as_str(&self) -> &'static str {
        match self {
            AccessMode::Read => "read",
            AccessMode::Write => "write",
            AccessMode::ReadWrite => "read-write",
        }
    }
}

#[derive(Debug, Clone, Copy, Serialize, Default, PartialEq, Eq)]
pub enum SslMode {
    #[default]
    #[serde(rename = "disable")]
    Disable,
    #[serde(rename = "require")]
    Require,
}

impl SslMode {
    pub fn as_str(&self) -> &'static str {
        match self {
            SslMode::Disable => "disable",
            SslMode::Require => "require",
        }
    }
}

impl<'de> Deserialize<'de> for SslMode {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        #[derive(Deserialize)]
        #[serde(untagged)]
        enum LegacySslMode {
            Bool(bool),
            String(String),
        }

        match LegacySslMode::deserialize(deserializer)? {
            LegacySslMode::Bool(false) => Ok(SslMode::Disable),
            LegacySslMode::Bool(true) => Ok(SslMode::Require),
            LegacySslMode::String(value) => {
                parse_legacy_ssl_mode(&value).map_err(de::Error::custom)
            }
        }
    }
}

#[derive(Debug, Clone, Serialize)]
pub struct ResolvedProfile {
    pub name: String,
    pub description: Option<String>,
    #[serde(serialize_with = "serialize_redacted_url")]
    pub url: String,
    pub ssl_mode: SslMode,
    pub access_mode: AccessMode,
    pub migrations_path: Option<String>,
}

#[derive(Debug)]
pub struct ConfigMigrationResult {
    pub config: SkillConfig,
    pub source_path: PathBuf,
    pub backup_path: Option<PathBuf>,
    pub migration_outcome: &'static str,
}

pub fn canonical_config_path(project_root: &Path) -> PathBuf {
    project_root.join(".skills/postgres").join(CONFIG_FILENAME)
}

fn serialize_redacted_url<S>(url: &str, serializer: S) -> std::result::Result<S::Ok, S::Error>
where
    S: Serializer,
{
    serializer.serialize_str(&redact_connection_url(url))
}

pub fn redact_connection_url(url: &str) -> String {
    let Ok(mut parsed) = Url::parse(url) else {
        return "<redacted-invalid-url>".to_string();
    };
    if parsed.password().is_some() {
        let _ = parsed.set_password(Some("***"));
    }
    let query_pairs = parsed
        .query_pairs()
        .map(|(key, value)| (key.into_owned(), value.into_owned()))
        .collect::<Vec<_>>();
    if query_pairs.iter().any(|(key, _)| {
        key.eq_ignore_ascii_case("password") || key.eq_ignore_ascii_case("sslpassword")
    }) {
        parsed.set_query(None);
        let mut query = parsed.query_pairs_mut();
        for (key, value) in query_pairs {
            let value = if key.eq_ignore_ascii_case("password")
                || key.eq_ignore_ascii_case("sslpassword")
            {
                "***"
            } else {
                &value
            };
            query.append_pair(&key, value);
        }
    }
    parsed.to_string()
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

    let url = match &options.url_override {
        Some(url) => Some(url.clone()),
        None => env_url()?,
    };
    if let Some(url) = url {
        let ssl_mode = ssl_mode_from_url(&url).unwrap_or_default();
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
            ssl_mode,
            access_mode: AccessMode::ReadWrite,
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

    let config = load_config(&config_path)?;
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
        ssl_mode: resolved.ssl_mode,
        access_mode: resolved.access_mode,
        url_source: "config".to_string(),
        application_name: application_name(),
    })
}

/// Load and normalize config in memory without creating or rewriting files.
pub fn load_config(path: &Path) -> Result<SkillConfig> {
    let (config, _) = load_config_from_disk(path)?;
    Ok(config)
}

/// Load config and explicitly persist any legacy or schema normalization.
/// Callers must already have mutation authority.
pub fn load_and_migrate_config(path: &Path) -> Result<SkillConfig> {
    Ok(migrate_config_file(path)?.config)
}

/// Explicitly migrate config with a pre-migration backup and atomic canonical write.
pub fn migrate_config_file(path: &Path) -> Result<ConfigMigrationResult> {
    migrate_config_file_with_backup_root(path, None)
}

fn migrate_config_file_with_backup_root(
    path: &Path,
    backup_root: Option<&Path>,
) -> Result<ConfigMigrationResult> {
    let (config, loaded) = load_config_from_disk(path)?;
    let changed = loaded.needs_persisted_normalization
        || should_save_loaded_config(path, &loaded.read_path, &loaded.original, &config);
    let backup_path = if changed {
        let default_backup_root;
        let backup_root = match backup_root {
            Some(path) => path,
            None => {
                default_backup_root = config_backup_root(&loaded.read_path)?;
                &default_backup_root
            }
        };
        let backup_path = write_config_backup(
            &loaded.read_path,
            backup_root,
            loaded.original_content.as_bytes(),
        )?;
        save_config(path, &config)?;
        Some(backup_path)
    } else {
        None
    };
    Ok(ConfigMigrationResult {
        config,
        source_path: loaded.read_path,
        backup_path,
        migration_outcome: if changed { "migrated" } else { "no-change" },
    })
}

struct LoadedConfig {
    read_path: PathBuf,
    original: SkillConfig,
    original_content: String,
    needs_persisted_normalization: bool,
}

fn load_config_from_disk(path: &Path) -> Result<(SkillConfig, LoadedConfig)> {
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
    let needs_persisted_normalization = has_legacy_persisted_encoding(&raw)?;
    let mut config = parse_config(&raw)?;
    let original = config.clone();
    migrate_config_in_place(&mut config)?;
    Ok((
        config,
        LoadedConfig {
            read_path,
            original,
            original_content: raw,
            needs_persisted_normalization,
        },
    ))
}

pub fn save_config(path: &Path, config: &SkillConfig) -> Result<()> {
    let parent = path
        .parent()
        .ok_or_else(|| anyhow!("Postgres config path has no parent: {}", path.display()))?;
    fs::create_dir_all(parent)?;
    let content = toml::to_string_pretty(config).context("Failed to serialize postgres config")?;
    let mut temp = NamedTempFile::new_in(parent)
        .with_context(|| format!("Failed to create temp config in {}", parent.display()))?;
    temp.write_all(content.as_bytes())?;
    temp.as_file().sync_all()?;
    temp.persist(path)
        .map_err(|error| error.error)
        .with_context(|| format!("Failed to atomically write config at {}", path.display()))?;
    Ok(())
}

fn config_backup_root(config_path: &Path) -> Result<PathBuf> {
    select_config_backup_root(
        config_path,
        env::var_os("XDG_CACHE_HOME").map(PathBuf::from),
        env::var_os("HOME").map(PathBuf::from),
    )
}

fn select_config_backup_root(
    config_path: &Path,
    xdg_cache_home: Option<PathBuf>,
    home: Option<PathBuf>,
) -> Result<PathBuf> {
    let project_root = config_path
        .parent()
        .and_then(Path::parent)
        .and_then(Path::parent)
        .ok_or_else(|| {
            anyhow!(
                "Cannot resolve the consuming project root from postgres config {}",
                config_path.display()
            )
        })?;
    let resolved_project_root = resolve_for_containment(project_root)?;
    let candidates = [xdg_cache_home, home.map(|path| path.join(".cache"))];
    for cache_home in candidates.into_iter().flatten() {
        if !cache_home.is_absolute()
            || cache_home
                .components()
                .any(|component| matches!(component, std::path::Component::ParentDir))
        {
            continue;
        }
        let backup_root = cache_home
            .join("dotagents")
            .join("skills")
            .join("postgres")
            .join("config-backups");
        let resolved_backup_root = resolve_for_containment(&backup_root)?;
        if !resolved_backup_root.starts_with(&resolved_project_root) {
            return Ok(resolved_backup_root);
        }
    }
    bail!(
        "Cannot resolve a postgres config backup cache outside the consuming project {}. Set HOME or XDG_CACHE_HOME to an absolute external path.",
        resolved_project_root.display()
    )
}

fn resolve_for_containment(path: &Path) -> Result<PathBuf> {
    let absolute = if path.is_absolute() {
        path.to_path_buf()
    } else {
        env::current_dir()
            .context("Failed to resolve the current directory")?
            .join(path)
    };
    resolve_absolute_for_containment(&absolute)
}

fn resolve_absolute_for_containment(path: &Path) -> Result<PathBuf> {
    if path.exists() {
        return fs::canonicalize(path)
            .with_context(|| format!("Failed to resolve path {}", path.display()));
    }
    let parent = path
        .parent()
        .ok_or_else(|| anyhow!("Cannot resolve path {}", path.display()))?;
    let filename = path
        .file_name()
        .ok_or_else(|| anyhow!("Cannot resolve path {}", path.display()))?;
    Ok(resolve_absolute_for_containment(parent)?.join(filename))
}

fn backup_source_key(path: &Path) -> String {
    let normalized = fs::canonicalize(path).unwrap_or_else(|_| path.to_path_buf());
    let mut hash = 0xcbf29ce484222325_u64;
    for byte in normalized.to_string_lossy().as_bytes() {
        hash ^= u64::from(*byte);
        hash = hash.wrapping_mul(0x100000001b3);
    }
    format!("{hash:016x}")
}

#[cfg(unix)]
fn write_config_backup(path: &Path, backup_root: &Path, content: &[u8]) -> Result<PathBuf> {
    use std::ffi::{CString, OsStr};
    use std::os::fd::{AsRawFd, FromRawFd};
    use std::os::unix::ffi::OsStrExt;

    let backup_root = resolve_for_containment(backup_root)?;
    let directory = backup_root.join(backup_source_key(path));
    let backup_root_handle = open_or_create_absolute_directory(&backup_root)?;
    let source_key = directory
        .file_name()
        .ok_or_else(|| anyhow!("Postgres backup directory has no source key"))?;
    let source_key = CString::new(source_key.as_bytes())
        .context("Postgres backup source key contains a null byte")?;
    let directory_handle =
        open_or_create_child_directory(&backup_root_handle, &source_key, &directory)?;
    set_private_directory_handle(&directory_handle, &directory)?;
    let filename = path
        .file_name()
        .unwrap_or_else(|| OsStr::new(CONFIG_FILENAME))
        .to_string_lossy();
    for index in 0.. {
        let candidate_name = if index == 0 {
            format!("{filename}.bak")
        } else {
            format!("{filename}.bak.{index}")
        };
        let candidate = directory.join(&candidate_name);
        let candidate_name = CString::new(candidate_name.as_bytes())
            .context("Postgres backup filename contains a null byte")?;
        let descriptor = unsafe {
            libc::openat(
                directory_handle.as_raw_fd(),
                candidate_name.as_ptr(),
                libc::O_WRONLY | libc::O_CREAT | libc::O_EXCL | libc::O_NOFOLLOW | libc::O_CLOEXEC,
                0o600,
            )
        };
        if descriptor < 0 {
            let error = io::Error::last_os_error();
            if error.kind() == io::ErrorKind::AlreadyExists {
                continue;
            }
            return Err(error).with_context(|| {
                format!(
                    "Failed to create postgres config backup {}",
                    candidate.display()
                )
            });
        }
        let mut backup = unsafe { File::from_raw_fd(descriptor) };
        if let Err(error) = backup.write_all(content).and_then(|_| backup.sync_all()) {
            drop(backup);
            unsafe {
                libc::unlinkat(directory_handle.as_raw_fd(), candidate_name.as_ptr(), 0);
            }
            return Err(error).with_context(|| {
                format!(
                    "Failed to write postgres config backup {}",
                    candidate.display()
                )
            });
        }
        return Ok(candidate);
    }
    unreachable!("backup index iteration is unbounded")
}

#[cfg(unix)]
fn open_or_create_absolute_directory(path: &Path) -> Result<File> {
    use std::ffi::CString;
    use std::os::fd::FromRawFd;
    use std::os::unix::ffi::OsStrExt;
    use std::path::Component;

    if !path.is_absolute() {
        bail!(
            "Postgres backup directory must be absolute: {}",
            path.display()
        );
    }
    let root = CString::new("/").expect("root contains no null byte");
    let descriptor = unsafe {
        libc::open(
            root.as_ptr(),
            libc::O_RDONLY | libc::O_DIRECTORY | libc::O_NOFOLLOW | libc::O_CLOEXEC,
        )
    };
    if descriptor < 0 {
        return Err(io::Error::last_os_error()).context("Failed to open filesystem root");
    }
    let mut directory = unsafe { File::from_raw_fd(descriptor) };
    for component in path.components() {
        let Component::Normal(name) = component else {
            if matches!(component, Component::RootDir) {
                continue;
            }
            bail!(
                "Postgres backup directory contains an unsupported component: {}",
                path.display()
            );
        };
        let name = CString::new(name.as_bytes())
            .context("Postgres backup directory contains a null byte")?;
        directory = open_or_create_child_directory(&directory, &name, path)?;
    }
    set_private_directory_handle(&directory, path)?;
    Ok(directory)
}

#[cfg(not(unix))]
fn write_config_backup(path: &Path, backup_root: &Path, content: &[u8]) -> Result<PathBuf> {
    let directory = backup_root.join(backup_source_key(path));
    fs::create_dir_all(&directory).with_context(|| {
        format!(
            "Failed to create postgres config backup directory {}",
            directory.display()
        )
    })?;
    let filename = path
        .file_name()
        .and_then(|name| name.to_str())
        .unwrap_or(CONFIG_FILENAME);
    for index in 0.. {
        let candidate = if index == 0 {
            directory.join(format!("{filename}.bak"))
        } else {
            directory.join(format!("{filename}.bak.{index}"))
        };
        let mut backup = match OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&candidate)
        {
            Ok(file) => file,
            Err(error) if error.kind() == io::ErrorKind::AlreadyExists => continue,
            Err(error) => {
                return Err(error).with_context(|| {
                    format!(
                        "Failed to create postgres config backup {}",
                        candidate.display()
                    )
                });
            }
        };
        if let Err(error) = backup.write_all(content).and_then(|_| backup.sync_all()) {
            drop(backup);
            let _ = fs::remove_file(&candidate);
            return Err(error).with_context(|| {
                format!(
                    "Failed to write postgres config backup {}",
                    candidate.display()
                )
            });
        }
        return Ok(candidate);
    }
    unreachable!("backup index iteration is unbounded")
}

#[cfg(unix)]
fn open_or_create_child_directory(
    parent: &File,
    name: &std::ffi::CStr,
    display_path: &Path,
) -> Result<File> {
    use std::os::fd::{AsRawFd, FromRawFd};

    let result = unsafe { libc::mkdirat(parent.as_raw_fd(), name.as_ptr(), 0o700) };
    if result != 0 {
        let error = io::Error::last_os_error();
        if error.kind() != io::ErrorKind::AlreadyExists {
            return Err(error).with_context(|| {
                format!(
                    "Failed to create postgres backup directory {}",
                    display_path.display()
                )
            });
        }
    }
    let descriptor = unsafe {
        libc::openat(
            parent.as_raw_fd(),
            name.as_ptr(),
            libc::O_RDONLY | libc::O_DIRECTORY | libc::O_NOFOLLOW | libc::O_CLOEXEC,
        )
    };
    if descriptor < 0 {
        return Err(io::Error::last_os_error()).with_context(|| {
            format!(
                "Failed to open postgres backup directory without following symlinks: {}",
                display_path.display()
            )
        });
    }
    Ok(unsafe { File::from_raw_fd(descriptor) })
}

#[cfg(unix)]
fn set_private_directory_handle(directory: &File, display_path: &Path) -> Result<()> {
    use std::os::fd::AsRawFd;

    let result = unsafe { libc::fchmod(directory.as_raw_fd(), 0o700) };
    if result != 0 {
        return Err(io::Error::last_os_error()).with_context(|| {
            format!(
                "Failed to set private permissions on postgres backup directory {}",
                display_path.display()
            )
        });
    }
    Ok(())
}

fn parse_config(raw: &str) -> Result<SkillConfig> {
    let value: toml::Value = toml::from_str(raw).context("Failed to parse postgres config")?;
    let table = value
        .as_table()
        .ok_or_else(|| anyhow!("Postgres config must be a TOML table."))?;

    if table.contains_key("tools")
        || table.contains_key("defaults")
        || table.contains_key("schema_version")
    {
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

fn has_legacy_persisted_encoding(raw: &str) -> Result<bool> {
    let value: toml::Value = toml::from_str(raw).context("Failed to parse postgres config")?;
    let table = value
        .as_table()
        .ok_or_else(|| anyhow!("Postgres config must be a TOML table."))?;
    if !table.contains_key("tools")
        && !table.contains_key("defaults")
        && !table.contains_key("schema_version")
    {
        return Ok(true);
    }
    let Some(postgres) = value
        .get("tools")
        .and_then(|tools| tools.get("postgres"))
        .and_then(toml::Value::as_table)
    else {
        return Ok(false);
    };
    if table_has_legacy_option_encoding(postgres) {
        return Ok(true);
    }
    Ok(postgres
        .get("profiles")
        .and_then(toml::Value::as_table)
        .is_some_and(|profiles| {
            profiles.values().any(|profile| {
                profile
                    .as_table()
                    .is_some_and(table_has_legacy_option_encoding)
            })
        }))
}

fn table_has_legacy_option_encoding(table: &toml::Table) -> bool {
    if table.contains_key("sslmode") || table.contains_key("access") {
        return true;
    }
    let legacy_ssl_value = table.get("ssl_mode").is_some_and(|value| match value {
        toml::Value::String(value) => !matches!(value.as_str(), "disable" | "require"),
        _ => true,
    });
    let legacy_access_value = table
        .get("access_mode")
        .and_then(toml::Value::as_str)
        .is_some_and(|value| value == "read_write");
    legacy_ssl_value || legacy_access_value
}

fn should_save_loaded_config(
    canonical_path: &Path,
    read_path: &Path,
    original: &SkillConfig,
    migrated: &SkillConfig,
) -> bool {
    canonical_path != read_path || original != migrated
}

pub fn migrate_config_in_place(config: &mut SkillConfig) -> Result<()> {
    let schema_version = config.schema_version.clone().unwrap_or_default();
    if !schema_version.is_empty()
        && schema_version != "2.0.0"
        && schema_version != "2.1.0"
        && schema_version != LATEST_SCHEMA_VERSION
    {
        bail!("Unsupported schema_version: {schema_version}");
    }

    if config.defaults.profile.as_deref() == Some("") {
        config.defaults.profile = None;
    }

    normalize_ssl_modes(config);
    normalize_access_modes(config);
    config.schema_version = Some(LATEST_SCHEMA_VERSION.to_string());
    Ok(())
}

fn migrate_legacy_config(mut legacy: LegacySkillConfig) -> Result<SkillConfig> {
    let schema_version = legacy
        .configuration
        .schema_version
        .take()
        .unwrap_or_default();
    if !schema_version.is_empty()
        && schema_version != "1"
        && schema_version != "1.0.0"
        && schema_version != "1.1.0"
    {
        bail!("Unsupported schema_version: {schema_version}");
    }

    legacy.database.sslmode.get_or_insert_default();

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
                ssl_mode: legacy.database.sslmode,
                url: legacy.database.url,
                description: legacy.database.description,
                access_mode: legacy.database.access,
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

fn normalize_access_modes(config: &mut SkillConfig) {
    let shared_access = config
        .tools
        .postgres
        .access_mode
        .unwrap_or(AccessMode::ReadWrite);
    for profile in config.tools.postgres.profiles.values_mut() {
        profile.access_mode = Some(profile.access_mode.unwrap_or(shared_access));
    }
}

fn normalize_ssl_modes(config: &mut SkillConfig) {
    config.tools.postgres.ssl_mode.get_or_insert_default();
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
        let ssl_mode = profile.ssl_mode.or(tool.ssl_mode).unwrap_or_default();

        build_url(&host, port, &database, &user, &password, ssl_mode.as_str())?
    };

    let ssl_mode = profile.ssl_mode.or(tool.ssl_mode).unwrap_or_default();

    Ok(ResolvedProfile {
        name: name.to_string(),
        description: profile
            .description
            .clone()
            .or_else(|| tool.description.clone()),
        url,
        ssl_mode,
        access_mode: profile
            .access_mode
            .or(tool.access_mode)
            .unwrap_or(AccessMode::ReadWrite),
        migrations_path: profile
            .migrations_path
            .clone()
            .or_else(|| tool.migrations_path.clone()),
    })
}

pub fn update_ssl_mode(path: &Path, profile_name: &str, ssl_mode: SslMode) -> Result<()> {
    let mut config = load_and_migrate_config(path)?;
    let profile = config
        .tools
        .postgres
        .profiles
        .get_mut(profile_name)
        .ok_or_else(|| anyhow!("Profile '{profile_name}' not found in config.toml."))?;
    profile.ssl_mode = Some(ssl_mode);
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

pub fn ssl_mode_from_url(url: &str) -> Option<SslMode> {
    if let Ok(parsed) = Url::parse(url) {
        for (key, value) in parsed.query_pairs() {
            if key == "sslmode" {
                return parse_legacy_ssl_mode(&value).ok();
            }
        }
    }
    None
}

pub fn application_name() -> String {
    env::var("DB_APPLICATION_NAME").unwrap_or_else(|_| "codex-postgres-skill".to_string())
}

pub fn parse_ssl_mode(value: &str) -> Result<SslMode> {
    let lowered = value.trim().to_ascii_lowercase();
    match lowered.as_str() {
        "disable" => Ok(SslMode::Disable),
        "require" => Ok(SslMode::Require),
        _ => bail!("Invalid ssl_mode value '{value}'. Expected disable or require."),
    }
}

pub fn parse_legacy_ssl_mode(value: &str) -> Result<SslMode> {
    let lowered = value.trim().to_ascii_lowercase();
    match lowered.as_str() {
        "true" | "t" | "1" | "yes" | "y" | "on" | "enable" | "enabled" | "require" | "required"
        | "verify-ca" | "verify-full" => Ok(SslMode::Require),
        "false" | "f" | "0" | "no" | "n" | "off" | "disable" | "disabled" => Ok(SslMode::Disable),
        _ => bail!("Unrecognized legacy sslmode value: {value}"),
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
    let mut config =
        if path.exists() || sibling_legacy_config_path(path).is_some_and(|p| p.exists()) {
            if save {
                load_and_migrate_config(path)?
            } else {
                load_config(path)?
            }
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
    let ssl_mode = prompt("ssl_mode (disable/require)", Some("disable"), false)?;
    let description = prompt("Description", Some(""), false)?;
    let migrations_path = prompt("migrations_path", Some(""), false)?;

    let ssl_mode = parse_ssl_mode(&ssl_mode)?;
    let resolved = ResolvedProfile {
        name: profile_name.clone(),
        description: if description.is_empty() {
            None
        } else {
            Some(description.clone())
        },
        url: build_url(&host, port, &database, &user, &password, ssl_mode.as_str())?,
        ssl_mode,
        access_mode: AccessMode::ReadWrite,
        migrations_path: if migrations_path.is_empty() {
            None
        } else {
            Some(migrations_path.clone())
        },
    };

    if save {
        config.schema_version = Some(LATEST_SCHEMA_VERSION.to_string());
        config.defaults.profile = Some(profile_name.clone());
        if config.tools.postgres.ssl_mode.is_none() {
            config.tools.postgres.ssl_mode = Some(SslMode::Disable);
        }
        if config.tools.postgres.migrations_path.is_none() && !migrations_path.is_empty() {
            config.tools.postgres.migrations_path = Some(migrations_path.clone());
        }
        config.tools.postgres.profiles.insert(
            profile_name.clone(),
            ProfileConfig {
                description: resolved.description.clone(),
                access_mode: Some(resolved.access_mode),
                migrations_path: resolved.migrations_path.clone(),
                host: Some(host),
                port: Some(port),
                database: Some(database),
                user: Some(user),
                password: Some(password),
                ssl_mode: Some(ssl_mode),
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

    fn migrate_for_test(path: &Path, temp_root: &Path) -> Result<ConfigMigrationResult> {
        migrate_config_file_with_backup_root(path, Some(&temp_root.join("backups")))
    }

    fn load_and_migrate_for_test(path: &Path, temp_root: &Path) -> Result<SkillConfig> {
        Ok(migrate_for_test(path, temp_root)?.config)
    }

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
        let config = load_and_migrate_for_test(&canonical_path, temp.path()).unwrap();
        let written = fs::read_to_string(&canonical_path).unwrap();

        assert_eq!(
            config.schema_version.as_deref(),
            Some(LATEST_SCHEMA_VERSION)
        );
        assert_eq!(config.defaults.profile.as_deref(), Some("local"));
        assert_eq!(
            config.tools.postgres.migrations_path.as_deref(),
            Some("db/migrations")
        );
        assert_eq!(
            config.tools.postgres.profiles["local"].ssl_mode,
            Some(SslMode::Disable)
        );
        assert!(written.contains("schema_version = \"3.0.0\""));
        assert!(written.contains("access_mode = \"read-write\""));
        assert!(written.contains("ssl_mode = \"disable\""));
        assert!(!written.contains("sslmode ="));
        assert!(!written.contains("access ="));
        assert!(written.contains("[defaults]"));
        assert!(written.contains("[tools.postgres]"));
        assert!(written.contains("[tools.postgres.profiles.local]"));
        assert!(!written.contains("pg_bin_dir"));
        assert!(!written.contains("python_bin"));
    }

    #[test]
    fn load_config_reads_legacy_without_writing_canonical_config() {
        let temp = tempdir().unwrap();
        let project_root = temp.path();
        let legacy_path = legacy_config_path(project_root);
        let canonical_path = canonical_config_path(project_root);
        fs::create_dir_all(legacy_path.parent().unwrap()).unwrap();
        fs::write(
            &legacy_path,
            r#"[database.local]
database = "app"
user = "postgres"
password = "postgres"
"#,
        )
        .unwrap();

        let config = load_config(&canonical_path).unwrap();

        assert_eq!(
            config.schema_version.as_deref(),
            Some(LATEST_SCHEMA_VERSION)
        );
        assert_eq!(
            config.tools.postgres.profiles["local"].access_mode,
            Some(AccessMode::ReadWrite)
        );
        assert!(!canonical_path.exists());
        assert!(legacy_path.exists());
    }

    #[test]
    fn load_config_normalizes_missing_access_without_rewriting_canonical_config() {
        let temp = tempdir().unwrap();
        let canonical_path = canonical_config_path(temp.path());
        fs::create_dir_all(canonical_path.parent().unwrap()).unwrap();
        let original = r#"schema_version = "2.0.0"

[tools.postgres]
access = "read"

[tools.postgres.profiles.local]
database = "app"
user = "postgres"
password = "postgres"
"#;
        fs::write(&canonical_path, original).unwrap();

        let config = load_config(&canonical_path).unwrap();

        assert_eq!(
            config.tools.postgres.profiles["local"].access_mode,
            Some(AccessMode::Read)
        );
        assert_eq!(fs::read_to_string(&canonical_path).unwrap(), original);
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

        let config =
            load_and_migrate_for_test(&canonical_config_path(project_root), temp.path()).unwrap();
        assert_eq!(
            config.schema_version.as_deref(),
            Some(LATEST_SCHEMA_VERSION)
        );
        assert_eq!(config.tools.postgres.ssl_mode, Some(SslMode::Require));
        assert_eq!(
            config.tools.postgres.profiles["alpha"].ssl_mode,
            Some(SslMode::Require)
        );
        assert_eq!(
            config.tools.postgres.profiles["alpha"].access_mode,
            Some(AccessMode::ReadWrite)
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

        let config = load_and_migrate_for_test(&canonical_path, temp.path()).unwrap();
        assert_eq!(
            config.tools.postgres.profiles["local"].database.as_deref(),
            Some("canonical")
        );
    }

    #[test]
    fn update_ssl_mode_rewrites_canonical_config() {
        let temp = tempdir().unwrap();
        let canonical_path = canonical_config_path(temp.path());
        fs::create_dir_all(canonical_path.parent().unwrap()).unwrap();
        fs::write(
            &canonical_path,
            r#"schema_version = "3.0.0"

[defaults]
profile = "local"

[tools.postgres]
ssl_mode = "disable"

[tools.postgres.profiles.local]
database = "app"
user = "postgres"
password = "postgres"
ssl_mode = "disable"
"#,
        )
        .unwrap();

        update_ssl_mode(&canonical_path, "local", SslMode::Require).unwrap();
        let config = load_and_migrate_for_test(&canonical_path, temp.path()).unwrap();
        assert_eq!(
            config.tools.postgres.profiles["local"].ssl_mode,
            Some(SslMode::Require)
        );
    }

    #[test]
    fn migrates_v2_config_to_v3_clean_option_fields() {
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
"#,
        )
        .unwrap();

        let config = load_and_migrate_for_test(&canonical_path, temp.path()).unwrap();
        let written = fs::read_to_string(&canonical_path).unwrap();

        assert_eq!(config.schema_version.as_deref(), Some("3.0.0"));
        assert_eq!(
            config.tools.postgres.profiles["local"].access_mode,
            Some(AccessMode::ReadWrite)
        );
        assert!(written.contains("schema_version = \"3.0.0\""));
        assert!(written.contains("access_mode = \"read-write\""));
        assert!(written.contains("ssl_mode = \"disable\""));
        assert!(!written.contains("sslmode ="));
        assert!(!written.contains("access ="));
    }

    #[test]
    fn shared_access_is_copied_to_profiles_missing_access() {
        let temp = tempdir().unwrap();
        let canonical_path = canonical_config_path(temp.path());
        fs::create_dir_all(canonical_path.parent().unwrap()).unwrap();
        fs::write(
            &canonical_path,
            r#"schema_version = "2.0.0"

[tools.postgres]
sslmode = false
access = "read"

[tools.postgres.profiles.local]
database = "app"
user = "postgres"
password = "postgres"

[tools.postgres.profiles.writer]
access = "write"
database = "app"
user = "postgres"
password = "postgres"
"#,
        )
        .unwrap();

        let config = load_and_migrate_for_test(&canonical_path, temp.path()).unwrap();

        assert_eq!(
            config.tools.postgres.profiles["local"].access_mode,
            Some(AccessMode::Read)
        );
        assert_eq!(
            config.tools.postgres.profiles["writer"].access_mode,
            Some(AccessMode::Write)
        );
    }

    #[test]
    fn invalid_access_value_fails_clearly() {
        let temp = tempdir().unwrap();
        let canonical_path = canonical_config_path(temp.path());
        fs::create_dir_all(canonical_path.parent().unwrap()).unwrap();
        fs::write(
            &canonical_path,
            r#"schema_version = "3.0.0"

[tools.postgres.profiles.local]
access_mode = "admin"
database = "app"
user = "postgres"
password = "postgres"
"#,
        )
        .unwrap();

        let error = load_and_migrate_config(&canonical_path).unwrap_err();
        let message = format!("{error:#}");
        assert!(message.contains("Failed to decode config.toml"));
        assert!(message.contains("admin"));
    }

    #[test]
    fn builds_url() {
        let url = build_url("localhost", 5432, "db", "user", "pw", "disable").unwrap();
        assert!(url.contains("sslmode=disable"));
        assert!(url.contains("localhost"));
    }

    #[test]
    fn save_decision_only_writes_for_migration_or_normalization() {
        let path = Path::new("/tmp/config.toml");
        let same_path = Path::new("/tmp/config.toml");
        let legacy_path = Path::new("/tmp/postgres.toml");

        let mut original = SkillConfig::default();
        original.schema_version = Some(LATEST_SCHEMA_VERSION.to_string());
        let migrated = original.clone();

        assert!(!should_save_loaded_config(
            path, same_path, &original, &migrated
        ));
        assert!(should_save_loaded_config(
            path,
            legacy_path,
            &original,
            &migrated
        ));

        let mut normalized = migrated.clone();
        normalized.defaults.profile = Some("local".to_string());
        assert!(should_save_loaded_config(
            path,
            same_path,
            &original,
            &normalized
        ));
    }

    #[test]
    fn explicit_migration_creates_one_backup_and_is_idempotent() {
        let temp = tempdir().unwrap();
        let canonical_path = canonical_config_path(temp.path());
        fs::create_dir_all(canonical_path.parent().unwrap()).unwrap();
        let original = r#"schema_version = "2.1.0"

[tools.postgres]
sslmode = false
access = "read_write"

[tools.postgres.profiles.local]
database = "app"
user = "postgres"
password = "postgres"
"#;
        fs::write(&canonical_path, original).unwrap();

        let first = migrate_for_test(&canonical_path, temp.path()).unwrap();
        let backup_path = first.backup_path.expect("migration backup");
        assert_eq!(first.migration_outcome, "migrated");
        assert_eq!(fs::read_to_string(&backup_path).unwrap(), original);
        assert!(
            backup_path.starts_with(resolve_for_containment(&temp.path().join("backups")).unwrap())
        );
        assert!(!PathBuf::from(format!("{}.bak", canonical_path.display())).exists());
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            assert_eq!(
                fs::metadata(&backup_path).unwrap().permissions().mode() & 0o777,
                0o600
            );
            assert_eq!(
                fs::metadata(backup_path.parent().unwrap())
                    .unwrap()
                    .permissions()
                    .mode()
                    & 0o777,
                0o700
            );
        }

        let canonical = fs::read_to_string(&canonical_path).unwrap();
        assert!(canonical.contains("schema_version = \"3.0.0\""));
        assert!(canonical.contains("ssl_mode = \"disable\""));
        assert!(canonical.contains("access_mode = \"read-write\""));

        let second = migrate_for_test(&canonical_path, temp.path()).unwrap();
        assert_eq!(second.migration_outcome, "no-change");
        assert_eq!(second.backup_path, None);
        assert!(!PathBuf::from(format!("{}.1", backup_path.display())).exists());
        assert_eq!(fs::read_to_string(&canonical_path).unwrap(), canonical);
    }

    #[test]
    fn backup_root_ignores_relative_and_project_local_cache_candidates() {
        let project = tempdir().unwrap();
        let safe_home = tempdir().unwrap();
        let config_path = canonical_config_path(project.path());
        let expected = resolve_for_containment(
            &safe_home
                .path()
                .join(".cache/dotagents/skills/postgres/config-backups"),
        )
        .unwrap();

        let relative = select_config_backup_root(
            &config_path,
            Some(PathBuf::from(".cache")),
            Some(safe_home.path().to_path_buf()),
        )
        .unwrap();
        assert_eq!(relative, expected);

        let project_local = select_config_backup_root(
            &config_path,
            Some(project.path().join(".cache")),
            Some(safe_home.path().to_path_buf()),
        )
        .unwrap();
        assert_eq!(project_local, expected);
    }

    #[test]
    fn backup_root_ignores_cache_candidates_with_parent_traversal() {
        let project = tempdir().unwrap();
        let safe_home = tempdir().unwrap();
        let config_path = canonical_config_path(project.path());
        let deceptive_cache = project
            .path()
            .parent()
            .unwrap()
            .join("missing-cache-parent")
            .join("..")
            .join(project.path().file_name().unwrap())
            .join(".cache");

        let selected = select_config_backup_root(
            &config_path,
            Some(deceptive_cache),
            Some(safe_home.path().to_path_buf()),
        )
        .unwrap();

        assert_eq!(
            selected,
            resolve_for_containment(
                &safe_home
                    .path()
                    .join(".cache/dotagents/skills/postgres/config-backups")
            )
            .unwrap()
        );
    }

    #[test]
    fn backup_root_fails_when_every_candidate_is_project_local() {
        let project = tempdir().unwrap();
        let config_path = canonical_config_path(project.path());

        let error = select_config_backup_root(
            &config_path,
            Some(project.path().join("cache")),
            Some(project.path().to_path_buf()),
        )
        .unwrap_err();

        assert!(format!("{error:#}").contains("outside the consuming project"));
    }

    #[cfg(unix)]
    #[test]
    fn backup_root_rejects_symlink_resolving_inside_project() {
        use std::os::unix::fs::symlink;

        let project = tempdir().unwrap();
        let safe_home = tempdir().unwrap();
        let link_root = tempdir().unwrap();
        let project_cache = project.path().join("cache");
        fs::create_dir_all(&project_cache).unwrap();
        let cache_link = link_root.path().join("cache-link");
        symlink(&project_cache, &cache_link).unwrap();
        let config_path = canonical_config_path(project.path());

        let selected = select_config_backup_root(
            &config_path,
            Some(cache_link),
            Some(safe_home.path().to_path_buf()),
        )
        .unwrap();

        assert_eq!(
            selected,
            resolve_for_containment(
                &safe_home
                    .path()
                    .join(".cache/dotagents/skills/postgres/config-backups")
            )
            .unwrap()
        );
    }

    #[cfg(unix)]
    #[test]
    fn backup_creation_skips_existing_symlink_without_touching_its_target() {
        use std::os::unix::fs::symlink;

        let temp = tempdir().unwrap();
        let canonical_path = canonical_config_path(temp.path());
        fs::create_dir_all(canonical_path.parent().unwrap()).unwrap();
        fs::write(&canonical_path, "source").unwrap();
        let backup_root = temp.path().join("backups");
        let backup_directory = backup_root.join(backup_source_key(&canonical_path));
        fs::create_dir_all(&backup_directory).unwrap();
        let victim = temp.path().join("victim");
        fs::write(&victim, "untouched").unwrap();
        symlink(&victim, backup_directory.join("config.toml.bak")).unwrap();

        let backup = write_config_backup(&canonical_path, &backup_root, b"original").unwrap();

        assert_eq!(backup.file_name().unwrap(), "config.toml.bak.1");
        assert_eq!(fs::read_to_string(victim).unwrap(), "untouched");
        assert_eq!(fs::read_to_string(backup).unwrap(), "original");
    }

    #[cfg(unix)]
    #[test]
    fn backup_creation_rejects_symlinked_source_key_directory() {
        use std::os::unix::fs::symlink;

        let temp = tempdir().unwrap();
        let canonical_path = canonical_config_path(temp.path());
        fs::create_dir_all(canonical_path.parent().unwrap()).unwrap();
        fs::write(&canonical_path, "source").unwrap();
        let backup_root = temp.path().join("backups");
        fs::create_dir_all(&backup_root).unwrap();
        let victim = temp.path().join("victim");
        fs::create_dir_all(&victim).unwrap();
        symlink(
            &victim,
            backup_root.join(backup_source_key(&canonical_path)),
        )
        .unwrap();

        let error = write_config_backup(&canonical_path, &backup_root, b"original").unwrap_err();

        assert!(format!("{error:#}").contains("without following symlinks"));
        assert!(!victim.join("config.toml.bak").exists());
    }

    #[test]
    fn explicit_migration_normalizes_legacy_keys_even_with_v3_version() {
        let temp = tempdir().unwrap();
        let canonical_path = canonical_config_path(temp.path());
        fs::create_dir_all(canonical_path.parent().unwrap()).unwrap();
        fs::write(
            &canonical_path,
            r#"schema_version = "3.0.0"

[tools.postgres]
sslmode = false

[tools.postgres.profiles.local]
access = "read_write"
database = "app"
user = "postgres"
password = "postgres"
"#,
        )
        .unwrap();

        let result = migrate_for_test(&canonical_path, temp.path()).unwrap();
        assert_eq!(result.migration_outcome, "migrated");
        assert!(result.backup_path.is_some());
        let canonical = fs::read_to_string(&canonical_path).unwrap();
        assert!(canonical.contains("ssl_mode = \"disable\""));
        assert!(canonical.contains("access_mode = \"read-write\""));
        assert!(!canonical.contains("sslmode ="));
        assert!(!canonical.contains("access ="));
    }

    #[test]
    fn explicit_migration_rewrites_legacy_layout_at_canonical_path() {
        let temp = tempdir().unwrap();
        let canonical_path = canonical_config_path(temp.path());
        fs::create_dir_all(canonical_path.parent().unwrap()).unwrap();
        let original = r#"[configuration]
schema_version = "1.1.0"

[database.local]
database = "app"
user = "postgres"
password = "postgres"
sslmode = "disable"
"#;
        fs::write(&canonical_path, original).unwrap();

        let first = migrate_for_test(&canonical_path, temp.path()).unwrap();
        assert_eq!(first.migration_outcome, "migrated");
        let backup_path = first.backup_path.expect("legacy-layout backup");
        assert_eq!(fs::read_to_string(backup_path).unwrap(), original);
        let canonical = fs::read_to_string(&canonical_path).unwrap();
        assert!(canonical.contains("schema_version = \"3.0.0\""));
        assert!(canonical.contains("[tools.postgres.profiles.local]"));
        assert!(canonical.contains("ssl_mode = \"disable\""));
        assert!(canonical.contains("access_mode = \"read-write\""));
        assert!(!canonical.contains("[configuration]"));
        assert!(!canonical.contains("[database.local]"));

        let second = migrate_for_test(&canonical_path, temp.path()).unwrap();
        assert_eq!(second.migration_outcome, "no-change");
        assert_eq!(second.backup_path, None);
    }

    #[test]
    fn explicit_migration_normalizes_legacy_values_under_v3_keys() {
        let temp = tempdir().unwrap();
        let canonical_path = canonical_config_path(temp.path());
        fs::create_dir_all(canonical_path.parent().unwrap()).unwrap();
        fs::write(
            &canonical_path,
            r#"schema_version = "3.0.0"

[tools.postgres]
ssl_mode = true

[tools.postgres.profiles.local]
access_mode = "read_write"
database = "app"
user = "postgres"
password = "postgres"
"#,
        )
        .unwrap();

        let result = migrate_for_test(&canonical_path, temp.path()).unwrap();
        assert_eq!(result.migration_outcome, "migrated");
        let canonical = fs::read_to_string(&canonical_path).unwrap();
        assert!(canonical.contains("ssl_mode = \"require\""));
        assert!(canonical.contains("access_mode = \"read-write\""));
        assert!(!canonical.contains("ssl_mode = true"));
        assert!(!canonical.contains("read_write"));
    }

    #[test]
    fn future_schema_fails_without_backup_or_rewrite() {
        let temp = tempdir().unwrap();
        let canonical_path = canonical_config_path(temp.path());
        fs::create_dir_all(canonical_path.parent().unwrap()).unwrap();
        let original = r#"schema_version = "99.0.0"

[tools.postgres.profiles.local]
database = "app"
user = "postgres"
password = "postgres"
"#;
        fs::write(&canonical_path, original).unwrap();

        let error = migrate_for_test(&canonical_path, temp.path()).unwrap_err();
        assert!(format!("{error:#}").contains("Unsupported schema_version: 99.0.0"));
        assert_eq!(fs::read_to_string(&canonical_path).unwrap(), original);
        assert!(!temp.path().join("backups").exists());
    }

    #[test]
    fn canonical_ssl_mode_parser_rejects_legacy_boolean_phrases() {
        assert_eq!(parse_ssl_mode("disable").unwrap(), SslMode::Disable);
        assert_eq!(parse_ssl_mode("require").unwrap(), SslMode::Require);
        assert!(parse_ssl_mode("true").is_err());
        assert_eq!(parse_legacy_ssl_mode("true").unwrap(), SslMode::Require);
    }

    #[test]
    fn runtime_json_redacts_connection_passwords() {
        let context = RuntimeContext {
            project_root: None,
            config_path: None,
            toml_path: None,
            profile_name: "local".to_string(),
            url: "postgresql://postgres:secret@localhost:5432/app?sslmode=disable".to_string(),
            ssl_mode: SslMode::Disable,
            access_mode: AccessMode::ReadWrite,
            url_source: "config".to_string(),
            application_name: "codex-postgres-skill".to_string(),
        };

        let serialized = serde_json::to_string(&context).unwrap();
        assert!(!serialized.contains("secret"));
        assert!(serialized.contains("***"));
    }

    #[test]
    fn connection_url_redaction_masks_credential_query_parameters() {
        let redacted = redact_connection_url(
            "postgresql://postgres@localhost/app?password=secret&sslpassword=tls-secret&sslmode=require",
        );

        assert!(!redacted.contains("secret"));
        assert!(redacted.contains("password=***"));
        assert!(redacted.contains("sslpassword=***"));
        assert!(redacted.contains("sslmode=require"));
    }
}
