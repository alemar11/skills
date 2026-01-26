---
name: postgres
description: Connect to Postgres databases and run queries or checks. Use when asked to access a DB or execute SQL.
---

# Postgres

## Goal

Use this skill to connect to Postgres and run user-requested queries or checks.

## Workflow
1) Confirm connection source:
   - Use `postgres.toml` when present; otherwise ask the user for a `DB_PROFILE` or a `DB_URL`.
2) Choose action:
   - Connect/run a query, inspect schema, or run a helper script.
3) Execute and report:
   - Run the requested action and summarize results or errors.
4) Persist only if asked:
   - Update TOML only with explicit user approval, except `[configuration].pg_bin_path` which may be auto-written when missing. `schema_version` is written by the migration helper. Prompt before changing an existing value.

## Default Local Example
The canonical source is `postgres.toml`. The values below are just a minimal reference.

## Connection profiles (primary)
- **Config file:** `<project-root>/.skills/postgres/postgres.toml`
- **Gitignore:** add `<project-root>/.skills/postgres/postgres.toml` to your repo `.gitignore`
- **Template:** copy `postgres.toml.example` to `<project-root>/.skills/postgres/postgres.toml` to get started
- **Schema reference:** `references/postgres_skill_schema.md` (all schema versions and migration rules)
- **Best practices index:** `references/postgres_best_practices/README.md` (general Postgres best practices)
- **Profile sections:** `[database.<profile>]` (e.g. `[database.local]`, `[database.db_test_1]`)
- **Profile name rule:** lowercase letters, digits, underscores only (`^[a-z0-9_]+$`)
- **Default profile:** `local` (set via `DB_PROFILE`)
- **Default sslmode:** `false` under `[database]`. Each `[database.<profile>]` can override `sslmode` (if a connection fails and SSL retry succeeds, ask before updating the TOML to `true`).
- **Optional fields:** `project`, `description`, `migrations_path` (per-profile override)
- **Optional section:** `[migrations] path = "<migrations_path>"` (per-user default)
- **Required section:** `[configuration] schema_version = 1` (TOML schema version; missing implies pre-1 and must be migrated)
- **Required section:** `[configuration] pg_bin_path = "<bin_dir>"` (prepends to PATH; auto-set when missing; migration fails if it cannot be determined)

Example TOML lives in `postgres.toml.example`.

## Schema summary (current)
- `schema_version` is required; missing implies pre-1 and must be migrated.
- For full version history and migration rules, see `references/postgres_skill_schema.md`.
- Run `./scripts/migrate_toml_schema.sh` to upgrade legacy TOMLs (rewrites file and may drop comments).

## When the skill is triggered
- If `<project-root>/.skills/postgres/postgres.toml` exists, **do not** prompt to scan by default; assume the project is already configured. Only offer a scan if the user explicitly asks for it or if the TOML is missing.
- Ask whether to scan the project for existing DB configs (env/code/config files) **only** when the TOML is missing or the user requests it.
- If scan is approved, recap found configs in TOML format and ask whether to modify them. The `project` field is inferred from the scan root (monorepo-aware: `apps/`, `packages/`, `services/`, `modules/`, `projects/`).
- If `postgres.toml` is missing or the requested profile is missing, ask for **host**, **port**, **database**, **user**, **password** (only ask for **sslmode** if needed).
- If the user provides a connection URL, infer missing fields from it.
- Ask whether to save the profile into `postgres.toml` or use the values as a one-off (temporary) connection.
- During bootstrap, confirm the migrations path (per profile). Default to `db/migrations` relative to the project root unless overridden by `[migrations].path` or `DB_MIGRATIONS_PATH` (relative overrides resolve from the project root).
- For custom migrations paths, resolve relative paths from the project root; if missing, offer to search under the project root for matches, then offer to create the directory.
- If the default path is relative and missing, offer to create it. If `AGENTS.md` is missing, ask whether it should be created to store `DB_MIGRATIONS_PATH`.
- All scripts should support one-off connections via `DB_URL` (and `DB_URL_A`/`DB_URL_B` for compare scripts) without requiring `postgres.toml`.

## Install psql
macOS (Homebrew, latest):
```sh
brew update
latest="$(brew search postgresql@ | awk '/^postgresql@/ {print $1}' | sort -V | tail -n 1)"
brew install "${latest:-postgresql}"
```

Ubuntu/Debian:
- `sudo apt update && sudo apt install -y postgresql-client`

Fedora:
- `sudo dnf install -y postgresql`

Arch:
- `sudo pacman -S postgresql`

Windows:
- `winget install PostgreSQL.PostgreSQL`
- or `choco install postgresql`

## Dependencies
- `python3` (3.11+ for `tomllib`) is required by `resolve_db_url.sh` and the SSL fallback flow.
  - macOS: prefer Homebrew `python3` (3.11+) to avoid the older system Python. Example:
    ```sh
    export PATH="$(brew --prefix python)/bin:$PATH"
    python3 --version
    ```
- `pg_dump`/`pg_restore` are required for schema diff and dump/restore helpers.

