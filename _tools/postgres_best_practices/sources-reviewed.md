# Sources Reviewed

This file records the source materials used to regenerate generic PostgreSQL best practices.

## Top 5 Skills Reviewed

1. `supabase/agent-skills/supabase-postgres-best-practices`
2. `wshobson/agents/postgresql-table-design`
3. `affaan-m/everything-claude-code/postgres-patterns`
4. `neondatabase/agent-skills/neon-postgres`
5. `jeffallan/claude-skills/postgres-pro`

## Files Accessed

- `SKILL.md` for each of the five skills above.
- Supabase references (rule files under `references/*.md`) for query, schema, security, locking, monitoring, data access, and advanced features.
- Jeffallan Postgres references:
  - `references/performance.md`
  - `references/maintenance.md`
  - `references/jsonb.md`
  - `references/extensions.md`
  - `references/replication.md`
- Neon references under `skills/neon-postgres/references/**/*.md` were reviewed and filtered for generic PostgreSQL rules only.

## What Was Intentionally Excluded

- Vendor product APIs/SDK setup flows.
- Provider-specific auth helpers and environment conventions.
- Prescriptive, fixed tuning values not universally valid.
- Rules that were primarily stylistic/opinionated without clear PostgreSQL basis.
