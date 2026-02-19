# Postgres Skill TOML Schema

This document describes all known `postgres.toml` schema versions for the postgres skill.

## Schema versioning rules
- `schema_version` is required in all new TOMLs.
- Missing `schema_version` is treated as pre-1 (version 0) and must be migrated.
- Any schema change must:
  - Bump `schema_version` in `assets/postgres.toml.example`.
  - Add a migration step for every prior version in `scripts/migrate_toml_schema.sh`.
  - Update this document with the new version details.

## Version 1 (current)
**Status:** current.

### Required
```toml
[configuration]
schema_version = 1
pg_bin_path = "/path/to/postgres/bin"
```

### Defaults / base tables
```toml
[database]
sslmode = false
```

### Profiles
Profiles live under `[database.<profile>]`.

Required fields:
- `host`
- `port`
- `database`
- `user`
- `password`

Optional fields:
- `project`
- `description`
- `migrations_path`
- `sslmode` (boolean override; defaults to `[database].sslmode`)
- `url` (full connection URL; if set, it overrides host/port/user/password/database)

### Optional global section
```toml
[migrations]
path = "db/migrations"
```

### Behavior
- `sslmode = false` maps to `sslmode=disable` in connection URLs.
- `sslmode = true` maps to `sslmode=require` in connection URLs.
- `pg_bin_path` must point to a directory containing a `psql` binary.
- `project` (per-profile) is used for auto-selecting a profile when `DB_PROFILE` is unset; profiles without `project` are treated as shared/global.
- Runtime TOML profile usage enforces `schema_version == 1`; if missing/outdated, run `./scripts/migrate_toml_schema.sh` before using profile-based scripts.
- One-off `DB_URL` usage does not require `postgres.toml` and bypasses TOML schema checks.

## Version 0 (legacy, pre-`schema_version`)
**Status:** legacy; must be migrated to v1.

### Notes
- No `[configuration]` table.
- `sslmode` values may appear as strings (e.g., `"disable"`, `"require"`, `"verify-full"`)
  or booleans depending on historical usage. In v1, `sslmode` in TOML is strictly boolean.

### Migration to v1
- Add `[configuration].schema_version = 1`.
- Normalize `sslmode` to boolean:
  - `"disable"` → `false`
  - `"require"`, `"verify-ca"`, `"verify-full"`, `"true"`, `"enable"` → `true`
- If `sslmode` is unrecognized (e.g., `prefer`, `allow`), migration fails and requires a manual fix
  (set `sslmode` to `true|false`, or remove it and rely on a one-off `DB_URL` with the desired `sslmode`).
- Add `[configuration].pg_bin_path` (detected from `psql` or set explicitly).
