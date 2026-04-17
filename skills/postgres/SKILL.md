---
name: postgres
description: Connect to Postgres databases, run SQL and diagnostics, inspect schemas and migrations, review query performance, and use common PostGIS or pgvector patterns.
---

# Postgres

## Goal
Use this skill to connect to Postgres, run SQL, inspect schemas, review query
performance, design tables/indexes, work with common PostGIS or pgvector
patterns, and manage migration release flow from one canonical CLI:
`./scripts/postgres`.

## Runtime surface

- `./scripts/postgres` is the only supported runtime entrypoint.
- `./scripts/postgres --version` is the runtime version check.
- Do not use or reintroduce per-task helper scripts from the pre-Rust runtime
  surface.
- The implementation lives in `projects/postgres/` and is maintenance-only.
  Normal usage stays on the `scripts/postgres` surface.
- Canonical persisted config lives at
  `<project-root>/.skills/postgres/config.toml`.

## Fast path

- Doctor / setup status:
  - `DB_PROJECT_ROOT=/path/to/repo ./scripts/postgres --json doctor`
- Bootstrap and save a profile:
  - `DB_PROJECT_ROOT=/path/to/repo ./scripts/postgres profile bootstrap --save`
- Resolve the active connection:
  - `DB_PROJECT_ROOT=/path/to/repo DB_PROFILE=local ./scripts/postgres --json profile resolve`
- Run ad-hoc SQL:
  - `DB_PROJECT_ROOT=/path/to/repo DB_PROFILE=local ./scripts/postgres query run -c "select now();"`
- Run a SQL file:
  - `DB_PROJECT_ROOT=/path/to/repo DB_PROFILE=local ./scripts/postgres query run -f ./query.sql`
- Safe heredoc for multi-statement SQL / `DO $$`:
  - `DB_PROJECT_ROOT=/path/to/repo DB_PROFILE=local ./scripts/postgres query run <<'SQL'`
  - `select now();`
  - `SQL`
- Connection test:
  - `DB_PROJECT_ROOT=/path/to/repo DB_PROFILE=local ./scripts/postgres profile test`
- Schema introspection:
  - `DB_PROJECT_ROOT=/path/to/repo DB_PROFILE=local ./scripts/postgres schema inspect`
- Object search:
  - `DB_PROJECT_ROOT=/path/to/repo DB_PROFILE=local ./scripts/postgres query find users --types table,column`
- Release a pending migration file:
  - `DB_PROJECT_ROOT=/path/to/repo DB_PROFILE=local ./scripts/postgres migration release --summary "Add agent-context prompt sections"`

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
   - If the user explicitly asks to create or refresh a saved profile, use
     `./scripts/postgres profile bootstrap`.
2) Choose action:
   - Query / inspect data
   - Inspect schema / indexes / roles / activity
   - Review query shape or schema design
   - Draft or release migrations
   - Search official PostgreSQL docs only when explicitly requested
3) Execute and report:
   - Return the answer first, then only the supporting context needed to trust
     it.
   - Be explicit when an operation uses managed PostgreSQL client tools for
     dump / restore / diff behavior.
4) Persist only if asked:
   - Update `config.toml` only with explicit user approval, except canonical
     config migration plus explicit profile bootstrap / `set-ssl` flows.
   - Treat `<project-root>/.skills/postgres/config.toml` as local persisted
     operator config; consuming repos should gitignore it just as they
     previously gitignored legacy `postgres.toml`.

## Command map

- `doctor`
  - Validate config resolution, runtime readiness, and managed-tools status.
- `profile resolve`
  - Show the active URL / profile / source.
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
  - Execute SQL from `-c`, `-f`, or stdin.
- `query explain`
  - Run `EXPLAIN`, defaulting to `ANALYZE`.
- `query find <pattern> [--types ...]`
  - Search schemas / tables / columns / functions by name.
- `activity overview|locks|slow|long-running|cancel|terminate|cancel-pid|terminate-pid|pg-stat-top`
  - Runtime diagnostics and query-control operations.
- `schema inspect|diff|dump|table-sizes|index-health|missing-fk-indexes|vacuum-status|roles`
  - Schema and catalog inspection.
- `dump schema|data|restore`
  - Dump or restore schema / data.
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
- Do not persist `pg_bin_dir`, `pg_bin_path`, or `python_bin`.
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
  - missing composite indexes matching real join/filter predicates
- Validate with schema/catalog inspection first (`schema inspect`,
  `schema table-sizes`, `schema index-health`, `activity slow`) before asking
  for live benchmarking.

## SQL safety

- Prefer `query run` with heredoc or `-f` for multi-statement SQL.
- Do not inline `DO $$ ... $$` into double-quoted shell strings.

## Data-copy migrations

- When copying selected rows from dev/local into a production SQL file:
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
  lookup / verification.
- For migrations path resolution and schema-change workflow, follow
  `references/postgres_guardrails.md`.
- If a pending migration file contains its own `BEGIN` / `COMMIT`, do not wrap
  it in an outer rollback transaction during scratch validation.
- If the user explicitly marks a pending migration as migrated / released / run
  in production, perform `migration release` immediately unless they ask for a
  dry run only.
- Do not use this runtime skill to refresh best-practices references or
  otherwise upgrade the skill package itself.

## Guardrails

- Always ask for approval before making DDL changes.
- Keep pending changes in prerelease migration files and maintain a changelog.
- Use “pending migration file” / “released migration file” as the canonical
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

- Keep normal execution on `./scripts/postgres`.
- Treat `projects/postgres/Cargo.toml` as the single source of truth for the
  CLI semver, and use `./scripts/postgres --version` to verify the shipped
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
  - `./scripts/postgres --help`
  - `./scripts/postgres --version`
  - `DB_PROJECT_ROOT=/path/to/repo ./scripts/postgres --json doctor`
- Keep config migration one-way from legacy `postgres.toml` to canonical
  `config.toml`.
- Route dump / restore / schema diff through the managed PostgreSQL backend
  only. Do not restore PATH probing or persisted binary-dir config.

## Usage references

- Setup and runtime usage: `references/postgres_usage.md`
- Env var contract: `references/postgres_env.md`
- Config schema: `references/postgres_skill_schema.md`
- Migration guardrails: `references/postgres_guardrails.md`
- Design guidance: `references/postgres_best_practices/README.md`
- Local/Docker recovery: `references/postgres_local_recovery.md`
