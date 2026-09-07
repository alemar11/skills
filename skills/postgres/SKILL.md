---
name: postgres
description: Inspect Postgres databases, design or run SQL, and manage migrations through the shipped Postgres CLI.
---

# Postgres

Use `<skill-root>/scripts/postgres` for application databases configured by
`.skills/postgres/config.toml` (legacy: `.skills/postgres/postgres.toml`).
Resolve the project and profile before connecting; verify database identity
before consequential queries and whenever the target changes. Ask for a target
only when configuration and the conversation leave it ambiguous.

Default remote access to read-only. Applying writes or DDL requires
authorization for that operation and database; an explicit request can supply
it. Preparing a requested local migration does not require another approval.
Before an unauthorized application, prepare the SQL and relevant verification
so the user can approve a concrete change. Local profile access guards do not
replace server roles, grants, or RLS.

## Routes

- Commands, connection setup, JSON: [runtime usage](references/runtime/usage.md).
- Config choices: [options](references/runtime/options.md) and
  [config schema](references/runtime/config-schema.md).
- Environment variables: [environment](references/runtime/environment.md).
- Inspection queries and database identity: [common workflows](references/workflows/common-workflows.md).
- Migration edits or release: [migration guardrails](references/workflows/migration-guardrails.md)
  and [states](references/states.md).
- Local connection recovery: [recovery](references/workflows/local-recovery.md).
- Schema, query, security, concurrency, or diagnostics design:
  [design map](references/design/README.md).
- Version-sensitive syntax: [SQL version router](references/sql/postgres-sql-versions.md).
- Foreign tables: [FDW versions](references/sql/postgres-fdw-versions.md).
- Extensions: read the matching guide for [PostGIS](references/extensions/postgis.md),
  [pgvector](references/extensions/pgvector.md), [pg_cron](references/extensions/pg-cron.md),
  [pgmq](references/extensions/pgmq.md), or [pg_durable](references/extensions/pg-durable.md).

Choose syntax supported by the oldest deployed major. If unknown, use portable
SQL or state the minimum version and fallback. Load full version catalogs only
for an upgrade comparison or a feature missing from the router; verify current
release status before relying on PostgreSQL 19.

Ordinary commands normalize config in memory; persist changes only through an
intended config-write command or documented opt-in. Use `--json doctor` for
runtime diagnosis. Dump, restore, export, and schema diff are outside this
launcher's coverage. Raw `psql` remains available for those operator workflows,
repo-documented container/smoke checks, an explicit user choice, or launcher
recovery; do not silently bypass the configured application profile.
