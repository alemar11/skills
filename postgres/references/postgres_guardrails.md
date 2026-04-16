# Postgres Migration Guardrails

Use this reference when the task touches schema changes or migration release.

## Core rules

- Always ask for approval before making DDL changes.
- Keep pending work in a pending migration file such as `prerelease.sql`.
- Do not edit existing released SQL files.
- Do not create a new file under `released/` for pending work.
- Only move a pending migration into `released/` when the user explicitly
  confirms it has been migrated / released / run in production.
- After any schema change, run the least expensive validation query that proves
  the change landed.

## Canonical terms

- “pending migration file”
- “released migration file”

“SQL script” is fine for file format, but the workflow action is releasing a
migration.

## Release flow

Preferred command:

```sh
DB_PROJECT_ROOT=/path/to/project DB_PROFILE=local \
  ./scripts/postgres migration release \
  --summary "Add agent-context prompt sections"
```

Dry run:

```sh
DB_PROJECT_ROOT=/path/to/project DB_PROFILE=local \
  ./scripts/postgres migration release \
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
