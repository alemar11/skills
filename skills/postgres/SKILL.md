---
name: postgres
description: Connect to Postgres databases, run SQL and diagnostics, inspect schemas and migrations, review query performance, and use common PostGIS or pgvector patterns.
---

# Postgres

## Goal
Use this skill to connect to Postgres, run SQL, inspect schemas, review query
performance, design tables and indexes, work with common PostGIS or pgvector
patterns, and manage migration release flow through the shipped
`scripts/postgres` artifact in the skill package.

## Runtime surface

- The only supported runtime entrypoint is the shipped `scripts/postgres`
  artifact inside this skill package.
- If your current working directory is the skill root, run it as
  `./scripts/postgres`.
- If you are invoking the skill from another repo, resolve the skill package
  path first and run `<postgres-skill-root>/scripts/postgres`.
- `<postgres-skill-root>/scripts/postgres --version` is the runtime version
  check.
- Do not use or reintroduce per-task helper scripts from the pre-Rust runtime
  surface.
- The implementation lives in `projects/postgres/` and is maintenance-only.
  Normal usage stays on the `scripts/postgres` surface.
- Canonical persisted config lives at
  `<project-root>/.skills/postgres/config.toml`.
- This runtime skill does not provide dump, restore, export, or schema-diff
  workflows. Keep those operator tasks outside this skill.
- If a target repo has `.skills/postgres/config.toml` or legacy
  `.skills/postgres/postgres.toml`, use the shipped `scripts/postgres`
  artifact for normal app-database work instead of raw `psql`.
- Bare `psql` is allowed only as an explicit exception for container-local
  runbooks such as `docker compose exec pg psql ...`, repo-documented smoke
  checks, unsupported operator workflows outside this skill's runtime surface,
  or emergency fallback when the shipped artifact cannot run.

## Fast path

- Resolve the shipped CLI once and reuse it in commands below:
  - `POSTGRES_CLI=/path/to/postgres-skill/scripts/postgres`
- Doctor / setup status:
  - `DB_PROJECT_ROOT=/path/to/repo "$POSTGRES_CLI" --json doctor`
- Bootstrap and save a profile:
  - `DB_PROJECT_ROOT=/path/to/repo "$POSTGRES_CLI" profile bootstrap --save`
- Resolve the active connection:
  - `DB_PROJECT_ROOT=/path/to/repo DB_PROFILE=local "$POSTGRES_CLI" --json profile resolve`
- Run ad-hoc SQL:
  - `DB_PROJECT_ROOT=/path/to/repo DB_PROFILE=local "$POSTGRES_CLI" query run -c "select now();"`
- Run a SQL file:
  - `DB_PROJECT_ROOT=/path/to/repo DB_PROFILE=local "$POSTGRES_CLI" query run -f ./query.sql`
- Safe heredoc for multi-statement SQL / `DO $$`:
  - `DB_PROJECT_ROOT=/path/to/repo DB_PROFILE=local "$POSTGRES_CLI" query run <<'SQL'`
  - `select now();`
  - `SQL`
- Connection test:
  - `DB_PROJECT_ROOT=/path/to/repo DB_PROFILE=local "$POSTGRES_CLI" profile test`
- Schema introspection:
  - `DB_PROJECT_ROOT=/path/to/repo DB_PROFILE=local "$POSTGRES_CLI" schema inspect`
- Toolbox-style catalog and diagnostic commands:
  - `DB_PROJECT_ROOT=/path/to/repo DB_PROFILE=local "$POSTGRES_CLI" toolbox database-overview`
  - `DB_PROJECT_ROOT=/path/to/repo DB_PROFILE=local "$POSTGRES_CLI" toolbox list-tables`
- Object search:
  - `DB_PROJECT_ROOT=/path/to/repo DB_PROFILE=local "$POSTGRES_CLI" query find users --types table,column`
- Release a pending migration file:
  - `DB_PROJECT_ROOT=/path/to/repo DB_PROFILE=local "$POSTGRES_CLI" migration release --summary "Add agent-context prompt sections"`

## Workflow
1) Confirm connection source:
   - If `DB_URL` is provided, use it for a one-off connection unless the user
     explicitly asks to persist it.
   - Prefer `DB_*` environment variables. Compatibility inputs such as
     `DATABASE_URL`, `POSTGRES_URL`, `POSTGRESQL_URL`, and libpq vars
     (`PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`, `PGSSLMODE`)
     are also accepted.
   - `PROJECT_ROOT` remains unsupported; use `DB_PROJECT_ROOT`.
   - If `<project-root>/.skills/postgres/config.toml` exists, use it.
   - Else if legacy `<project-root>/.skills/postgres/postgres.toml` exists,
     runtime migrates it one-way into canonical `config.toml` and continues on
     the canonical path.
   - During that migration, make sure the consuming repo ignores
     `.skills/postgres/config.toml` too; do not leave the canonical file
     unignored when the legacy `postgres.toml` had ignore coverage.
   - If the user explicitly asks to create or refresh a saved profile, use the
     shipped `scripts/postgres` artifact from the skill package, for example
     `<postgres-skill-root>/scripts/postgres profile bootstrap`.