## Optional safety defaults (recommended)
- `DB_APPLICATION_NAME` (default: `codex-postgres-skill`) sets a consistent `application_name`.
- `DB_STATEMENT_TIMEOUT_MS` and `DB_LOCK_TIMEOUT_MS` apply session timeouts via `PGOPTIONS`.
- `DB_AUTO_UPDATE_SSLMODE=1` auto-persists `sslmode=true` after a successful retry (otherwise ask and print the command).
- `DB_CONFIRM=YES` skips confirmation prompts for cancel/terminate scripts.
- `DB_VIEW_DEF_TRUNC` and `DB_FUNC_DEF_TRUNC` truncate view/function definitions in schema introspection output.

## psql usage
Run these from your project root (the directory that contains `.skills/postgres/postgres.toml`).
If you need to run from the skill directory, set `DB_PROJECT_ROOT` (or `PROJECT_ROOT`) to your project root first.
1. Ensure `psql` is on your PATH (only if `psql` is not found). If `[configuration].pg_bin_path` is set, it is prepended automatically. If the key is missing, scripts will try to locate `psql` and persist `pg_bin_path`. If `pg_bin_path` is set but invalid, you will be prompted before updating it.

macOS (Homebrew):
```sh
formula="$(brew list --versions | awk '/^postgresql(@[0-9]+)? / {print $1}' | sort -V | tail -n 1)"
export PATH="$(brew --prefix "${formula:-postgresql}")/bin:$PATH"
```
```sh
which psql && psql --version
```

Ubuntu/Debian (default location):
```sh
export PATH="/usr/lib/postgresql/$(ls /usr/lib/postgresql | sort -V | tail -n 1)/bin:$PATH"
```
```sh
which psql && psql --version
```

Fedora/Arch (usually already on PATH):
```sh
export PATH="/usr/bin:$PATH"
```
```sh
which psql && psql --version
```

Windows (PowerShell):
```powershell
$env:Path = "C:\\Program Files\\PostgreSQL\\bin;" + $env:Path
```
```powershell
Get-Command psql; psql --version
```

2. Connect:

```sh
export DB_PROFILE=local
eval "$(./scripts/resolve_db_url.sh)"
psql "$DB_URL"
```

Note: use `./scripts/psql_with_ssl_fallback.sh` (or scripts that wrap it) if you want automatic SSL retry. If the retry succeeds, ask before updating `postgres.toml` unless `DB_AUTO_UPDATE_SSLMODE=1` is set.

## Bootstrap a profile (interactive)
This helper will optionally scan a project for existing config, recap candidates in TOML format, and let you save or use a one-off connection. It prompts for the project root to scan.

```sh
./scripts/bootstrap_profile.sh
```

## Temporary connection (no TOML write)
Use `DB_URL` for a one-off connection without updating `postgres.toml`:

```sh
DB_URL="postgresql://user:pass@host:5432/dbname" \
  ./scripts/test_connection.sh
```

## Connection test (use this to ensure the connection is doable)
Run this script to verify the DB connection quickly (uses `postgres.toml`, default profile `local`):

```sh
DB_PROFILE=local ./scripts/test_connection.sh
```

## Postgres version
Print the server version quickly (uses `postgres.toml`, default profile `local`):

```sh
DB_PROFILE=local ./scripts/pg_version.sh
```

## Roles and users overview
List roles, login capability, key privileges, and role memberships (uses `postgres.toml`, default profile `local`):

```sh
DB_PROFILE=local ./scripts/roles_overview.sh
```

Or run just the SQL directly:

```sh
eval "$(./scripts/resolve_db_url.sh)"
psql "$DB_URL" \\
  -v ON_ERROR_STOP=1 \\
  -f ./scripts/roles_overview.sql
```

## Schema introspection (tables, columns, relationships, indexes, constraints, views, functions, extensions)
Reusable scripts live in `./scripts`:

- SQL: `./scripts/schema_introspect.sql`
- Runner: `./scripts/schema_introspect.sh`

Run the introspection script (uses `postgres.toml`, default profile `local`):

```sh
DB_PROFILE=local ./scripts/schema_introspect.sh
```

Truncate view/function definitions:

```sh
DB_VIEW_DEF_TRUNC=200 DB_FUNC_DEF_TRUNC=200 ./scripts/schema_introspect.sh
```

Or run just the SQL directly:

```sh
eval "$(./scripts/resolve_db_url.sh)"
psql "$DB_URL" \\
  -v ON_ERROR_STOP=1 \\
  -f ./scripts/schema_introspect.sql
```

## Schema diff (compare two connections)
Compare schema-only diffs between two profiles:

```sh
./scripts/schema_diff.sh local staging
```

Or via env:

```sh
DB_PROFILE_A=local DB_PROFILE_B=staging ./scripts/schema_diff.sh
```

## Quick diagnostics (examples)
```sh
./scripts/check_deps.sh
./scripts/connection_info.sh
./scripts/table_sizes.sh 20
./scripts/locks_overview.sh
./scripts/slow_queries.sh 20
./scripts/index_health.sh 20
./scripts/activity_overview.sh 20
./scripts/long_running_queries.sh 5 20
```

