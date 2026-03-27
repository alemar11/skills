# Postgres Best Practices Runbook

This runbook is the canonical procedure for refreshing Postgres best-practices references from within the `skills-maintainer` project skill.

## Hard Rule: Postgres Runtime Skill Unawareness
- The runtime `postgres` skill must remain unaware of regeneration internals.
- Keep regeneration mechanics in this `skills-maintainer` skill (`scripts/`, `references/`, `artifacts/`).
- The runtime `postgres` skill should only consume final content under `postgres/references/postgres_best_practices/`.

## Scope
- Refresh source snapshot artifacts under `.agents/skills/skills-maintainer/artifacts/`.
- Update best-practices category docs under `postgres/references/postgres_best_practices/`.
- Keep the procedure and maintainer evidence in this `skills-maintainer` skill.

## Temporary Data Policy
- Use `.agents/skills/skills-maintainer/artifacts/` for runbook artifacts.
- Use `.cache/` for transient downloads or scratch files.
- Treat both locations as temporary working areas; cleanup before final report unless explicitly asked to keep artifacts.

## Content Rules
- Keep guidance generic to PostgreSQL (no provider-specific lock-in).
- Prefer vendor-neutral SQL and operations patterns.
- Validate recommendations against official PostgreSQL docs where possible: `https://www.postgresql.org/docs/current/`.
- Update category files only when changes are meaningful:
  - Existing guidance is inaccurate/outdated/contradicted.
  - New evidence improves correctness, safety, or applicability.
  - A category is missing high-value guidance.
- Do not update files for non-meaningful changes alone:
  - Formatting-only edits.
  - Wording polish without semantic improvement.
  - Reordering equivalent points.

## Tooling
- Snapshot script: `./.agents/skills/skills-maintainer/scripts/postgres_best_practices_snapshot.sh`
- Cleanup script: `./.agents/skills/skills-maintainer/scripts/postgres_best_practices_cleanup.sh`
- Artifacts directory: `./.agents/skills/skills-maintainer/artifacts/`

## Prerequisites
- Run commands from repository root.
- Required tools: `bash`, `curl`, `python3`.

## Refresh Flow
1. Regenerate source snapshot:
   - `./.agents/skills/skills-maintainer/scripts/postgres_best_practices_snapshot.sh 5`
2. Review snapshot diff:
   - `git diff -- .agents/skills/skills-maintainer/artifacts/top-postgres-skills.md`
3. Re-evaluate and update only meaningful category files:
   - `query-performance.md`
   - `connection-management.md`
   - `security-rls.md`
   - `schema-design.md`
   - `concurrency-locking.md`
   - `data-access-patterns.md`
   - `monitoring-diagnostics.md`
   - `advanced-features.md`
4. If no meaningful changes are needed, leave `postgres/references/postgres_best_practices/` unchanged.
5. Optionally update maintainer evidence files under `./.agents/skills/skills-maintainer/artifacts/`:
   - `sources-reviewed.md`
   - `verification.md`
6. Ensure runtime skill docs stay clean:
   - `postgres/SKILL.md` references final best-practices content only.
   - `postgres/references/postgres_usage.md` does not include regeneration mechanics.
7. Optional cleanup preview:
   - `./.agents/skills/skills-maintainer/scripts/postgres_best_practices_cleanup.sh --dry-run`
8. Cleanup temporary artifacts:
   - `./.agents/skills/skills-maintainer/scripts/postgres_best_practices_cleanup.sh`
9. If `.cache/` was used, remove stale task-specific scratch files before completion.

## Validation
- Script syntax checks:
  - `bash -n .agents/skills/skills-maintainer/scripts/postgres_best_practices_snapshot.sh`
  - `bash -n .agents/skills/skills-maintainer/scripts/postgres_best_practices_cleanup.sh`
- Diff review:
  - `git diff -- .agents/skills/skills-maintainer/references/postgres-best-practices-runbook.md .agents/skills/skills-maintainer/scripts/postgres_best_practices_snapshot.sh .agents/skills/skills-maintainer/scripts/postgres_best_practices_cleanup.sh`

## Notes
- This runbook is self-contained within the `skills-maintainer` skill.
- `top-postgres-skills.md`, `sources-reviewed.md`, and `verification.md` are temporary artifacts and may be deleted after each refresh cycle.
