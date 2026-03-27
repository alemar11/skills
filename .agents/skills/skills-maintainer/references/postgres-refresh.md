# Postgres Refresh Playbook

Use this playbook when asked to refresh Postgres best-practices references.

## Routing Rule
- Keep Postgres regeneration mechanics outside the runtime `postgres` skill.
- Use `references/postgres-best-practices-runbook.md` as the canonical refresh procedure.
- This task is domain-refresh only; do not combine with sync/audit/benchmark logic unless the user explicitly asks for a mixed run.

## Execution Flow (Mandatory Order)
1. `syntax-check`: run `bash -n` on both scripts.
2. `snapshot`: run `./.agents/skills/skills-maintainer/scripts/postgres_best_practices_snapshot.sh <limit>`.
3. `review`: apply the meaningful-change gate to each category file.
4. `optional-edits`: update only files with semantic improvements.
5. `cleanup`: run `./.agents/skills/skills-maintainer/scripts/postgres_best_practices_cleanup.sh`.
6. `final-report`: use the release checklist report schema and mark `PASS (NOOP)` if no persistent edits were required.

## Read-only Evaluation Mode
When a read-only verification is requested:
- Run `syntax-check` as-is.
- Run `snapshot` with output directed to a temporary/untracked path under `.cache/`.
- Do not modify tracked Postgres reference files.
- Run cleanup in preview mode:
  - `./.agents/skills/skills-maintainer/scripts/postgres_best_practices_cleanup.sh --dry-run`
- Report whether full refresh execution would require tracked-file edits.

## Guardrails
- Do not introduce regeneration internals into `postgres/SKILL.md`.
- Keep recommendations generic to PostgreSQL and prefer official docs validation.
- Preserve existing `DB_*` user-facing environment contract.

## Deliverable
Report:
- Which runbook steps were executed
- Which `postgres/references/postgres_best_practices/*.md` files changed
- Why each change passed the meaningful-change gate
