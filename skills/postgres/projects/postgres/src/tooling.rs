use crate::config::RuntimeContext;
use anyhow::Result;
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
pub struct ToolBackend {
    binary_dir: PathBuf,
}

impl ToolBackend {
    pub fn binary_dir(&self) -> PathBuf {
        self.binary_dir.clone()
    }

    pub fn status(&self) -> ToolingStatus {
        ToolingStatus {
            source: "managed".to_string(),
            binary_dir: Some(self.binary_dir()),
            pg_dump: true,
            pg_restore: true,
        }
    }
}

pub async fn ensure_backend(_ctx: &RuntimeContext, skill_root: &Path) -> Result<ToolBackend> {
    let binary_dir = ensure_managed_binary_dir(skill_root).await?;
    Ok(ToolBackend { binary_dir })
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
