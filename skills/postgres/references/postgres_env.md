# Postgres Environment Contract

Use these environment variables with the shipped `scripts/postgres` artifact in
the skill package.

## Primary runtime vars

- `DB_PROJECT_ROOT`
  - Target project root containing `.skills/postgres/config.toml`.
- `DB_PROFILE`
  - Saved profile name from `config.toml`.
- `DB_URL`
  - One-off connection URL. Takes precedence over saved profiles.
- `DB_APPLICATION_NAME`
  - Session `application_name`. Default: `codex-postgres-skill`.
- `DB_STATEMENT_TIMEOUT_MS`
  - Session statement timeout.
- `DB_LOCK_TIMEOUT_MS`
  - Session lock timeout.
- `DB_AUTO_UPDATE_SSLMODE=1`
  - Auto-persist `sslmode=true` after a successful retry against a saved
    profile in canonical `config.toml`.
- `DB_PG_BIN_DIR`
  - Explicit host-tools override. Must contain executable `pg_dump` and
    `pg_restore` binaries.
- `DB_MANAGED_PG_DIR`
  - Override the managed PostgreSQL install root.
  - This is a raw path override; the CLI does not shell-expand `~` itself.
  - Default root:
    - Unix: `~/.cache/dotagents/skills/postgres/postgresql`
    - Windows: `%LOCALAPPDATA%\\dotagents\\skills\\postgres\\postgresql`

Resolved examples:

- macOS:
  - `~/.cache/dotagents/skills/postgres/postgresql`
- Linux:
  - `~/.cache/dotagents/skills/postgres/postgresql`
- Windows:
  - `%LOCALAPPDATA%\\dotagents\\skills\\postgres\\postgresql`

## Docs lookup

- `DB_DOCS_SEARCH_URL`
  - Override the PostgreSQL docs search endpoint. Default:
    `https://www.postgresql.org/search/`
- `DB_DOCS_SEARCH_MAX_TIME`
  - Max seconds for the docs search request. Default: `30`

## Compatibility inputs

These are accepted when `DB_URL` is absent:

- `DATABASE_URL`
- `POSTGRES_URL`
- `POSTGRESQL_URL`
- `PGHOST`
- `PGPORT`
- `PGDATABASE`
- `PGUSER`
- `PGPASSWORD`
- `PGSSLMODE`

## Unsupported

- `PROJECT_ROOT`
  - Use `DB_PROJECT_ROOT` instead.
- `PG_DOCS_SEARCH_URL`
  - Use `DB_DOCS_SEARCH_URL` instead.
- `PG_DOCS_SEARCH_MAX_TIME`
  - Use `DB_DOCS_SEARCH_MAX_TIME` instead.
