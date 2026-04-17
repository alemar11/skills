use crate::cli::MigrationReleaseArgs;
use crate::config::{RuntimeContext, load_and_migrate_config};
use anyhow::{Context, Result, anyhow, bail};
use chrono::{Datelike, Timelike};
use serde::Serialize;
use std::fs;
use std::path::{Path, PathBuf};

#[derive(Debug, Clone, Serialize)]
pub struct ReleasePlan {
    pub project_root: PathBuf,
    pub profile: String,
    pub migrations_path: PathBuf,
    pub pending_path: PathBuf,
    pub release_target: PathBuf,
    pub changelog_path: PathBuf,
    pub summary: String,
    pub dry_run: bool,
}

pub fn build_release_plan(
    ctx: &RuntimeContext,
    args: &MigrationReleaseArgs,
) -> Result<ReleasePlan> {
    let project_root = ctx
        .project_root
        .clone()
        .ok_or_else(|| anyhow!("Project root is required for migration release."))?;
    let config_path = ctx
        .config_path
        .clone()
        .ok_or_else(|| anyhow!("config.toml is required for migration release."))?;
    let config = load_and_migrate_config(&config_path)?;
    let profile = ctx.profile_name.clone();
    let postgres = &config.tools.postgres;

    let migrations_path = if let Some(path) = args.migrations_path.clone() {
        absolutize(&project_root, &path)
    } else if let Some(profile_cfg) = postgres.profiles.get(&profile) {
        profile_cfg
            .migrations_path
            .as_ref()
            .map(|value| absolutize(&project_root, &PathBuf::from(value)))
            .or_else(|| postgres.migrations_path.as_ref().map(|value| absolutize(&project_root, &PathBuf::from(value))))
            .unwrap_or_else(|| project_root.join("db/migrations"))
    } else {
        project_root.join("db/migrations")
    };

    let released_dir = migrations_path.join("released");
    let pending_path = migrations_path.join(&args.pending_file);
    let changelog_path = migrations_path.join("CHANGELOG.md");
    if !pending_path.exists() {
        bail!(
            "Pending migration file not found: {}",
            pending_path.display()
        );
    }
    if fs::read_to_string(&pending_path)
        .with_context(|| format!("Failed to read {}", pending_path.display()))?
        .trim()
        .is_empty()
    {
        bail!(
            "Pending migration file is empty: {}",
            pending_path.display()
        );
    }

    let timestamp = args.timestamp.clone().unwrap_or_else(now_timestamp);
    if timestamp.len() != 14 || !timestamp.chars().all(|value| value.is_ascii_digit()) {
        bail!("--timestamp must use YYYYMMDDHHMMSS.");
    }

    let slug = sanitize_slug(
        args.slug
            .clone()
            .unwrap_or_else(|| {
                project_root
                    .file_name()
                    .unwrap_or_default()
                    .to_string_lossy()
                    .to_string()
            })
            .as_str(),
    );
    let release_target = next_release_target(&released_dir, &timestamp, &slug);
    let summary = args
        .summary
        .clone()
        .unwrap_or_else(|| derive_summary(&changelog_path, &args.pending_file));

    Ok(ReleasePlan {
        project_root,
        profile,
        migrations_path,
        pending_path,
        release_target,
        changelog_path,
        summary,
        dry_run: args.dry_run,
    })
}

pub fn apply_release(plan: &ReleasePlan, pending_file: &str) -> Result<()> {
    fs::create_dir_all(plan.release_target.parent().expect("release parent"))?;
    fs::rename(&plan.pending_path, &plan.release_target).with_context(|| {
        format!(
            "Failed to move {} to {}",
            plan.pending_path.display(),
            plan.release_target.display()
        )
    })?;
    fs::write(&plan.pending_path, "").with_context(|| {
        format!(
            "Failed to recreate pending migration file {}",
            plan.pending_path.display()
        )
    })?;
    let updated_changelog = update_changelog(
        &plan.changelog_path,
        pending_file,
        &plan.release_target,
        &plan.summary,
    )?;
    fs::write(&plan.changelog_path, updated_changelog)
        .with_context(|| format!("Failed to write {}", plan.changelog_path.display()))?;
    Ok(())
}