2) Choose action:
   - Query or inspect data
   - Inspect schema, indexes, roles, or activity
   - Review query shape or schema design
   - Draft or release migrations
   - Search official PostgreSQL docs only when explicitly requested
3) Execute and report:
   - Return the answer first, then only the supporting context needed to trust
     it.
   - Keep backup, restore, export, and schema-diff requests out of this skill's
     runtime surface.
4) Persist only if asked:
   - Update `config.toml` only with explicit user approval, except canonical
     config migration plus explicit profile bootstrap or `set-ssl` flows.
   - Treat `<project-root>/.skills/postgres/config.toml` as local persisted
     operator config; consuming repos should gitignore it just as they
     previously gitignored legacy `postgres.toml`.

## Command map

- `doctor`
  - Validate config resolution and report runtime readiness without mutating
    config.
- `profile resolve`
  - Show the active URL, profile, and source.
- `profile bootstrap [--save]`
  - Interactively create or print a profile.
- `profile test`
  - Quick connection check.
- `profile info`
  - Print connection details and key server settings.
- `profile version`
  - Show server version.
- `profile migrate-toml`
  - Migrate legacy `postgres.toml` into canonical `config.toml` using schema
    `2.0.0`, and ensure ignore coverage follows the canonical file.
- `profile set-ssl <profile> <true|false>`
  - Persist `sslmode` for a saved profile.
- `query run`
  - Execute SQL from `-c`, `-f`, or stdin, preserving per-statement results.
- `query explain`
  - Run `EXPLAIN`, defaulting to `ANALYZE`.
- `query find <pattern> [--types ...]`
  - Search schemas, tables, columns, views, and functions by name.
- `activity overview|locks|slow|long-running|cancel|terminate|cancel-pid|terminate-pid|pg-stat-top`
  - Runtime diagnostics and query-control operations.
- `schema inspect|table-sizes|index-health|missing-fk-indexes|vacuum-status|roles`
  - Schema and catalog inspection.
- `toolbox <command>`
  - SQL-backed compatibility commands for common MCP Toolbox-style Postgres
    catalog and diagnostic surfaces. Underscore aliases such as
    `execute_sql` are also accepted.
  - Supported commands: `execute-sql`, `get-query-plan`,
    `database-overview`, `list-active-queries`, `list-tables`, `list-views`,
    `list-schemas`, `list-triggers`, `list-indexes`, `list-sequences`,
    `list-available-extensions`, `list-installed-extensions`,
    `list-autovacuum-configurations`, `list-memory-configurations`,
    `list-top-bloated-tables`, `list-replication-slots`, and
    `list-invalid-indexes`.
- `migration release`
  - Move a pending migration into `released/` and update `CHANGELOG.md`.
- `docs search`
  - Search official PostgreSQL current docs.

## Config shape

Canonical persisted config uses owner-level `config.toml`:

```toml
schema_version = "2.0.0"

[defaults]
profile = "local"

[tools.postgres]
sslmode = false
migrations_path = "db/migrations"

[tools.postgres.profiles.local]
description = "Local development DB"
host = "127.0.0.1"
port = 5432
database = "app"
user = "postgres"
password = "postgres"
sslmode = false
migrations_path = "db/migrations"
```

Rules:

- `schema_version` is top-level and required in canonical saved configs.
- Do not add or rely on `[meta]`.
- Canonical `config.toml` is local persisted operator config, not normal repo
  content; consuming repos should gitignore `.skills/postgres/config.toml`.
- When migrating from legacy `postgres.toml`, update ignore rules in the same
  rollout so the canonical file stays untracked too.
- `[defaults]` stores the default saved profile.
- `[tools.postgres]` stores shared Postgres defaults.
- `[tools.postgres.profiles.<name>]` stores per-profile overrides.

## Schema and feature design

- For schema or table design, start with:
  - `references/postgres_best_practices/schema-design.md`
  - `references/postgres_best_practices/advanced-features.md`
- For geospatial tables, SRIDs, radius search, nearest-neighbor lookups, or
  spatial indexing, use `references/postgres_best_practices/postgis.md`.
- For embeddings, semantic search, similarity search, vector indexes, or
  retrieval/RAG in Postgres, use
  `references/postgres_best_practices/pgvector.md`.

## Backend query performance review

- Inventory read queries separately from write queries before recommending
  changes.
- Unless the user explicitly includes writes, optimize only read-side paths.
- Prioritize:
  - N+1 query patterns
  - repeated correlated subqueries
  - dynamic `IN (...)` SQL that should become parameterized arrays
  - missing composite indexes matching real join and filter predicates
- Validate with schema and catalog inspection first (`schema inspect`,
  `schema table-sizes`, `schema index-health`, `activity slow`) before asking
  for live benchmarking.

## SQL safety

