# Postgres Skill Environment Variables

This skill exposes a `DB_*`-only user-facing environment contract.

## Supported user-facing variables
- `DB_URL`
- `DB_PROFILE`
- `DB_PROJECT_ROOT`
- `DB_APPLICATION_NAME`
- `DB_STATEMENT_TIMEOUT_MS`
- `DB_LOCK_TIMEOUT_MS`
- `DB_AUTO_UPDATE_SSLMODE`
- `DB_RESOLVE_CACHE`
- `DB_RESOLVE_CACHE_MAX_ENTRIES`
- `DB_GITIGNORE_CHECK`
- `DB_SSL_RETRY`
- `DB_QUERY_TEXT_MAX_CHARS`
- `DB_TABLE_SIZES_SCHEMA`
- `DB_TABLE_SIZES_MIN_BYTES`
- `DB_FIND_OBJECT_TYPES`
- `DB_PROFILE_SCAN_MODE`
- `DB_CONFIRM`
- `DB_VIEW_DEF_TRUNC`
- `DB_FUNC_DEF_TRUNC`
- `DB_PROFILE_A`
- `DB_PROFILE_B`
- `DB_URL_A`
- `DB_URL_B`
- `DB_DOCS_SEARCH_URL`
- `DB_DOCS_SEARCH_MAX_TIME`
- `DB_MIGRATIONS_PATH` (for AGENTS.md guidance updates)

## Internal bridge variables
The skill may set PostgreSQL-native variables internally when invoking Postgres tools:
- `PGAPPNAME` (from `DB_APPLICATION_NAME`)
- `PGOPTIONS` (from timeout settings)

Do not set these as part of the public skill configuration contract.

## Removed aliases
These are intentionally unsupported and should be replaced:
- `PROJECT_ROOT` -> `DB_PROJECT_ROOT`
- `DATABASE_URL` -> `DB_URL`
- `POSTGRES_URL` -> `DB_URL`
- `POSTGRESQL_URL` -> `DB_URL`
- `PGHOST` -> `DB_URL`
- `PGPORT` -> `DB_URL`
- `PGDATABASE` -> `DB_URL`
- `PGUSER` -> `DB_URL`
- `PGPASSWORD` -> `DB_URL`
- `PGSSLMODE` -> `DB_URL`
- `DB_HOST` -> `DB_URL`
- `DB_PORT` -> `DB_URL`
- `DB_NAME` -> `DB_URL`
- `DB_DATABASE` -> `DB_URL`
- `DB_USER` -> `DB_URL`
- `DB_PASSWORD` -> `DB_URL`
- `PG_DOCS_SEARCH_URL` -> `DB_DOCS_SEARCH_URL`
- `PG_DOCS_SEARCH_MAX_TIME` -> `DB_DOCS_SEARCH_MAX_TIME`
