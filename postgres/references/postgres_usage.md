# Postgres Usage

Use this reference for setup, connection helpers, and the script catalog.

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
- `python3` (3.11+ for `tomllib`) is required for `postgres.toml` profile parsing (`resolve_db_url.sh`, `bootstrap_profile.sh`, `migrate_toml_schema.sh`). One-off `DB_URL` resolution does not require TOML parsing.
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
- `DB_DOCS_SEARCH_URL` and `DB_DOCS_SEARCH_MAX_TIME` tune official docs lookup behavior.

## psql usage
Run these from the skill directory (the one that contains `scripts/`).
Set `DB_PROJECT_ROOT` to the target project root (the directory that contains `.skills/postgres/postgres.toml`).

This skill accepts only `DB_*` user-facing env vars. Legacy aliases such as `PROJECT_ROOT`, `DATABASE_URL`, `POSTGRES_URL`, and `PGHOST` are unsupported.
When using TOML profiles, scripts require `postgres.toml` to be on the latest schema version; run `./scripts/migrate_toml_schema.sh` if prompted. One-off `DB_URL` usage bypasses TOML schema checks.

Example:
```sh
export DB_PROJECT_ROOT="/path/to/project"
DB_PROFILE=local ./scripts/test_connection.sh
```

1) Ensure `psql` is on your PATH (only if `psql` is not found). If `[configuration].pg_bin_path` is set, it is prepended automatically. If the key is missing, scripts will try to locate `psql` and persist `pg_bin_path`. If `pg_bin_path` is set but invalid, you will be prompted before updating it.

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

2) Connect:
```sh
export DB_PROFILE=local
eval "$(./scripts/resolve_db_url.sh)"
psql "$DB_URL"
```

If `DB_PROFILE` is unset and `postgres.toml` has multiple profiles, the resolver asks you to choose one (shows profile name + description and suggests a default based on context). In non-interactive runs, set `DB_PROFILE` explicitly.

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
psql "$DB_URL" \
  -v ON_ERROR_STOP=1 \
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
psql "$DB_URL" \
  -v ON_ERROR_STOP=1 \
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

## Official docs search (explicit request only)
Run this helper only when the user explicitly asks to search or verify against official PostgreSQL docs (for example: "search docs", "find official docs", or "verify against official docs"). Do not run it for normal SQL/query/diagnostics requests.

Optional env overrides:
- `DB_DOCS_SEARCH_URL` (default: `https://www.postgresql.org/search/`)
- `DB_DOCS_SEARCH_MAX_TIME` (default: `30`)

```sh
./scripts/search_postgres_docs.sh "row level security policies" 5
```

## Fast object search (by name)
Search tables, views, columns, functions/procedures, triggers, enums/types, indexes, and sequences:

```sh
DB_PROFILE=local ./scripts/find_objects.sh users
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
- `check_psql.sh` — Lightweight check for `psql` presence (uses `pg_env.sh`), prints version if available.
- `test_connection.sh` — Quick connection check (profile-aware).
- `pg_version.sh` — Prints server version (profile-aware).
- `roles_overview.sh` — Lists roles and memberships (profile-aware).
- `schema_introspect.sh` — Schema introspection (profile-aware).
- `schema_diff.sh` — Compares schema-only diffs between two connections.
- `schema_dump.sh` — Schema-only dump (custom or SQL based on file extension).
- `data_dump.sh` — Data-only dump (custom or SQL based on file extension).
- `restore_dump.sh` — Restores a dump file (custom or SQL).
- `connection_info.sh` — Prints connection details and key settings.
- `search_postgres_docs.sh` — Searches official PostgreSQL docs at runtime and returns ranked `docs/current` links with snippets.
  - Example: `./scripts/search_postgres_docs.sh "row level security policies" 5`
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

## Skill maintenance
If you discover or add meaningful scripts under `./scripts`, update this file to list them with a short purpose and example usage so they are easy to find and reuse.

## Learn (skill evolution)
When this skill uncovers useful **generic** queries or workflows, add them as scripts under `./scripts` and document them here. If new **critical** reusable rules emerge, update the guardrails reference.
