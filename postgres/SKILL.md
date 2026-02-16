---
name: postgres
description: Connect to Postgres databases, run queries/diagnostics, and search official PostgreSQL docs only when explicitly requested.
---

# Postgres

## Goal
Use this skill to connect to Postgres, run user-requested queries/diagnostics, and search official PostgreSQL docs only when explicitly requested.

## Workflow
1) Confirm connection source:
   - If `DB_URL` is provided, use it for a one-off connection unless the user asks to persist it.
   - Use only `DB_*` environment variables for this skill. Non-`DB_*` aliases (for example `PROJECT_ROOT`, `DATABASE_URL`, `PGHOST`) are unsupported.
   - Use `postgres.toml` when present; otherwise ask the user for the data required to create a profile.
   - If a `postgres.toml` is already present under the current repo/root at `.skills/postgres/postgres.toml`, treat that repo/root as the project root and proceed without prompting for `DB_PROJECT_ROOT`.
   - If not in a git repo, or if running outside the target project, set `DB_PROJECT_ROOT` explicitly.
   - When creating or loading `postgres.toml` and the target project is a git repo, verify `.skills/postgres/postgres.toml` is gitignored to avoid committing credentials.
   - If `postgres.toml` exists, **first** ensure it is at the latest schema version. Run `./scripts/migrate_toml_schema.sh` only when an older schema is found, and run it from the skill dir only if `DB_PROJECT_ROOT` is set.
2) Choose action:
   - Connect/run a query, inspect schema, or run a helper script.
   - For official PostgreSQL docs lookup, use `./scripts/search_postgres_docs.sh` only when the user explicitly asks for docs search/verification.
3) Execute and report:
   - Run the requested action and summarize results or errors.
   - If a connection test fails, run `./scripts/check_deps.sh` and/or `./scripts/connection_info.sh` to diagnose.
4) Persist only if asked:
   - Update TOML only with explicit user approval, except `[configuration].pg_bin_path` which may be auto-written when missing. `schema_version` is written by the migration helper. Prompt before changing an existing value.

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
- For migrations path resolution and schema-change workflow, follow the guardrails reference.

## Guardrails (summary)
- Always ask for approval before making any database structure change (DDL like CREATE/ALTER/DROP).
- Keep pending changes in prerelease migration files and maintain a changelog.
- Never touch any file or folder whose name ends with `released` (case-insensitive) inside the migrations folder.
- After any schema change, run the least expensive query that confirms the change.
- For full rules and migration workflow, read `references/postgres_guardrails.md` when doing schema changes.

## Common requests
- Check connection: `DB_PROFILE=local ./scripts/test_connection.sh`
- Postgres version: `DB_PROFILE=local ./scripts/pg_version.sh`
- Connection details: `DB_PROFILE=local ./scripts/connection_info.sh`
- Find objects by name: `DB_PROFILE=local ./scripts/find_objects.sh users`

## Usage references
- Setup, env defaults, and script catalog: `references/postgres_usage.md`
