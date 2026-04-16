# Postgres Usage

Use this reference for runtime setup and the canonical `./scripts/postgres`
command surface.

## Runtime model

- `./scripts/postgres` is the only supported runtime entrypoint.
- The CLI is implemented in Rust under `../src/`.
- Normal query / inspection paths use Rust-native PostgreSQL access.
- Dump / restore / schema-diff paths prefer local PostgreSQL client tools when
  available and otherwise bootstrap managed PostgreSQL binaries automatically.
- Homebrew is not the required setup path anymore.

## Prerequisites

- `./scripts/postgres` must exist as the shipped runtime artifact.
- A running target Postgres database is still required for live DB operations.
- Managed client-tools fallback needs outbound network access the first time it
  downloads PostgreSQL binaries.
- `cargo` and a recent Rust toolchain are only required when maintaining or
  rebuilding the shipped artifact from `../src/`.

## Start here

Doctor:
```sh
DB_PROJECT_ROOT=/path/to/project ./scripts/postgres --json doctor
```

Bootstrap and save a profile:
```sh
DB_PROJECT_ROOT=/path/to/project ./scripts/postgres profile bootstrap --save
```

Resolve the active connection:
```sh
DB_PROJECT_ROOT=/path/to/project DB_PROFILE=local \
  ./scripts/postgres --json profile resolve
```

Run ad-hoc SQL:
```sh
DB_PROJECT_ROOT=/path/to/project DB_PROFILE=local \
  ./scripts/postgres query run -c "select now();"
```

Run SQL from a file:
```sh
DB_PROJECT_ROOT=/path/to/project DB_PROFILE=local \
  ./scripts/postgres query run -f ./query.sql
```

Safe heredoc:
```sh
DB_PROJECT_ROOT=/path/to/project DB_PROFILE=local \
  ./scripts/postgres query run <<'SQL'
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
  ./scripts/postgres profile test
```

Schema introspection:
```sh
DB_PROJECT_ROOT=/path/to/project DB_PROFILE=local \
  ./scripts/postgres schema inspect
```

Search schema objects:
```sh
DB_PROJECT_ROOT=/path/to/project DB_PROFILE=local \
  ./scripts/postgres query find user --types table,column,view
```

Release a pending migration:
```sh
DB_PROJECT_ROOT=/path/to/project DB_PROFILE=local \
  ./scripts/postgres migration release \
  --summary "Add agent-context prompt sections"
```

## JSON mode

Use `--json` whenever Codex will parse or chain the output.

Examples:
```sh
./scripts/postgres --json doctor
./scripts/postgres --json profile resolve
./scripts/postgres --json query run -c "select 1 as ok;"
./scripts/postgres --json schema table-sizes 20
```

Rules:

- JSON output goes to stdout only.
- Human diagnostics stay on stderr.
- Errors must remain machine-readable and must not leak credentials.
- Documentation examples below redact credential values for safety.

Contract:

- `doctor` returns a runtime-status object with `application_name`, `runtime`,
  and `managed_tools`.
- `profile` commands return profile- or connection-specific objects such as the
  resolved runtime context or `{ "status": "ok", ... }` for connection checks.
- `query` commands return query-specific objects such as
  `{ "query": "...", "result": { "columns": [...], "rows": [...] } }`.
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
    "sslmode": "disable",
    "toml_path": "/path/to/project/.skills/postgres/postgres.toml",
    "url": "postgresql://postgres:***@localhost:5432/app?sslmode=disable",
    "url_source": "toml"
  },
  "managed_tools": {
    "binary_dir": "/opt/homebrew/opt/postgresql@18/bin",
    "pg_dump": true,
    "pg_restore": true,
    "source": "local"
  }
}
```

Profile success:
```json
{
  "project_root": "/path/to/project",
  "toml_path": "/path/to/project/.skills/postgres/postgres.toml",
  "profile_name": "local",
  "url": "postgresql://postgres:***@localhost:5432/app?sslmode=disable",
  "sslmode": "disable",
  "url_source": "toml",
  "application_name": "codex-postgres-skill"
}
```

Query success:
```json
{
  "query": "select 1 as ok;",
  "result": {
    "columns": ["ok"],
    "rows": [{ "ok": "1" }]
  }
}
```

Schema success:
```json
{
  "table_sizes": {
    "columns": [
      "schemaname",
      "relname",
      "total_size",
      "table_size",
      "index_size"
    ],
    "rows": [
      {
        "schemaname": "public",
        "relname": "report_store_rs",
        "total_size": "1037 MB",
        "table_size": "963 MB",
        "index_size": "74 MB"
      }
    ]
  }
}
```

Error example:
```json
{
  "error": {
    "message": "Profile 'missing' not found in postgres.toml."
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
5. `<project-root>/.skills/postgres/postgres.toml`

Project-root precedence:

1. `--project-root`
2. `DB_PROJECT_ROOT`
3. current git top-level (unless that resolves to the skill repo itself)
4. current working directory

## Canonical commands

- `doctor`
  - Check config resolution and managed-tools readiness.
- `profile resolve`
  - Show active profile / URL / source.
- `profile bootstrap [--save]`
  - Interactively create or print a profile.
- `profile test`
  - Quick connection check.
- `profile info`
  - Print database, user, host, port, version, timezone, and app name.
- `profile version`
  - Show server version.
- `profile migrate-toml`
  - Normalize legacy TOML schema.
- `profile set-ssl <profile> <true|false>`
  - Persist `sslmode`.
- `query run`
  - Execute SQL from `-c`, `-f`, or stdin.
- `query explain`
  - Run `EXPLAIN`, defaulting to `ANALYZE`.
- `query find`
  - Search common schema objects by name.
- `activity overview|locks|slow|long-running|cancel|terminate|cancel-pid|terminate-pid|pg-stat-top`
  - Runtime diagnostics and query control.
- `schema inspect|diff|dump|table-sizes|index-health|missing-fk-indexes|vacuum-status|roles`
  - Schema and catalog inspection.
- `dump schema|data|restore`
  - Dump or restore schema / data payloads.
- `migration release`
  - Move a pending migration file into `released/` and update `CHANGELOG.md`.
- `docs search`
  - Search official PostgreSQL current docs.

## Managed PostgreSQL tools

For dump / restore / schema diff:

- If local `pg_dump` / `pg_restore` are available, the CLI uses them.
- Otherwise the CLI bootstraps managed PostgreSQL binaries under the skill
  directory or `DB_MANAGED_PG_DIR`.
- This is intentional: the runtime should not depend on `brew install
  postgresql`.

## Scratch validation guidance

Use scratch validation when you need end-to-end confidence for a pending
migration file before touching the real target DB.

- If the pending migration file already contains `BEGIN` / `COMMIT`, do not
  wrap it in an outer rollback transaction.
- Prefer a temporary clone database over wrapping the target DB in a
  rollback-only session.
- When reporting results, clearly separate:
  - real target DB operations run through `./scripts/postgres`
  - scratch validation steps against temporary databases

## References

- Env vars: `postgres_env.md`
- Config schema: `postgres_skill_schema.md`
- Migration guardrails: `postgres_guardrails.md`
- Design guidance: `postgres_best_practices/README.md`
