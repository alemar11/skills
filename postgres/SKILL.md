---
name: postgres
description: Connect to Postgres databases, run queries/diagnostics, review backend SQL for performance, and search official PostgreSQL docs only when explicitly requested.
---

# Postgres

## Goal
Use this skill to connect to Postgres, run user-requested queries/diagnostics, review backend SQL for performance, and search official PostgreSQL docs only when explicitly requested.

## Fast path (copy/paste)
- Ad-hoc read query:
  - `DB_PROFILE=local ./scripts/run_sql.sh -c "select now();"`
- DDL/DO block (safe quoting):
  - `DB_PROFILE=local ./scripts/run_sql.sh <<'SQL'`
  - `DO $$ BEGIN RAISE NOTICE 'ok'; END $$;`
  - `SQL`
- Connection test:
  - `DB_PROFILE=local ./scripts/test_connection.sh`
- Find objects:
  - `DB_PROFILE=local ./scripts/find_objects.sh users`

## Workflow
1) Confirm connection source:
   - If `DB_URL` is provided, use it for a one-off connection unless the user asks to persist it.
   - Use only `DB_*` environment variables for this skill. Non-`DB_*` aliases (for example `PROJECT_ROOT`, `DATABASE_URL`, `PGHOST`) are unsupported.
   - Use `postgres.toml` when present; otherwise ask the user for the data required to create a profile.
   - If a `postgres.toml` is already present under the current repo/root at `.skills/postgres/postgres.toml`, treat that repo/root as the project root and proceed without prompting for `DB_PROJECT_ROOT`.
   - If not in a git repo, or if running outside the target project, set `DB_PROJECT_ROOT` explicitly.
   - When creating or loading `postgres.toml` and the target project is a git repo, verify `.skills/postgres/postgres.toml` is gitignored to avoid committing credentials.
   - If `postgres.toml` exists, **first** ensure it is at the latest schema version. Run `./scripts/migrate_toml_schema.sh` only when an older schema is found, and run it from the skill dir only if `DB_PROJECT_ROOT` is set.
   - Treat missing or outdated `schema_version` as a hard stop for TOML profile usage; migrate first, then continue.
   - In `postgres.toml`, `sslmode` must be a boolean (`true`/`false`), not a string.
2) Choose action:
   - Connect/run a query, inspect schema, review backend SQL/query usage, or run a helper script.
   - If the user wants to copy data from a dev/local DB into a production migration or seed SQL, treat that as a data-copy migration workflow: inspect the source rows, inspect target table defaults/constraints, generate SQL in the pending migration file, and expect follow-up edits to adapt values for production.
   - Default query runner: use `./scripts/psql_with_ssl_fallback.sh` (or `./scripts/run_sql.sh` for SQL text/file/stdin).
   - If the user says a migration is "migrated", "released", or "run in production", execute the release workflow in `references/postgres_guardrails.md` (move pending SQL to `released/` and transition changelog entries from `WIP` to `RELEASED`).
   - For official PostgreSQL docs lookup, use `./scripts/search_postgres_docs.sh` only when the user explicitly asks for docs search/verification.
3) Execute and report:
   - Run the requested action and summarize results or errors.
   - If a connection test fails, run `./scripts/check_deps.sh` and/or `./scripts/connection_info.sh` to diagnose.
4) Persist only if asked:
   - Update TOML only with explicit user approval, except `[configuration].pg_bin_path` which may be auto-written when missing. `schema_version` is written by the migration helper. Prompt before changing an existing value.

## Backend query performance review
- Use this path when the user asks to review backend queries, inspect SQL for speed, improve loading time, or analyze schema/index support.
- Inventory read queries separately from write queries before making recommendations.
- Unless the user explicitly includes writes, optimize only read-side queries and treat write queries as out of scope.
- Prioritize by user-visible loading time, query count per request, and obvious scaling risks over local row counts.
- Look for:
  - N+1 query patterns
  - dynamic `IN (...)` SQL that should become parameterized arrays
  - recursive views/CTEs on hot read paths
  - repeated correlated `EXISTS` / `COUNT(*)` subqueries
  - missing composite indexes that match real join/filter predicates
- Validate with schema/catalog inspection first:
  - `pg_indexes`
  - `pg_stats`
  - `pg_views`
  - relation size and stats when useful
- Treat local data volume as inspection context only. Do not overfit conclusions to small local datasets if the user is concerned about production scale.
- Report findings in this shape:
  - hotspot
  - why it scales poorly
  - safe optimization approach
  - payload/behavior constraints
  - validation method
- When helpful, recommend `EXPLAIN (ANALYZE, BUFFERS)` targets, but do not require live benchmarking to identify obvious query-shape issues.

## SQL safety
- Never run `DO $$ ... $$` using `-c "..."` with double quotes; shell expansion can break `$$`.
- Prefer `./scripts/run_sql.sh` with heredoc (`<<'SQL'`) or a `.sql` file.
- If `-c` is unavoidable for `DO $$`, escape dollars as `\$\$`.

## Data-copy migrations
- Use this path when the user wants to copy selected rows from a local/dev database into a SQL file that will later run against production.
- First inspect the source rows and the target table shape:
  - source data to copy
  - `information_schema.columns`
  - relevant foreign keys / indexes / defaults when needed
- Default destination is the pending migration file resolved by the guardrails workflow, not a direct write to production.
- Treat copied values as a draft for production:
  - expect the user to rename labels, swap foreign-key references, trim arrays, or otherwise adapt values
  - preserve the structure of the copied row, but do not assume local IDs or environment-specific values are valid in production
