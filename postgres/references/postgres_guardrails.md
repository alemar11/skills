# Postgres Guardrails

Use this when making schema changes, migrations, or any potentially destructive DB operations.

## Guardrails
- Always ask for approval before making any database structure change (DDL like CREATE/ALTER/DROP).
- Keep pending changes in `<migrations_path>/prerelease.sql` (or ordered `1_prerelease.sql`, `2_prerelease.sql` if splitting is needed).
- Treat SQL files inside `<migrations_path>/released/` as immutable after release.
- Use "pending migration file" / "released migration file" as the canonical workflow terms. "SQL script" is fine for the file format, but the release flow operates on migration files.
- Maintain `<migrations_path>/CHANGELOG.md` with this template; if a legacy format is present, migrate it to this template before further updates:

```md
## WIP

### prerelease.sql
- <ongoing change>

## RELEASED

### YYYY-MM-DD — `<released_filename>.sql`
- <short summary>
```

- Keep detailed in-progress notes in `## WIP` under the active pending-file subsection.
- When a migration is released, remove its detailed notes from `## WIP` and add one short entry under `## RELEASED` (newest first).
- Whenever you modify pending migration file(s), update the matching `## WIP` subsection in `<migrations_path>/CHANGELOG.md`.

## Important rule for DB structure changes
After the change is approved and completed, ask where to save the migration SQL. Resolve `<migrations_path>` in this order:
1) `[database.<profile>].migrations_path`
2) `[migrations].path` from `postgres.toml`
3) `AGENTS.md` (`DB_MIGRATIONS_PATH`)
4) Default `<migrations_path>` at the project root

Prefer creating or updating the **latest pending** migration file when possible (the most recent migration that has not yet been released/applied), even if it touches multiple schema objects.
When a pending migration file already contains the object definition you are changing (e.g. a view/function/trigger), prefer updating that existing creation logic (e.g. `CREATE OR REPLACE ...`) instead of appending a second change later in the same file, unless the user asks otherwise.
If a single migration file becomes too complex, propose splitting it into meaningful, ordered files.
If the same view/table is changed multiple times on the same day across different migration files, check whether they should be compacted into a single file and ask the user. If approved, consolidate and remove the superseded migration files.

## Release workflow (when the user says a pending migration file was "migrated", "released", or "run in production")
Preferred helper:

```sh
DB_PROJECT_ROOT=/path/to/repo DB_PROFILE=local \
  ./scripts/release_migration.sh --summary "Add agent-context prompt sections"
```

The helper resolves `<migrations_path>`, picks the released filename, moves the pending migration file, recreates an empty pending file, and updates `CHANGELOG.md`. Use the manual steps below when the helper cannot be used cleanly.

1) Resolve `<migrations_path>` using the order above.
2) Identify the pending file to release (default `prerelease.sql`; use explicit project variants like `prerelease_cdr.sql` when applicable).
3) Ensure `<migrations_path>/released/` exists.
4) Generate UTC timestamp prefix: `YYYYMMDDHHMMSS`.
5) Pick filename using collision rules:
   - First choice: `released/YYYYMMDDHHMMSS.sql`
   - If that already exists, use `released/YYYYMMDDHHMMSS_<slug>.sql`
   - If that still exists, use `released/YYYYMMDDHHMMSS_<slug>_01.sql`, then `_02`, ...
6) Move pending SQL into the chosen released filename.
7) Recreate an empty pending file with the same name.
8) Update changelog:
   - Ensure `## WIP` + `## RELEASED` template is present (migrate legacy format if needed).
   - Remove released notes from the pending-file subsection in `## WIP`.
   - Add one concise entry at top of `## RELEASED`:
     - `### YYYY-MM-DD — \`<released_filename>.sql\``
     - `- <short summary>`
   - Keep `## RELEASED` newest-first.
   - Prefer an explicit summary, but the helper may derive one from the first bullet in the matching `## WIP` subsection when possible.

## Post-change verification
After any schema change, run the least expensive query that confirms the change (e.g., check `information_schema` or `pg_catalog` for views/tables/columns) to ensure the update matches expectations.
