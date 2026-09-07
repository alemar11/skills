use std::fs;
use std::process::{Command, Output};
use tempfile::{TempDir, tempdir};

fn fixture() -> TempDir {
    let root = tempdir().unwrap();
    let config = root.path().join(".skills/postgres/config.toml");
    fs::create_dir_all(config.parent().unwrap()).unwrap();
    fs::write(
        config,
        "schema_version = \"3.0.0\"\n\
         [tools.postgres.profiles.local]\n\
         url = \"postgresql://fixture:fixture@127.0.0.1:1/fixture\"\n\
         access_mode = \"read-write\"\n",
    )
    .unwrap();
    root
}

fn cli(root: &TempDir) -> Command {
    let executable = std::env::var_os("POSTGRES_TEST_CLI")
        .unwrap_or_else(|| env!("CARGO_BIN_EXE_postgres").into());
    let mut command = Command::new(executable);
    command.env_clear().args(["--json", "--project-root"]);
    command.arg(root.path());
    command
}

fn error_message(output: &Output) -> String {
    assert!(!output.status.success(), "{output:?}");
    let json: serde_json::Value = serde_json::from_slice(&output.stdout).unwrap();
    json["error"]["message"].as_str().unwrap().to_string()
}

#[test]
fn entrypoint_supports_help_version_and_offline_doctor() {
    let root = fixture();
    let output = cli(&root).arg("--help").output().unwrap();
    assert!(output.status.success(), "{output:?}");
    assert!(String::from_utf8_lossy(&output.stdout).contains("Usage: postgres"));
    let output = cli(&root).arg("--version").output().unwrap();
    assert!(output.status.success(), "{output:?}");
    assert!(String::from_utf8_lossy(&output.stdout).contains(env!("CARGO_PKG_VERSION")));
    let output = cli(&root).arg("doctor").output().unwrap();
    assert!(output.status.success(), "{output:?}");
    let json: serde_json::Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(json["runtime"]["profile_name"], "local");
    assert_eq!(json["runtime"]["url_source"], "config");
}

#[test]
fn invalid_environment_connection_does_not_fall_back_to_saved_profile() {
    let root = fixture();
    let mut command = cli(&root);
    command.envs([
        ("PGHOST", "127.0.0.1"),
        ("PGPORT", "invalid"),
        ("PGDATABASE", "requested_database"),
        ("PGUSER", "fixture"),
        ("PGPASSWORD", "fixture"),
    ]);
    command.args(["profile", "resolve"]);
    let output = command.output().unwrap();
    assert!(error_message(&output).contains("Invalid PGPORT value"));

    // An explicit URL still has precedence over the malformed environment.
    let output = command
        .args(["--url", "postgresql://fixture:fixture@127.0.0.1:1/explicit"])
        .output()
        .unwrap();
    assert!(output.status.success(), "{output:?}");
    let json: serde_json::Value = serde_json::from_slice(&output.stdout).unwrap();
    assert!(json["url"].as_str().unwrap().ends_with("/explicit"));
}

#[test]
fn invalid_changelog_leaves_migration_files_untouched_including_dry_run() {
    let root = fixture();
    let migrations = root.path().join("db/migrations");
    fs::create_dir_all(&migrations).unwrap();
    let pending = migrations.join("prerelease.sql");
    let changelog = migrations.join("CHANGELOG.md");
    fs::write(&pending, "SELECT 1;\n").unwrap();

    for content in ["# Invalid changelog\n", "### WIP\n### RELEASED\n"] {
        fs::write(&changelog, content).unwrap();
        for dry_run in [true, false] {
            let mut command = cli(&root);
            command.args(["migration", "release", "--timestamp", "20260907120000"]);
            if dry_run {
                command.arg("--dry-run");
            }
            let output = command.output().unwrap();
            assert!(error_message(&output).contains("## WIP and ## RELEASED"));
            assert_eq!(fs::read_to_string(&pending).unwrap(), "SELECT 1;\n");
            assert_eq!(fs::read_to_string(&changelog).unwrap(), content);
            assert!(!migrations.join("released").exists());
        }
    }
}

#[test]
fn valid_release_preserves_sql_and_updates_changelog() {
    let root = fixture();
    let migrations = root.path().join("db/migrations");
    fs::create_dir_all(&migrations).unwrap();
    let pending = migrations.join("prerelease.sql");
    let changelog = migrations.join("CHANGELOG.md");
    fs::write(&pending, "SELECT 1;\n").unwrap();
    let original = "## WIP\n\n### prerelease.sql\n- Example change\n\n## RELEASED\n";
    fs::write(&changelog, original).unwrap();
    let mut command = cli(&root);
    command.args(["migration", "release", "--timestamp", "20260907120000"]);
    let output = command.arg("--dry-run").output().unwrap();
    assert!(output.status.success(), "{output:?}");
    assert_eq!(fs::read_to_string(&pending).unwrap(), "SELECT 1;\n");
    assert_eq!(fs::read_to_string(&changelog).unwrap(), original);
    assert!(!migrations.join("released").exists());

    let output = cli(&root)
        .args(["migration", "release", "--timestamp", "20260907120000"])
        .output()
        .unwrap();
    assert!(output.status.success(), "{output:?}");
    assert_eq!(fs::read_to_string(&pending).unwrap(), "");
    assert_eq!(
        fs::read_to_string(migrations.join("released/20260907120000.sql")).unwrap(),
        "SELECT 1;\n"
    );
    let updated = fs::read_to_string(&changelog).unwrap();
    assert!(updated.contains("20260907120000.sql"));
    assert!(updated.contains("- Example change"));
    assert!(!updated.contains("### prerelease.sql"));
}
