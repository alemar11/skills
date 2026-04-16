use crate::config::RuntimeContext;
use anyhow::{Result, bail};
use postgresql_embedded::{PostgreSQL, SettingsBuilder, VersionReq};
use serde::Serialize;
use std::env;
use std::path::{Path, PathBuf};

#[derive(Debug, Clone, Serialize)]
pub struct ToolingStatus {
    pub source: String,
    pub binary_dir: Option<PathBuf>,
    pub pg_dump: bool,
    pub pg_restore: bool,
}

#[derive(Debug, Clone)]
pub enum ToolBackend {
    Local { binary_dir: Option<PathBuf> },
    Managed { binary_dir: PathBuf },
}

impl ToolBackend {
    pub fn binary_dir(&self) -> Option<PathBuf> {
        match self {
            ToolBackend::Local { binary_dir } => binary_dir.clone(),
            ToolBackend::Managed { binary_dir } => Some(binary_dir.clone()),
        }
    }

    pub fn status(&self) -> ToolingStatus {
        match self {
            ToolBackend::Local { binary_dir } => ToolingStatus {
                source: "local".to_string(),
                binary_dir: binary_dir.clone(),
                pg_dump: true,
                pg_restore: true,
            },
            ToolBackend::Managed { binary_dir } => ToolingStatus {
                source: "managed".to_string(),
                binary_dir: Some(binary_dir.clone()),
                pg_dump: true,
                pg_restore: true,
            },
        }
    }
}

pub async fn ensure_backend(ctx: &RuntimeContext, skill_root: &Path) -> Result<ToolBackend> {
    if let Ok(binary_dir) = resolve_local_binary_dir(ctx) {
        return Ok(ToolBackend::Local { binary_dir });
    }
    let binary_dir = ensure_managed_binary_dir(skill_root).await?;
    Ok(ToolBackend::Managed { binary_dir })
}

fn resolve_local_binary_dir(ctx: &RuntimeContext) -> Result<Option<PathBuf>> {
    if let Some(path) = find_command("pg_dump") {
        return Ok(path.parent().map(Path::to_path_buf));
    }

    if let Some(toml_path) = &ctx.toml_path {
        let content = std::fs::read_to_string(toml_path)?;
        let value: toml::Value = toml::from_str(&content)?;
        if let Some(dir) = value
            .get("configuration")
            .and_then(|table| table.get("pg_bin_dir"))
            .and_then(|value| value.as_str())
        {
            let path = PathBuf::from(dir);
            if path.join("pg_dump").exists() && path.join("pg_restore").exists() {
                return Ok(Some(path));
            }
        }
    }

    bail!("Local PostgreSQL client tools not found.")
}

async fn ensure_managed_binary_dir(skill_root: &Path) -> Result<PathBuf> {
    let install_root = env::var("DB_MANAGED_PG_DIR")
        .map(PathBuf::from)
        .unwrap_or_else(|_| skill_root.join(".managed-postgresql"));
    let settings = SettingsBuilder::new()
        .installation_dir(install_root)
        .version(VersionReq::parse("=16").expect("valid version"))
        .temporary(true)
        .timeout(Some(std::time::Duration::from_secs(30)))
        .build();
    let mut postgres = PostgreSQL::new(settings);
    postgres.setup().await?;
    Ok(postgres.settings().binary_dir())
}

fn find_command(name: &str) -> Option<PathBuf> {
    let path = env::var_os("PATH")?;
    env::split_paths(&path).find_map(|entry| {
        let candidate = entry.join(name);
        if candidate.exists() {
            Some(candidate)
        } else {
            None
        }
    })
}
