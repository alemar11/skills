# Postgres Usage

Use this reference for runtime setup and the canonical `scripts/postgres`
command surface in the skill package.

## Runtime model

- The only supported runtime entrypoint is the shipped `scripts/postgres`
  artifact in the skill package.
- The CLI is implemented in Rust under `../projects/postgres/`.
- Runtime operations use direct PostgreSQL connections through the Rust client.
- The skill is intentionally scoped to connection resolution, SQL execution,
  schema and catalog inspection, diagnostics, and migration release flow.
- Dump, restore, export, and schema-diff workflows are intentionally out of
  scope for this runtime surface.
- Canonical persisted config lives at `<project-root>/.skills/postgres/config.toml`.

## Prerequisites

- The shipped CLI artifact must exist at `<postgres-skill-root>/scripts/postgres`.
- A running target Postgres database is still required for live DB operations.
- `cargo` and a recent Rust toolchain are only required when maintaining or
  rebuilding the shipped artifact from `../projects/postgres/`.

## Start here

Resolve the shipped CLI once and reuse it in the examples below:

```sh
POSTGRES_CLI=/path/to/postgres-skill/scripts/postgres
```

Doctor:

```sh
DB_PROJECT_ROOT=/path/to/project "$POSTGRES_CLI" --json doctor
```

Bootstrap and save a profile:

```sh
DB_PROJECT_ROOT=/path/to/project "$POSTGRES_CLI" profile bootstrap --save
```

Resolve the active connection:

```sh
DB_PROJECT_ROOT=/path/to/project DB_PROFILE=local \
  "$POSTGRES_CLI" --json profile resolve
```

Run ad-hoc SQL:

```sh
DB_PROJECT_ROOT=/path/to/project DB_PROFILE=local \
  "$POSTGRES_CLI" query run -c "select now();"
```

Run SQL from a file:

```sh
DB_PROJECT_ROOT=/path/to/project DB_PROFILE=local \
  "$POSTGRES_CLI" query run -f ./query.sql
```

Safe heredoc:

```sh
DB_PROJECT_ROOT=/path/to/project DB_PROFILE=local \
  "$POSTGRES_CLI" query run <<'SQL'
DO $$
BEGIN
  RAISE NOTICE 'ok';
END
$$;
SQL
```

Connection check:

```sh
DB_PROJECT_ROOT=/path/to/project DB_PROFILE=local \
  "$POSTGRES_CLI" profile test
```

Schema introspection:

```sh
DB_PROJECT_ROOT=/path/to/project DB_PROFILE=local \
  "$POSTGRES_CLI" schema inspect
```

Search schema objects:

```sh
DB_PROJECT_ROOT=/path/to/project DB_PROFILE=local \
  "$POSTGRES_CLI" query find user --types table,column,view
```

Release a pending migration:

```sh
DB_PROJECT_ROOT=/path/to/project DB_PROFILE=local \
  "$POSTGRES_CLI" migration release \
  --summary "Add agent-context prompt sections"
```

## JSON mode

Use `--json` whenever Codex will parse or chain the output.

Examples:

```sh
"$POSTGRES_CLI" --json doctor
"$POSTGRES_CLI" --json profile resolve
"$POSTGRES_CLI" --json query run -c "select 1 as ok;"
"$POSTGRES_CLI" --json schema table-sizes 20
```

Rules:

- JSON output goes to stdout only.
- Human diagnostics stay on stderr.
- Errors must remain machine-readable and must not leak credentials.
- Documentation examples below redact credential values for safety.

Contract:

- `doctor` returns `application_name` and `runtime`.
- `profile` commands return profile- or connection-specific objects such as the
  resolved runtime context or `{ "status": "ok", ... }` for connection checks.
- `query run` returns the submitted SQL plus a `statements` array, with one
  entry per completed SQL statement. Each entry includes `statement`,
  `row_count`, and `result`.
- Other `query` commands return query-specific objects such as
  `{ "matches": { "columns": [...], "rows": [...] } }`.
- `schema` commands return schema-specific objects keyed by the inspected
  result, such as `{ "table_sizes": { "columns": [...], "rows": [...] } }`.
- Under `--json`, failures return `{ "error": { "message": "..." } }` on
  stdout and exit non-zero.