## Backup and restore (examples)
```sh
./scripts/schema_dump.sh
./scripts/data_dump.sh
./scripts/restore_dump.sh ./schema_local_20240101_120000.dump
```

## Activity control (use with care)
```sh
./scripts/cancel_backend.sh 12345
DB_CONFIRM=YES ./scripts/terminate_backend.sh 12345
./scripts/query_action.sh cancel --query "select * from events"
```

## Script index (keep current)
- `resolve_db_url.sh` — Resolves `DB_URL` from `postgres.toml` or `DB_URL` env for one-off use.
  - Example: `eval "$(./scripts/resolve_db_url.sh)"`
- `psql_with_ssl_fallback.sh` — Runs `psql` with automatic SSL retry when needed.
  - Example: `./scripts/psql_with_ssl_fallback.sh -v ON_ERROR_STOP=1 -c "select 1;"`
- `bootstrap_profile.sh` — Interactive profile setup with optional project scan.
- `check_deps.sh` — Verifies required CLI tools and prints install hints.
- `test_connection.sh` — Quick connection check (profile-aware).
- `pg_version.sh` — Prints server version (profile-aware).
- `roles_overview.sh` — Lists roles and memberships (profile-aware).
- `schema_introspect.sh` — Schema introspection (profile-aware).
- `schema_diff.sh` — Compares schema-only diffs between two connections.
- `schema_dump.sh` — Schema-only dump (custom or SQL based on file extension).
- `data_dump.sh` — Data-only dump (custom or SQL based on file extension).
- `restore_dump.sh` — Restores a dump file (custom or SQL).
- `connection_info.sh` — Prints connection details and key settings.
- `table_sizes.sh` — Lists largest tables (total/table/index sizes).
- `locks_overview.sh` — Shows blocked/blocking sessions and queries.
- `slow_queries.sh` — Lists slowest queries from `pg_stat_statements` (if enabled).
- `index_health.sh` — Highlights missing/unused index candidates.
- `activity_overview.sh` — Lists active sessions and queries.
- `long_running_queries.sh` — Shows active queries exceeding a duration threshold.
- `cancel_backend.sh` — Cancels a running query (prompts for confirmation).
- `terminate_backend.sh` — Terminates a backend (prompts for confirmation).
- `query_action.sh` — Lists matching active queries, then cancels or terminates selected PIDs.
- `explain_analyze.sh` — Runs `EXPLAIN (ANALYZE, BUFFERS)` for a provided SQL statement (use `--no-analyze` to avoid executing the query).
- `pg_stat_statements_top.sh` — Shows top queries by total/mean execution time.
- `vacuum_analyze_status.sh` — Summarizes VACUUM/ANALYZE recency and dead tuples.
- `missing_fk_indexes.sh` — Lists foreign keys without supporting indexes.
- `update_sslmode.sh` — Updates `sslmode` for a profile in `postgres.toml` (used by the fallback flow).
- `migrate_toml_schema.sh` — Migrates `postgres.toml` to the latest schema version (adds `schema_version`, normalizes `sslmode`).
- `bootstrap_profile.py` — Helper for interactive profile setup (used by `bootstrap_profile.sh`).

## Skill maintenance (keep this list current)
If you discover or add meaningful scripts under `./scripts`, update this file to list them with a short purpose and example usage so they are easy to find and reuse.

## Learn (skill evolution)
When this skill uncovers useful **generic** queries or workflows, add them as scripts under `./scripts` and document them here. If new **critical** reusable rules emerge, update the Guardrails section too. The skill should continuously evolve and improve.

## Guardrails
- Always ask for approval before making any database structure change (DDL like CREATE/ALTER/DROP).
- Keep pending changes in `<migrations_path>/prerelease.sql` (or ordered `1_prerelease.sql`, `2_prerelease.sql` if splitting is needed).
- Never touch any file or folder whose name ends with `released` (case-insensitive) inside the chosen migrations folder.
- Maintain `<migrations_path>/CHANGELOG.md` with dated entries; create it if missing and remove entries for released migrations.
- Whenever you modify prerelease migration file(s), update `<migrations_path>/CHANGELOG.md` with a dated entry for that change (every time).

## Important rule for DB structure changes
After the change is approved and completed, ask where to save the migration SQL. Resolve `<migrations_path>` in this order: `[database.<profile>].migrations_path`, then `[migrations].path` from `postgres.toml`, then `AGENTS.md` (`DB_MIGRATIONS_PATH`), then the default `<migrations_path>` at the project root.
Prefer creating or updating the **latest pending** migration file when possible (the most recent migration that has not yet been released/applied), even if it touches multiple schema objects.
If a single migration file becomes too complex, propose splitting it into meaningful, ordered files.
If the same view/table is changed multiple times on the same day across different migration files, check whether they should be compacted into a single file and ask the user. If approved, consolidate and remove the superseded migration files.

## Post-change verification
After any schema change, run the least expensive query that confirms the change (e.g., check `information_schema` or `pg_catalog` for views/tables/columns) to ensure the update matches expectations.