- Never copy generated identifiers from the source database into production seed SQL when the target column is generated by default (`serial`, identity, sequence-backed PKs).
- If downstream rows depend on generated IDs, use `INSERT ... RETURNING` and CTE chaining to resolve foreign keys inside the same SQL file instead of hard-coding local IDs.
- For child rows, prefer referencing newly inserted parents through stable business keys or returned IDs rather than copied source PK values.
- Keep schema changes separate in reasoning:
  - DDL still follows the normal approval guardrails
  - data inserts/updates requested by the user can be prepared in the pending migration file without extra approval
- After drafting the SQL, summarize any values that were intentionally changed from dev/local to fit production.

## Task to script map
- Ad-hoc SQL query: `./scripts/run_sql.sh` (or `./scripts/psql_with_ssl_fallback.sh`)
- Connection check: `./scripts/test_connection.sh`
- Connection diagnostics: `./scripts/check_deps.sh`, `./scripts/connection_info.sh`
- Postgres version: `./scripts/pg_version.sh`
- Find objects by name: `./scripts/find_objects.sh`
- Schema introspection: `./scripts/schema_introspect.sh`
- Data-copy migration drafting: use repo search plus `./scripts/run_sql.sh` for source-row extraction, schema/default inspection, and FK validation
- Backend query review: use repo search plus `./scripts/run_sql.sh` for catalog inspection and validation
- Slow/active query diagnostics: `./scripts/slow_queries.sh`, `./scripts/activity_overview.sh`, `./scripts/long_running_queries.sh`
- Lock diagnostics: `./scripts/locks_overview.sh`
- Official docs search (explicit request only): `./scripts/search_postgres_docs.sh`
- Flag migration as migrated/run in production: follow release workflow in `references/postgres_guardrails.md`

## Config and schema (brief)
- Config file: `<project-root>/.skills/postgres/postgres.toml`
- Template (canonical schema): `assets/postgres.toml.example`
- Schema history/migrations: `references/postgres_skill_schema.md`
- Env var contract: `references/postgres_env.md`
- Best practices index: `references/postgres_best_practices/README.md`
- Scripts are intended to be run from the skill directory; set `DB_PROJECT_ROOT` to the target project root.

## Trigger rules (summary)
- If `<project-root>/.skills/postgres/postgres.toml` exists, do not scan by default; only scan when asked or missing.
- If that TOML is under the current repo/root, use that root for scripts without asking for `DB_PROJECT_ROOT`.
- If `DB_PROFILE` is unset and multiple profiles exist, ask the user which profile to use before running queries. Show profile `name` + `description`, and include a context-based suggested default.
- If `DB_PROFILE` is unset and exactly one profile exists, use it.
- If `postgres.toml` is missing, ask for host/port/database/user/password to create a profile (ask for `sslmode` only if needed).
- If the requested profile is missing, ask for the profile details to add it.
- If the user provides a connection URL, infer missing fields from it.
- Ask whether to save the profile into `postgres.toml` or use a one-off (temporary) connection.
- Do not run `./scripts/search_postgres_docs.sh` unless the user explicitly asks for official docs lookup/verification.
- If the user asks to copy rows from dev/local into a production SQL file, inspect both the source row values and the target table defaults/constraints before drafting the migration.
- When drafting copied data for production, do not preserve generated PK values by default; rewrite dependent inserts to resolve FK targets via returned IDs or stable keys.
- If the user asks for backend query optimization or performance review, inspect the application query code and separate read paths from write paths before recommending changes.
- For migrations path resolution and schema-change workflow, follow the guardrails reference.
- If the user explicitly marks a migration as migrated/released/run in production, perform the release workflow in guardrails immediately (unless they ask for a dry run only).
- If `CHANGELOG.md` is not in `WIP/RELEASED` format, migrate it to that template before writing new migration notes.
- If the user asks to refresh Postgres best-practices docs/references, treat that as maintainer-only workflow outside this runtime skill.

## Guardrails (summary)
- Always ask for approval before making any database structure change (DDL like CREATE/ALTER/DROP).
- Keep pending changes in prerelease migration files and maintain a changelog.
- Do not edit existing released SQL files; only create a new released file by moving a pending prerelease file when the user explicitly confirms release.
- Use released filename policy: `YYYYMMDDHHMMSS.sql`; add `_<slug>` only on same-second collision; add `_<slug>_01`, `_02`, ... if still colliding.
- Maintain changelog sections as `## WIP` and `## RELEASED`; if the changelog is not in this template, migrate it first, then continue updates.
- When releasing, remove related bullets from `WIP` and add one short summary under `RELEASED` (newest first).
- After any schema change, run the least expensive query that confirms the change.
- For full rules and migration workflow, read `references/postgres_guardrails.md` when doing schema changes.

## Common requests
- Run SQL safely (inline):
  - `DB_PROFILE=local ./scripts/run_sql.sh -c "select 1;"`
- Run SQL safely (heredoc):
  - `DB_PROFILE=local ./scripts/run_sql.sh <<'SQL'`
  - `select current_database();`
  - `SQL`
- Check connection: `DB_PROFILE=local ./scripts/test_connection.sh`
- Postgres version: `DB_PROFILE=local ./scripts/pg_version.sh`
- Connection details: `DB_PROFILE=local ./scripts/connection_info.sh`
- Find objects by name: `DB_PROFILE=local ./scripts/find_objects.sh users`

## Usage references
- Setup, env defaults, and script catalog: `references/postgres_usage.md`