pub fn update_changelog(
    changelog_path: &Path,
    pending_file: &str,
    release_target: &Path,
    summary: &str,
) -> Result<String> {
    let existing = if changelog_path.exists() {
        fs::read_to_string(changelog_path)?
    } else {
        String::new()
    };
    if !existing.trim().is_empty()
        && (!existing.contains("## WIP") || !existing.contains("## RELEASED"))
    {
        bail!("CHANGELOG.md must use top-level ## WIP and ## RELEASED sections before release.");
    }

    let date = release_target
        .file_stem()
        .and_then(|stem| stem.to_string_lossy().get(0..8).map(str::to_string))
        .unwrap_or_else(|| "00000000".to_string());
    let release_heading = format!(
        "### {}-{}-{} — `{}`",
        &date[0..4],
        &date[4..6],
        &date[6..8],
        release_target
            .file_name()
            .unwrap_or_default()
            .to_string_lossy()
    );

    let mut wip_lines = Vec::new();
    let mut released_lines = Vec::new();
    let mut section = "";
    let mut skipping_pending = false;
    for line in existing.lines() {
        match line {
            "## WIP" => {
                section = "WIP";
                wip_lines.push(line.to_string());
                continue;
            }
            "## RELEASED" => {
                section = "RELEASED";
                released_lines.push(line.to_string());
                continue;
            }
            _ => {}
        }

        if section == "WIP" {
            if line.starts_with("### ") {
                skipping_pending = line.trim() == format!("### {pending_file}");
            }
            if !skipping_pending {
                wip_lines.push(line.to_string());
            }
        } else if section == "RELEASED" {
            released_lines.push(line.to_string());
        }
    }

    if wip_lines.is_empty() {
        wip_lines.push("## WIP".to_string());
    }
    if released_lines.is_empty() {
        released_lines.push("## RELEASED".to_string());
    }

    let mut output = Vec::new();
    output.extend(wip_lines);
    if output.last().map(|line| !line.is_empty()).unwrap_or(true) {
        output.push(String::new());
    }
    output.push("## RELEASED".to_string());
    output.push(String::new());
    output.push(release_heading);
    output.push(format!("- {}", summary.trim()));
    output.push(String::new());
    for line in released_lines.into_iter().skip(1) {
        output.push(line);
    }

    Ok(output.join("\n").trim().to_string() + "\n")
}

fn absolutize(project_root: &Path, path: &Path) -> PathBuf {
    if path.is_absolute() {
        path.to_path_buf()
    } else {
        project_root.join(path)
    }
}

fn sanitize_slug(raw: &str) -> String {
    let cleaned = raw
        .chars()
        .map(|value| {
            if value.is_ascii_alphanumeric() {
                value.to_ascii_lowercase()
            } else {
                '_'
            }
        })
        .collect::<String>();
    cleaned.trim_matches('_').to_string()
}

fn next_release_target(released_dir: &Path, timestamp: &str, slug: &str) -> PathBuf {
    let base = released_dir.join(format!("{timestamp}.sql"));
    if !base.exists() {
        return base;
    }
    let mut counter = 1;
    loop {
        let candidate = if counter == 1 {
            released_dir.join(format!("{timestamp}_{slug}.sql"))
        } else {
            released_dir.join(format!("{timestamp}_{slug}_{counter:02}.sql"))
        };
        if !candidate.exists() {
            return candidate;
        }
        counter += 1;
    }
}

fn now_timestamp() -> String {
    use std::time::{SystemTime, UNIX_EPOCH};
    let now = chrono_like(
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs() as i64,
    );
    format!(
        "{:04}{:02}{:02}{:02}{:02}{:02}",
        now.0, now.1, now.2, now.3, now.4, now.5
    )
}

fn chrono_like(timestamp: i64) -> (i32, u32, u32, u32, u32, u32) {
    use std::time::{Duration, UNIX_EPOCH};
    let system_time = UNIX_EPOCH + Duration::from_secs(timestamp as u64);
    let datetime: chrono::DateTime<chrono::Utc> = system_time.into();
    (
        datetime.year(),
        datetime.month(),
        datetime.day(),
        datetime.hour(),
        datetime.minute(),
        datetime.second(),
    )
}

fn derive_summary(changelog_path: &Path, pending_file: &str) -> String {
    let Ok(content) = fs::read_to_string(changelog_path) else {
        return format!("Release {pending_file}.");
    };
    let mut in_wip = false;
    let mut in_pending = false;
    for line in content.lines() {
        if line.starts_with("## ") {
            in_wip = line.trim() == "## WIP";
            in_pending = false;
            continue;
        }
        if !in_wip {
            continue;
        }
        if line.starts_with("### ") {
            in_pending = line.trim() == format!("### {pending_file}");
            continue;
        }
        if in_pending && line.trim_start().starts_with("- ") {
            return line.trim_start()[2..].trim().to_string();
        }
    }
    format!("Release {pending_file}.")
}

#[cfg(test)]
mod tests {
    use super::*;
    use pretty_assertions::assert_eq;

    #[test]
    fn updates_changelog() {
        let temp = tempfile::tempdir().unwrap();
        let changelog = temp.path().join("CHANGELOG.md");
        fs::write(
            &changelog,
            "## WIP\n\n### prerelease.sql\n- Pending change\n\n## RELEASED\n\n",
        )
        .unwrap();
        let release = temp.path().join("released/20260416120000.sql");
        let updated =
            update_changelog(&changelog, "prerelease.sql", &release, "Pending change").unwrap();
        assert!(updated.contains("## WIP"));
        assert!(updated.contains("## RELEASED"));
        assert!(updated.contains("Pending change"));
        assert!(!updated.contains("### prerelease.sql"));
    }

    #[test]
    fn derives_summary_from_pending_section() {
        let temp = tempfile::tempdir().unwrap();
        let changelog = temp.path().join("CHANGELOG.md");
        fs::write(
            &changelog,
            "## WIP\n\n### prerelease.sql\n- Add table\n\n## RELEASED\n\n",
        )
        .unwrap();
        assert_eq!(derive_summary(&changelog, "prerelease.sql"), "Add table");
    }
}
