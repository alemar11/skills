# Maintenance Router

Use this file first to route maintenance requests to the right playbook.

## Request Types
- `default-maintenance`: safe mixed maintenance pass for generic tools invocations with no named task
- `upgrade`: improve an existing skill's docs/metadata/workflow clarity with minimal scope
- `sync`: align metadata and docs
- `bootstrap`: create a new skill scaffold
- `audit`: run consistency/release checks
- `refresh`: refresh domain best-practices content
- `benchmark`: compare local skills against upstream skill ecosystems and propose meaningful markdown/structure updates

## Decision Tree
1. If the user invokes `$tools` generically with a bare imperative such as `run`, `run your tasks`, or `do a maintenance pass` and does not name a task, classify as `default-maintenance` and run this deterministic mixed flow:
   - `sync` -> `metadata-sync.md`
   - `audit` -> `doc-consistency.md`, then `release-checklist.md`
   - Do not infer `bootstrap`, `refresh`, or `benchmark`.
2. If the user asks to upgrade, modernize, tighten, or improve an existing skill, classify as `upgrade` and use `skill-upgrade.md`.
3. If the user asks to align skill metadata, descriptions, or docs, classify as `sync` and use `metadata-sync.md`.
4. If the user asks to bootstrap a new skill, classify as `bootstrap` and use `skill_openai_metadata.md` then `metadata-sync.md`.
5. If the user asks for repo health, policy compliance, structure checks, or pre-release validation, classify as `audit` and use `doc-consistency.md` plus `release-checklist.md`.
6. If the user asks to refresh Postgres best-practices content, classify as `refresh` and use `postgres-refresh.md`.
7. If the user asks to benchmark local skills against upstream repos (for example `openai/skills`, `openai/plugins`, with optional comparison repos such as `anthropics/skills`), classify as `benchmark` and use `openai-skill-benchmark.md` (download/update the OpenAI upstream repos first, then analyze top-level and plugin-packaged `SKILL.md` patterns and propose markdown optimization changes).
8. If a request mixes categories, run in this deterministic order:
   - `sync` -> `metadata-sync.md`
   - `upgrade` -> `skill-upgrade.md`
   - `bootstrap` -> `skill_openai_metadata.md`, then `metadata-sync.md`
   - `refresh` -> `postgres-refresh.md`
   - `benchmark` -> `openai-skill-benchmark.md`
   - `audit` -> `doc-consistency.md`, then `release-checklist.md`
9. Always end with `release-checklist.md` for mixed or multi-step maintenance tasks.

## Task Isolation Rule
- Generic bare imperatives map only to `default-maintenance`.
- Run only the routed task playbook unless the user explicitly requests a mixed workflow.
- Do not silently expand `upgrade` into repo-wide `benchmark` or `refresh`.
- Do not silently expand `sync` into `audit`, `benchmark`, or `refresh`.

## Parallel Delegation Rule
- If subagent tools are available and the user explicitly asked for delegation or parallel agent work, spawn multiple subagents only after the request has been routed to a concrete playbook.
- Prefer explorer subagents for independent read-only inspections and worker subagents only when write ownership is clearly separated.
- Keep routing, playbook selection, final synthesis, and final report assembly in the main agent.

## Output Contract
For every routed workflow, report:
- Scope covered
- Checks executed
- Findings grouped by severity
- Exact files touched (if any)
- Any deferred work
- Use `release-checklist.md` final report fields (`Scope`, `Commands run`, `Files changed`, `Why changed`, `Result`).
