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
   - If `postgres.toml` exists, **first** check whether a schema migration is required (missing or outdated `schema_version`); run `./scripts/migrate_toml_schema.sh` before any other bootstrap step.
2) Choose action:
   - Connect/run a query, inspect schema, or run a helper script.
3) Execute and report:
   - Run the requested action and summarize results or errors.
4) Persist only if asked:
   - Update TOML only with explicit user approval, except `[configuration].pg_bin_path` which may be auto-written when missing. `schema_version` is written by the migration helper. Prompt before changing an existing value.

## Connection profiles (primary)
- **Config file:** `<project-root>/.skills/postgres/postgres.toml`
- **Gitignore:** add `<project-root>/.skills/postgres/postgres.toml` to your repo `.gitignore`
- **Template:** copy `postgres.toml.example` to `<project-root>/.skills/postgres/postgres.toml` to get started
- **Schema reference:** `references/postgres_skill_schema.md` (all schema versions and migration rules)
- **Best practices index:** `references/postgres_best_practices/README.md` (general Postgres best practices)
- **Profile sections:** `[database.<profile>]` (e.g. `[database.local]`, `[database.db_test_1]`)
- **Profile name rule:** lowercase letters, digits, underscores only (`^[a-z0-9_]+$`)
- **Default profile:** `local` (set via `DB_PROFILE`)
- **Project metadata:** optional `project` per profile. When `DB_PROFILE` is unset and any profiles define `project`, the skill will try to auto-pick a profile based on the current working directory (monorepo-aware). Profiles without `project` are treated as shared/global.
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
- If `DB_PROFILE` is unset and any profiles define `project`, auto-select the profile matching the current subproject (based on cwd). If no match, fall back to a single global profile (no `project`) or ask the user to set `DB_PROFILE`.
- If `postgres.toml` is missing or the requested profile is missing, ask for **host**, **port**, **database**, **user**, **password** (only ask for **sslmode** if needed).
- If the user provides a connection URL, infer missing fields from it.
- Ask whether to save the profile into `postgres.toml` or use the values as a one-off (temporary) connection.
- During bootstrap, confirm the migrations path. Default to `db/migrations` relative to the project root unless overridden by `[migrations].path` or `DB_MIGRATIONS_PATH`.
- For custom migrations paths, resolve relative paths from the project root; if missing, offer to search under the project root for matches, then offer to create the directory.
- All scripts should support one-off connections via `DB_URL` (and `DB_URL_A`/`DB_URL_B` for compare scripts) without requiring `postgres.toml`.

## Quick entrypoints
- Bootstrap: `./scripts/bootstrap_profile.sh`
- Check `psql`: `./scripts/check_psql.sh`
- Check dependencies: `./scripts/check_deps.sh`
- Test connection (uses TOML): `DB_PROFILE=local ./scripts/test_connection.sh`
- One-off connection: `DB_URL="postgresql://user:pass@host:5432/dbname" ./scripts/test_connection.sh`

## Script index (keep current)
- `resolve_db_url.sh` — Resolves `DB_URL` from `postgres.toml` or `DB_URL` env for one-off use.
- `psql_with_ssl_fallback.sh` — Runs `psql` with automatic SSL retry when needed.
- `bootstrap_profile.sh` — Interactive profile setup with optional project scan.
- `check_deps.sh` — Verifies required CLI tools and prints install hints.
- `check_psql.sh` — Lightweight check for `psql` presence (uses `pg_env.sh`), prints version if available.
- `test_connection.sh` — Quick connection check (profile-aware).
- `pg_version.sh` — Prints server version (profile-aware).
- `roles_overview.sh` — Lists roles and memberships (profile-aware).
- `schema_introspect.sh` — Schema introspection (profile-aware).
- `schema_diff.sh` — Compares schema-only diffs between two connections (example: `./scripts/schema_diff.sh local staging`).
- `schema_dump.sh` — Schema-only dump (custom or SQL based on file extension).
- `data_dump.sh` — Data-only dump (custom or SQL based on file extension).
- `restore_dump.sh` — Restores a dump file (custom or SQL).
- `connection_info.sh` — Prints connection details and key settings.
- `table_sizes.sh` — Lists largest tables (total/table/index sizes) (example: `./scripts/table_sizes.sh 20`).
- `locks_overview.sh` — Shows blocked/blocking sessions and queries.
- `slow_queries.sh` — Lists slowest queries from `pg_stat_statements` (if enabled) (example: `./scripts/slow_queries.sh 20`).
- `index_health.sh` — Highlights missing/unused index candidates (example: `./scripts/index_health.sh 20`).
- `activity_overview.sh` — Lists active sessions and queries (example: `./scripts/activity_overview.sh 20`).
- `long_running_queries.sh` — Shows active queries exceeding a duration threshold (example: `./scripts/long_running_queries.sh 5 20`).
- `cancel_backend.sh` — Cancels a running query (prompts for confirmation) (example: `./scripts/cancel_backend.sh 12345`).
- `terminate_backend.sh` — Terminates a backend (prompts for confirmation) (example: `DB_CONFIRM=YES ./scripts/terminate_backend.sh 12345`).
- `query_action.sh` — Lists matching active queries, then cancels or terminates selected PIDs (example: `./scripts/query_action.sh cancel --query \"select * from events\"`).
- `explain_analyze.sh` — Runs `EXPLAIN (ANALYZE, BUFFERS)` for a provided SQL statement (example: `./scripts/explain_analyze.sh \"select * from users\"`; use `--no-analyze` to avoid executing the query).
- `pg_stat_statements_top.sh` — Shows top queries by total/mean execution time.
- `vacuum_analyze_status.sh` — Summarizes VACUUM/ANALYZE recency and dead tuples.
- `missing_fk_indexes.sh` — Lists foreign keys without supporting indexes.
- `update_sslmode.sh` — Updates `sslmode` for a profile in `postgres.toml` (used by the fallback flow).
- `migrate_toml_schema.sh` — Migrates `postgres.toml` to the latest schema version (adds `schema_version`, normalizes `sslmode`).
- `bootstrap_profile.py` — Helper for interactive profile setup (used by `bootstrap_profile.sh`).

## Skill maintenance (keep this list current)
If you discover or add meaningful scripts under `./scripts`, update this file to list them with a short purpose and example usage (especially when arguments are required) so they are easy to find and reuse.

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
