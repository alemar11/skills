# Postgres Usage

Use this reference for runtime setup and the canonical `scripts/postgres`
command surface in the skill package.

## Runtime model

- The only supported runtime entrypoint is the shipped `scripts/postgres`
  launcher in the skill package.
- The launcher dispatches to platform-specific binaries in `scripts/bin/` using
  `postgres-<os>-<arch>` names.
- The CLI is implemented in Rust under `../projects/postgres/`.
- Runtime operations use direct PostgreSQL connections through the Rust client.
- The skill is intentionally scoped to connection resolution, SQL execution,
  schema and catalog inspection, diagnostics, and migration release flow.
- Dump, restore, export, and schema-diff workflows are intentionally out of
  scope for this runtime surface.
- Canonical persisted config lives at `<project-root>/.skills/postgres/config.toml`.

## Prerequisites

- The shipped CLI launcher must exist at `<postgres-skill-root>/scripts/postgres`.
- The current platform's Rust binary must exist and be executable under
  `<postgres-skill-root>/scripts/bin/`.
- A running target Postgres database is still required for live DB operations.
- `cargo` and a recent Rust toolchain are only required when maintaining or
  rebuilding shipped binaries from `../projects/postgres/`.
- Maintainers can install the current platform's binary with
  `projects/postgres/scripts/install-runtime-binary`; pass a Rust target triple
  such as `x86_64-unknown-linux-gnu` only when the matching cross toolchain is
  already configured.

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

Focused catalog and diagnostic commands:

```sh
DB_PROJECT_ROOT=/path/to/project DB_PROFILE=local \
  "$POSTGRES_CLI" profile overview

DB_PROJECT_ROOT=/path/to/project DB_PROFILE=local \
  "$POSTGRES_CLI" schema list tables

DB_PROJECT_ROOT=/path/to/project DB_PROFILE=local \
  "$POSTGRES_CLI" query plan -c "select * from public.users limit 10;"
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
    "ssl_mode": "disable",
    "access_mode": "read-write",
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
  "ssl_mode": "disable",
  "access_mode": "read-write",
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
6. legacy `<project-root>/.skills/postgres/postgres.toml` as a read-only
   compatibility input when canonical `config.toml` is absent; persist the
   canonical form only with `profile migrate-config`

Errors in a selected connection source stop resolution. For example, an invalid
`PGPORT` in a complete libpq environment does not fall back to a saved profile.

Project-root precedence:

1. `--project-root`
2. `DB_PROJECT_ROOT`
3. current git top-level unless that resolves to the skill repo itself
4. current working directory

## Access Modes

Profiles may declare `access_mode = "read"`, `access_mode = "write"`, or
`access_mode = "read-write"` under `[tools.postgres.profiles.<name>]`.

- Missing `access_mode` values are backward compatible and resolve to
  `read-write`.
- Loading a v1, `2.0.0`, or `2.1.0` config normalizes it to
  `schema_version = "3.0.0"` with explicit per-profile `access_mode` and
  `ssl_mode` values in memory. Health, inspection, query, dry-run, and other
  ordinary runtime paths never persist that normalization.
- `profile migrate-config` is the explicit config-migration write path. It
  creates a private pre-migration backup under the owner-scoped Postgres cache
  outside the consuming repository, writes and syncs it through a
  collision-free, descriptor-relative, no-follow `0600` file on Unix, then
  atomically persists canonical schema and option normalization. Relative,
  empty, parent-traversing, or project-local cache roots are ignored; migration
  stops if no safe absolute fallback exists. A no-change rerun performs no
  write.
- `[tools.postgres].access_mode` is allowed only as an inheritance/default
  source; prefer explicit per-profile values.
- `read` permits read-oriented profile, query, activity, and schema inspection
  commands, and rejects obvious write SQL or write-control commands.
- `write` permits write-oriented SQL/control operations and rejects read-only
  inspection commands, except neutral connection commands such as `doctor`,
  `profile resolve`, and `profile test`.
- Ambiguous SQL or SQL that mixes reads and writes requires `read-write`.
  Statement boundaries respect quoted strings, identifiers, dollar-quoted
  bodies, and comments; unrecognized or unterminated tokens are conservative.
- Access modes are CLI safety guards only. PostgreSQL roles, grants, RLS, and
  server-side read-only settings remain authoritative.

## Canonical commands

- `doctor`
  - Check config resolution and runtime readiness without creating, migrating,
    or rewriting config.
- `profile resolve`
  - Show active profile, URL, access mode, and source.
- `profile bootstrap [--save]`
  - Interactively create or print a profile.
- `profile test`
  - Quick connection check.
- `profile info`
  - Print database, user, host, port, version, timezone, and app name.
- `profile overview`
  - Summarize database identity, object counts, activity, and key settings.
- `profile settings autovacuum|memory`
  - Inspect focused PostgreSQL runtime settings.
- `profile version`
  - Show server version.
- `profile migrate-config`
  - Explicitly persist legacy `postgres.toml` or an older canonical schema as
    canonical `config.toml`; create a private backup under
    `~/.cache/dotagents/skills/postgres/config-backups/` (or
    `$XDG_CACHE_HOME`), write atomically, and update ignore coverage so
    `.skills/postgres/config.toml` stays untracked too.
- `profile set-ssl-mode <profile> <disable|require>`
  - Persist canonical `ssl_mode`.
- Hidden compatibility aliases: `profile migrate-toml` and
  `profile set-ssl <profile> <legacy-value>` remain accepted as input only.
- `query run`
  - Execute SQL from `-c`, `-f`, or stdin, preserving per-statement results.
- `query explain`
  - Run `EXPLAIN`, defaulting to `ANALYZE`.
- `query plan`
  - Return a non-executing JSON query plan by default; use `--analyze` to run
    `EXPLAIN ANALYZE`.
- `query find`
  - Search common schema objects by name.
- `activity overview|active-queries|locks|slow|long-running|cancel|terminate|cancel-pid|terminate-pid|pg-stat-top|replication-slots`
  - Runtime diagnostics and query control.
- `schema inspect|list|extensions|table-sizes|index-health|invalid-indexes|top-bloated-tables|missing-fk-indexes|vacuum-status|roles`
  - Schema and catalog inspection.
  - `schema list` supports `tables`, `views`, `schemas`, `triggers`,
    `indexes`, and `sequences`.
  - `schema extensions` supports `--installed` and `--available`; installed
    extensions are the default when neither flag is provided.
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

- Env vars: `environment.md`
- Config schema: `config-schema.md`
- Migration guardrails: `../workflows/migration-guardrails.md`
- Design guidance: `../design/README.md`
