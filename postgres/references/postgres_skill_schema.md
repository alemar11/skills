# Postgres Skill Config Schema

Config file:

```text
<project-root>/.skills/postgres/postgres.toml
```

Current schema version: `1.1.0`

## Shape

```toml
[configuration]
schema_version = "1.1.0"
pg_bin_dir = "/optional/local/postgres/bin"
python_bin = ""

[database]
sslmode = false

[database.local]
description = "Local development DB"
host = "127.0.0.1"
port = 5432
database = "app"
user = "postgres"
password = "postgres"
sslmode = false
migrations_path = "db/migrations"

[migrations]
path = "db/migrations"
```

## Notes

- `schema_version` is required and normalizes to `1.1.0`.
- `pg_bin_dir` is optional. If present, it points at a local PostgreSQL binary
  directory and is used before managed-tools fallback.
- `python_bin` is retained for compatibility with older configs but is no
  longer required by the Rust runtime.
- `[database]` stores defaults shared by profiles.
- `[database.<profile>]` stores per-profile overrides.
- `sslmode` must be boolean in TOML (`true` / `false`), not a string.
- `url` may be used in a profile when the user wants to persist a full
  connection string instead of discrete fields.

## Migration rules

- Missing `schema_version`, `1`, and `1.0.0` auto-migrate to `1.1.0`.
- Legacy `[configuration].pg_bin_path` is renamed to `pg_bin_dir`.
- String `sslmode` values such as `require` / `disable` are normalized to
  boolean form during migration.
- Unsupported future schema versions are a hard stop.
