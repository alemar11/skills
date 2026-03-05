# Maintenance Router

Use this file first to route maintenance requests to the right playbook.

## Request Types
- `sync`: align metadata and docs
- `audit`: run consistency/release checks
- `refresh`: refresh domain best-practices content
- `benchmark`: compare local skills against upstream skill ecosystems and propose meaningful markdown/structure updates

## Decision Tree
1. If the user asks to align skill metadata, descriptions, or docs, classify as `sync` and use `metadata-sync.md`.
2. If the user asks for repo health, policy compliance, structure checks, or pre-release validation, classify as `audit` and use `doc-consistency.md` plus `release-checklist.md`.
3. If the user asks to refresh Postgres best-practices content, classify as `refresh` and use `postgres-refresh.md`.
4. If the user asks to benchmark local skills against upstream repos (for example `openai/skills`, `anthropics/skills`), classify as `benchmark` and use `openai-skill-benchmark.md` (download/update upstream repos first, then analyze `SKILL.md` patterns and propose markdown optimization changes).
5. If a request mixes categories, run in this deterministic order:
   - `sync` -> `metadata-sync.md`
   - `refresh` -> `postgres-refresh.md`
   - `benchmark` -> `openai-skill-benchmark.md`
   - `audit` -> `doc-consistency.md`, then `release-checklist.md`
6. Always end with `release-checklist.md` for mixed or multi-step maintenance tasks.

## Output Contract
For every routed workflow, report:
- Scope covered
- Checks executed
- Findings grouped by severity
- Exact files touched (if any)
- Any deferred work
- Use `release-checklist.md` final report fields (`Scope`, `Commands run`, `Files changed`, `Why changed`, `Result`).