- Prefer `query run` with heredoc or `-f` for multi-statement SQL.
- Do not inline `DO $$ ... $$` into double-quoted shell strings.
- Replace raw one-off `psql` queries with `query run`:
  - Raw pattern:
    `PGPASSWORD=... psql -h host -U user -d app -c "select now();"`
  - Skill pattern:
    `DB_PROJECT_ROOT=/path/to/repo DB_PROFILE=local "$POSTGRES_CLI" query run -c "select now();"`
- Replace raw heredoc DDL with `query run` heredocs:

```bash
DB_PROJECT_ROOT=/path/to/repo DB_PROFILE=local "$POSTGRES_CLI" query run <<'SQL'
ALTER TABLE public.example
  ADD COLUMN IF NOT EXISTS description text;

SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'example'
ORDER BY ordinal_position;
SQL
```

- Replace `psql` catalog meta-commands such as `\d+ public.example` with SQL
  catalog queries because `query run` executes SQL, not `psql` meta-commands:

```bash
DB_PROJECT_ROOT=/path/to/repo DB_PROFILE=local "$POSTGRES_CLI" query run -c "
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'example'
ORDER BY ordinal_position;
"
```

## Data-copy migrations

- When copying selected rows from dev or local into a production SQL file:
  - inspect source values and target table shape first
  - treat copied values as a draft for production
  - do not preserve generated primary-key values by default
  - prefer `INSERT ... RETURNING` and stable business keys when dependent rows
    need new IDs
- Keep DDL reasoning separate from requested data-copy SQL.

## Trigger rules

- If `.skills/postgres/config.toml` exists, use it without scanning unless the
  user asks to bootstrap or refresh.
- Else if only legacy `.skills/postgres/postgres.toml` exists, use it as
  migration input to generate canonical `config.toml`, and make sure ignore
  coverage follows the canonical path too.
- If `DB_PROFILE` is unset and exactly one profile exists, use it.
- If multiple profiles exist, prefer the saved `[defaults].profile` when
  present; otherwise require an explicit profile or interactive selection.
- If the user asks to bootstrap or refresh a saved profile, use
  `profile bootstrap`.
- Do not run `docs search` unless the user explicitly asks for official docs
  lookup or verification.
- For migrations path resolution and schema-change workflow, follow
  `references/postgres_guardrails.md`.
- If a pending migration file contains its own `BEGIN` or `COMMIT`, do not wrap
  it in an outer rollback transaction during scratch validation.
- If the user explicitly marks a pending migration as migrated, released, or
  run in production, perform `migration release` immediately unless they ask
  for a dry run only.
- Do not use this runtime skill to refresh best-practices references or
  otherwise upgrade the skill package itself.

## Guardrails

- Always ask for approval before making DDL changes.
- Keep pending changes in prerelease migration files and maintain a changelog.
- Use `pending migration file` and `released migration file` as the canonical
  workflow terms.
- Do not edit existing released SQL files.
- Do not create a new file under `released/` for pending work.
- Only create a released migration file by moving a pending prerelease file when
  the user explicitly confirms release.
- After any schema change, run the least expensive validation query that proves
  the change landed.
- For full rules and migration workflow, read
  `references/postgres_guardrails.md`.

## CLI Maintenance

- Keep normal execution on the shipped `scripts/postgres` artifact.
- Treat `projects/postgres/Cargo.toml` as the single source of truth for the
  CLI semver, and use the shipped `scripts/postgres --version` to verify the
  runtime version.
- Open `projects/postgres/` only when fixing bugs, improving performance,
  rebuilding the shipped binary, or extending the CLI contract.
- Make maintenance changes in `projects/postgres/`, then rebuild
  `scripts/postgres` so the shipped artifact stays current.
- Treat compiled outputs in `projects/postgres/target/` as intermediates, not
  supported runtime entrypoints.
- Keep project-local ignore rules in `projects/postgres/.gitignore`. Only add a
  skill-root `.gitignore` if new generated state truly lives at the skill root.
- Follow semver for shipped CLI changes:
  - major for breaking CLI contract changes
  - minor for backward-compatible new features or meaningful capability
    additions
  - patch for backward-compatible bug fixes and corrections
- After maintenance changes, re-verify through the shipped artifact with:
  - from the skill root: `./scripts/postgres --help`
  - from the skill root: `./scripts/postgres --version`
  - from any cwd: `DB_PROJECT_ROOT=/path/to/repo <postgres-skill-root>/scripts/postgres --json doctor`
- Keep config migration one-way from legacy `postgres.toml` to canonical
  `config.toml`.
- Keep the runtime surface focused on query, inspection, and migration release.
  Do not reintroduce dump, restore, export, or schema-diff commands.

## Usage references

- Setup and runtime usage: `references/postgres_usage.md`
- Env var contract: `references/postgres_env.md`
- Config schema: `references/postgres_skill_schema.md`
- Migration guardrails: `references/postgres_guardrails.md`
- Design guidance: `references/postgres_best_practices/README.md`
- Local/Docker recovery: `references/postgres_local_recovery.md`
