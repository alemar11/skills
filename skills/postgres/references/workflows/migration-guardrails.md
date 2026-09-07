# Postgres Migration Guardrails

Use this reference when the task touches schema changes or migration release.
Use [../states.md](../states.md) for the canonical pending/released lifecycle
and derived migration outcome values.

## Core rules

- Apply DDL only with authorization for the operation and target database.
  Honor existing explicit authorization. Preparing a requested migration file
  is separate from applying it and needs no additional execution approval.
- Keep pending work in a pending migration file such as `prerelease.sql`.
- Before editing migrations, resolve the repo's exact `migrations_path` and
  pending migration filename by inspecting `.skills/postgres/config.toml` and
  the existing migration directory. Some repos use names such as
  `prerelease_cdr.sql` instead of the launcher default.
- If a `prerelease*.sql` file exists, use it for pending work instead of
  creating a timestamped migration file.
- Do not edit existing released SQL files.
- Do not create a new file under `released/` for pending work.
- Only move a pending migration into `released/` when the user explicitly
  confirms it has been migrated / released / run in production.
- After any schema change, run the least expensive validation query that proves
  the change landed.

## Schema evolution footguns

- `CREATE INDEX CONCURRENTLY` and `DROP INDEX CONCURRENTLY` cannot run inside a transaction block. If a repo's migration runner wraps every file in one transaction, use that repo's documented non-transactional migration path or ask before proceeding.
- Adding a column with a volatile default can rewrite or lock more data than expected on large tables. Prefer staged changes when the table is large or latency-sensitive.
- Changing a function signature can create an overload rather than replacing the old function. Drop or replace the intended signature explicitly and verify call sites.
- Dropping indexes, constraints, columns, tables, or partitions is destructive. Confirm the target object and the rollback path before applying the DDL.

## Canonical terms

- “pending migration file”
- “released migration file”

“SQL script” is fine for file format, but the workflow action is releasing a
migration.

## Release flow

Preferred command:

```sh
DB_PROJECT_ROOT=/path/to/project DB_PROFILE=local \
  /path/to/postgres-skill/scripts/postgres migration release \
  --summary "Add agent-context prompt sections"
```

For a repo with a non-default pending filename, pass it explicitly:

```sh
DB_PROJECT_ROOT=/path/to/project DB_PROFILE=local-cdr \
  /path/to/postgres-skill/scripts/postgres migration release \
  --pending-file prerelease_cdr.sql \
  --summary "Add CDR timestamp suffix columns"
```

Dry run:

```sh
DB_PROJECT_ROOT=/path/to/project DB_PROFILE=local \
  /path/to/postgres-skill/scripts/postgres migration release \
  --summary "Add agent-context prompt sections" \
  --dry-run
```

The command:

- resolves `migrations_path`
- moves the pending migration file into `released/`
- recreates an empty pending file
- updates `CHANGELOG.md`

## Changelog rules

- Keep top-level sections as:
  - `## WIP`
  - `## RELEASED`
- When releasing:
  - remove the matching pending subsection from `WIP`
  - add one short summary under `RELEASED`
- If the changelog is not already in `WIP` / `RELEASED` format, migrate it
  first.

## Filename rules

- Released filenames use `YYYYMMDDHHMMSS.sql`
- Add `_<slug>` only on same-second collision
- If still colliding, append `_01`, `_02`, and so on

## Verification References

- https://www.postgresql.org/docs/current/sql-createindex.html
- https://www.postgresql.org/docs/current/sql-dropindex.html
- https://www.postgresql.org/docs/current/ddl-alter.html
- https://www.postgresql.org/docs/current/xfunc-overload.html
