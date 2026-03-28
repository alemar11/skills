# Postgres Skill Maintenance

Use this reference for maintainer-only upkeep of the `postgres` skill package.
It is not part of the runtime workflow for normal database tasks.

## When to use this
- A script is added, removed, renamed, or materially repurposed.
- Runtime behavior changes and the docs need to stay in sync.
- A maintainer is refreshing reference content or tightening guidance.
- The skill surface is drifting and needs a structure/docs pass.

## What to keep aligned
- `SKILL.md`
  - Keep workflow, trigger rules, and runtime boundaries accurate.
  - Keep the entrypoint scannable; avoid duplicating the same command catalog in multiple sections.
- `references/postgres_usage.md`
  - Update the script index when runtime scripts change.
  - Keep examples runnable and current.
- `references/postgres_env.md`
  - Add or remove env vars only when runtime behavior actually changes.
  - Keep preferred `DB_*` inputs, compatibility inputs, and unsupported aliases distinct.
- `references/postgres_guardrails.md`
  - Update only for durable schema-change workflow rules.
  - Do not mix general runtime guidance with temporary repo notes.
- `references/postgres_best_practices/*.md`
  - Keep these generic and PostgreSQL-first.
  - Add scope/version caveats when advice depends on server version, privileges, or deployment model.
- `scripts/`
  - Keep runtime helpers general-purpose where possible.
  - Avoid hidden install or config-write side effects in scripts that are sourced by other scripts.

## Script maintenance checklist
When a runtime script changes:
- Confirm the script name and help text still match its real behavior.
- Update `references/postgres_usage.md` if the script index, examples, or flags changed.
- Update `references/postgres_env.md` if the script adds or removes env inputs.
- Update `SKILL.md` only if the change affects user-facing workflow selection or guardrails.
- Prefer explicit runtime/maintainer boundaries rather than leaking maintainer notes into runtime docs.

## Validation checklist
- `bash -n postgres/scripts/*.sh`
- `python3 -m py_compile postgres/scripts/bootstrap_profile.py`
- `git diff --check -- <touched paths>`
- If connection-resolution behavior changed, smoke-test `resolve_db_url.sh` with:
  - `DB_URL`
  - URL aliases such as `DATABASE_URL`
  - libpq `PG*` connection vars
  - split `DB_HOST` / `DB_PORT` / `DB_NAME` / `DB_USER` / `DB_PASSWORD`

## Boundaries
- Keep migration-file workflow guidance in the existing project convention docs.
- Keep maintainer-only notes in maintainer references, not in runtime usage sections.
- If a request is about evolving the skill package itself rather than using Postgres, route it through maintainer docs first.