Examples:

Doctor success:

```json
{
  "application_name": "codex-postgres-skill",
  "runtime": {
    "profile_name": "local",
    "project_root": "/path/to/project",
    "config_path": "/path/to/project/.skills/postgres/config.toml",
    "toml_path": "/path/to/project/.skills/postgres/config.toml",
    "sslmode": "disable",
    "url": "postgresql://postgres:***@localhost:5432/app?sslmode=disable",
    "url_source": "config"
  }
}
```

Profile success:

```json
{
  "project_root": "/path/to/project",
  "config_path": "/path/to/project/.skills/postgres/config.toml",
  "toml_path": "/path/to/project/.skills/postgres/config.toml",
  "profile_name": "local",
  "url": "postgresql://postgres:***@localhost:5432/app?sslmode=disable",
  "sslmode": "disable",
  "url_source": "config",
  "application_name": "codex-postgres-skill"
}
```

Query success:

```json
{
  "query": "select 1 as ok;",
  "statements": [
    {
      "statement": 1,
      "row_count": 1,
      "result": {
        "columns": ["ok"],
        "rows": [{ "ok": "1" }]
      }
    }
  ]
}
```

Error example:

```json
{
  "error": {
    "message": "Profile 'missing' not found in config.toml."
  }
}
```

## Connection precedence

The CLI resolves connections in this order:

1. `--url`
2. `DB_URL`
3. compatibility URL vars: `DATABASE_URL`, `POSTGRES_URL`, `POSTGRESQL_URL`
4. libpq vars: `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`,
   `PGSSLMODE`
5. `<project-root>/.skills/postgres/config.toml`
6. legacy `<project-root>/.skills/postgres/postgres.toml` as one-way migration
   input when canonical `config.toml` is absent

Project-root precedence:

1. `--project-root`
2. `DB_PROJECT_ROOT`
3. current git top-level unless that resolves to the skill repo itself
4. current working directory

## Canonical commands

- `doctor`
  - Check config resolution and runtime readiness without mutating config.
- `profile resolve`
  - Show active profile, URL, and source.
- `profile bootstrap [--save]`
  - Interactively create or print a profile.
- `profile test`
  - Quick connection check.
- `profile info`
  - Print database, user, host, port, version, timezone, and app name.
- `profile version`
  - Show server version.
- `profile migrate-toml`
  - Migrate legacy `postgres.toml` into canonical `config.toml` and update
    ignore coverage so `.skills/postgres/config.toml` stays untracked too.
- `profile set-ssl <profile> <true|false>`
  - Persist `sslmode`.
- `query run`
  - Execute SQL from `-c`, `-f`, or stdin, preserving per-statement results.
- `query explain`
  - Run `EXPLAIN`, defaulting to `ANALYZE`.
- `query find`
  - Search common schema objects by name.
- `activity overview|locks|slow|long-running|cancel|terminate|cancel-pid|terminate-pid|pg-stat-top`
  - Runtime diagnostics and query control.
- `schema inspect|table-sizes|index-health|missing-fk-indexes|vacuum-status|roles`
  - Schema and catalog inspection.
- `migration release`
  - Move a pending migration file into `released/` and update `CHANGELOG.md`.
- `docs search`
  - Search official PostgreSQL current docs.

## Scope boundary

- Use this skill for SQL execution, query review, catalog inspection, and
  migration workflow support.
- Keep backup, restore, export, and schema-diff operations outside this skill.
- When a request mixes both concerns, answer the Postgres-analysis part here and
  call out the operator workflow separately instead of widening the CLI again.

## Scratch validation guidance

Use scratch validation when you need end-to-end confidence for a pending
migration file before touching the real target DB.

- If the pending migration file already contains `BEGIN` or `COMMIT`, do not
  wrap it in an outer rollback transaction.
- Prefer a temporary clone database over wrapping the target DB in a
  rollback-only session.
- When reporting results, clearly separate:
  - real target DB operations run through the shipped `scripts/postgres`
    artifact
  - scratch validation steps against temporary databases

## References

- Env vars: `postgres_env.md`
- Config schema: `postgres_skill_schema.md`
- Migration guardrails: `postgres_guardrails.md`
- Design guidance: `postgres_best_practices/README.md`
