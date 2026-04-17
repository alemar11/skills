# Postgres Skill Learn

Use this reference when the runtime skill uncovers a repeated pattern that may
deserve promotion into a durable script, rule, or reference update.

## Promote to a script when
- The same SQL/inspection workflow is repeated across multiple sessions.
- The workflow is generic to PostgreSQL rather than tied to one application schema.
- Packaging it as a helper reduces quoting mistakes, safety risk, or repetitive setup.
- The script can expose a small, clear interface with predictable output.

## Promote to guardrails when
- The lesson is a safety rule for schema changes, destructive operations, or production-impacting actions.
- Missing the rule would create a real risk of data loss, bad migrations, or misleading behavior.
- The rule should apply broadly across runtime uses, not just one incident.

## Promote to best-practices references when
- The lesson is a reusable PostgreSQL design/performance recommendation.
- It belongs in a generic operator/developer reference rather than a narrow troubleshooting note.
- The advice can be stated with clear scope, trade-offs, and, when helpful, version/privilege caveats.

## Keep as maintainer-only guidance when
- The lesson is about package upkeep, doc sync, release hygiene, or repo conventions.
- The behavior is useful only for this skill’s maintenance workflow.
- It would distract runtime users from the core Postgres task flow.

## Keep out entirely when
- The pattern is app-specific, schema-specific, or too unstable to canonize yet.
- The workflow depends on one-off local environment quirks.
- The lesson is better captured in session memory until it proves durable.

## Packaging rules
- Prefer one focused helper over a large “do everything” script.
- Prefer extending an existing script only when the new behavior is a natural fit.
- Keep runtime scripts side-effect-light unless the side effect is the explicit purpose of the command.
- Document every promoted script in `references/postgres_usage.md`.
- Document any new env inputs in `references/postgres_env.md`.
- Update `SKILL.md` only when the promoted learning changes the runtime decision flow.
