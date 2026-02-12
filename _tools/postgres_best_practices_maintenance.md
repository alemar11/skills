# Postgres Best Practices Maintenance

This runbook describes how to refresh and maintain the Postgres best-practices references without making the `postgres` skill aware of the maintenance tooling.

## Hard Rule: Postgres Skill Unawareness
- The `postgres` skill must remain unaware of best-practices maintenance internals.
- Do not reference maintenance scripts, source snapshots, verification artifacts, or maintenance flow from files under `postgres/`.
- Keep all maintenance mechanics and provenance artifacts under `/_tools/postgres_best_practices/` and this runbook.
- The skill should only consume final best-practices content files under `postgres/references/postgres_best_practices/`.

## Scope
- Snapshot source skills data into `/_tools/postgres_best_practices/top-postgres-skills.md`.
- Update best-practices content under `postgres/references/postgres_best_practices/`.
- Keep maintenance tooling only under `/_tools`.

## Content Rules
- Keep all recommendations generic to PostgreSQL; avoid vendor-opinionated guidance tied to specific managed providers or proprietary features.
- Prefer vendor-neutral SQL and operational patterns that apply broadly to PostgreSQL deployments.
- When a recommendation can be validated against official PostgreSQL documentation, do it and prefer that source.
- Official reference for checks: https://www.postgresql.org/docs/current/

## Tooling
- Snapshot script: `./_tools/postgres_best_practices_snapshot.sh`

## Refresh Flow
1. From repo root, regenerate the source snapshot:
   - `./_tools/postgres_best_practices_snapshot.sh 5`
2. Review the updated `/_tools/postgres_best_practices/top-postgres-skills.md`.
3. Re-evaluate and update category docs as needed:
   - `query-performance.md`
   - `connection-management.md`
   - `security-rls.md`
   - `schema-design.md`
   - `concurrency-locking.md`
   - `data-access-patterns.md`
   - `monitoring-diagnostics.md`
   - `advanced-features.md`
4. Update evidence files:
   - `/_tools/postgres_best_practices/sources-reviewed.md`
   - `/_tools/postgres_best_practices/verification.md`
   - Include official PostgreSQL docs references whenever available (`https://www.postgresql.org/docs/current/`).
5. Ensure skill-level docs do not reference maintenance scripts:
   - `postgres/SKILL.md` should only reference best-practices content.
   - `postgres/references/postgres_usage.md` should not list maintenance scripts.

## Notes
- Keep this runbook and maintenance scripts in `/_tools` only.
- Treat best-practices docs as consumable references for the skill; regeneration mechanics stay outside the skill.
