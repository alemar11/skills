# Maintenance Router

Use this file first to route maintenance requests to the right playbook.

## Request Types
- `run`: proactive maintenance pass across one or more existing skills
- `upgrade`: improve one or more existing skills' docs, metadata, or workflow clarity with minimal scope
- `sync`: align metadata and docs
- `codex-deps`: audit which skills are Codex-dependent versus portable and tighten Codex-tool/runtime wording
- `audit`: run consistency/release checks
- `refresh`: refresh domain best-practices content or bundled skill reference content

## Decision Tree
1. If the user invokes `$skills-maintainer` generically with a bare imperative such as `run`, `run your tasks`, or `do a maintenance pass` and does not name a task, classify as `run` and use `run-maintenance.md`.
   - Deterministic default flow:
     - inspect local skills
     - shortlist clear actionable drift
     - upgrade the selected skills
     - sync touched docs
     - audit consistency
     - finish with `release-checklist.md`
   - Do not infer `refresh` or new-skill creation.
2. If the user asks to upgrade, modernize, tighten, or improve one or more existing skills, classify as `upgrade` and use `skill-upgrade.md`.
3. If the user asks to align skill metadata, descriptions, or docs, classify as `sync` and use `metadata-sync.md`.
4. If the user asks which skills are Codex-dependent versus portable, or asks to verify that Codex-dependent skills explicitly use the right Codex tools/runtime contracts, classify as `codex-deps` and use `codex-dependency-audit.md`.
5. If the user asks for repo health, policy compliance, structure checks, or pre-release validation, classify as `audit` and use `doc-consistency.md` plus `release-checklist.md`.
6. If the user asks to refresh bundled Swift-DocC references, review the `swift-docc` manifest, or re-sync the local DocC asset tree against upstream, classify as `refresh` and use `swift-docc-refresh.md`.
7. If the user asks to refresh bundled Swift API Design references, review the `swift-api-design` manifest, or re-sync the local guideline source against upstream, classify as `refresh` and use `swift-api-design-refresh.md`.
8. If the user asks to create or bootstrap a brand-new skill, route skill creation through `$skill-creator` first. Return to this maintainer skill only for repo integration or follow-up maintenance after the scaffold exists.
9. If a request mixes categories, run in this deterministic order:
   - `run` or `upgrade` -> `run-maintenance.md` or `skill-upgrade.md`
   - `sync` -> `metadata-sync.md`
   - `codex-deps` -> `codex-dependency-audit.md`
   - `refresh` -> the specific routed refresh playbook (`swift-docc-refresh.md` or `swift-api-design-refresh.md`)
   - `audit` -> `doc-consistency.md`, then `release-checklist.md`
10. Always end with `release-checklist.md` for mixed or multi-step maintenance tasks.

## Task Isolation Rule
- Generic bare imperatives map only to `run`.
- Run only the routed task playbook unless the user explicitly requests a mixed workflow.
- Do not silently expand `run` into `refresh` or new-skill creation.
- Do not silently expand `upgrade` into repo-wide `refresh`.
- Do not silently expand `sync` into `audit` or `refresh`.

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
