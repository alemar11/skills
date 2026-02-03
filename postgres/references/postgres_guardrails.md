# Postgres Guardrails

Use this when making schema changes, migrations, or any potentially destructive DB operations.

## Guardrails
- Always ask for approval before making any database structure change (DDL like CREATE/ALTER/DROP).
- Keep pending changes in `<migrations_path>/prerelease.sql` (or ordered `1_prerelease.sql`, `2_prerelease.sql` if splitting is needed).
- Never touch any file or folder whose name ends with `released` (case-insensitive) inside the chosen migrations folder.
- Maintain `<migrations_path>/CHANGELOG.md` with dated entries; create it if missing and remove entries for released migrations.
- Whenever you modify prerelease migration file(s), update `<migrations_path>/CHANGELOG.md` with a dated entry for that change (every time).

## Important rule for DB structure changes
After the change is approved and completed, ask where to save the migration SQL. Resolve `<migrations_path>` in this order:
1) `[database.<profile>].migrations_path`
2) `[migrations].path` from `postgres.toml`
3) `AGENTS.md` (`DB_MIGRATIONS_PATH`)
4) Default `<migrations_path>` at the project root

Prefer creating or updating the **latest pending** migration file when possible (the most recent migration that has not yet been released/applied), even if it touches multiple schema objects.
If a single migration file becomes too complex, propose splitting it into meaningful, ordered files.
If the same view/table is changed multiple times on the same day across different migration files, check whether they should be compacted into a single file and ask the user. If approved, consolidate and remove the superseded migration files.

## Post-change verification
After any schema change, run the least expensive query that confirms the change (e.g., check `information_schema` or `pg_catalog` for views/tables/columns) to ensure the update matches expectations.
