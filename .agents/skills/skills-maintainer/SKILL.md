---
name: skills-maintainer
description: Maintain and improve one or more skills in this repository with shared upgrade workflows and skill-specific refresh tasks.
---

# Skills Maintainer

## Goal
Use this project-maintainer skill to maintain existing skills in this repository. Its primary job is to inspect one or more local skills, apply concrete docs, metadata, and workflow improvements, and keep repo-level maintainer docs aligned.
When a user invokes `$skills-maintainer` with a bare imperative such as `run` or `run your tasks` and does not name a task or target, inspect the local skills, choose the ones with clear actionable drift, apply safe scoped upgrades, then run sync, audit, and release-style checks.
Treat benchmark and domain-refresh work as explicit tasks, not default behavior. For brand-new skills, start with `$skill-creator`; this skill is for maintaining and integrating existing skill packages.

## User-facing Capability Summary
If the user asks what this skill can do, answer with these three capability groups:
1) Maintain one or more existing skills:
   - Inspect reusable and project-local skills for actionable drift.
   - Upgrade targeted skills through `SKILL.md`, `agents/openai.yaml`, `references/*.md`, and directly coupled repo docs.
   - Keep `SKILL.md`, `agents/openai.yaml`, `README.md`, and `AGENTS.md` aligned.
   - Audit which skills are Codex-dependent versus portable and tighten runtime-tool wording where needed.
   - Run consistency checks and report `PASS`, `PASS (NOOP)`, or `FAIL`.
2) Run skill-specific maintainer workflows:
   - Refresh bundled Swift-DocC authored sources and validate the fast-path reference layer.
   - Refresh the bundled Swift API Design guideline source and validate the thin reference layer.
   - Keep regeneration mechanics and maintainer-only internals out of runtime skills.
3) Benchmark local skills against official OpenAI ecosystems when explicitly asked:
   - Download/update `openai/skills` and `openai/plugins`.
   - Study official patterns and propose meaningful structure improvements.
   - Use non-OpenAI repos only as optional comparison context.
   - Do not auto-apply benchmark proposals unless the user explicitly asks.

## Available Tasks (User Menu)
When the user asks what this skill can do, offer this task list:
1) `run`
   - Inspect one or more skills, choose the ones with clear actionable drift, and apply safe upgrades automatically.
   - If no skill names are given, default scope is all local skills in this repository.
   - Finish with sync, audit, and release-style reporting.
2) `upgrade skill`
   - Improve one or more named existing skills with deeper docs, metadata, or workflow changes while preserving intent.
3) `sync metadata/docs`
   - Align `SKILL.md`, `agents/openai.yaml`, `README.md`, and `AGENTS.md` for the targeted skills.
4) `audit consistency`
   - Run structure, rules, and reference checks across the repo or the touched skills.
5) `audit codex dependencies`
   - Verify which skills are Codex-dependent versus portable, keep the repo inventory current, and ensure Codex-specific tools or filesystem contracts are named precisely.
6) `refresh swift-docc references`
   - Check the bundled Swift-DocC manifest, refresh the local `DocCDocumentation.docc` asset tree when stale, and validate or tighten the local `references/*.md` fast paths.
7) `refresh swift-api-design references`
   - Check the bundled Swift API Design manifest, refresh the local guideline source file when stale, and validate the local `references/*.md` routing layer.
8) `benchmark against OpenAI`
   - Compare local skills against official OpenAI skill ecosystems and generate per-skill `CHANGE` or `NOOP` decisions.

## Trigger Rules
Use this skill when users ask to:
- Invoke `$skills-maintainer` generically to maintain existing skills in this repository
- Maintain, upgrade, tighten, or clean up one or more existing skills
- Optimize skill docs, metadata, workflow clarity, or maintainability
- Run a proactive skill maintenance pass before release
- Sync `SKILL.md`, `agents/openai.yaml`, and repository docs for one or more skills
- Audit which skills are Codex-dependent versus portable, or tighten Codex-tool/runtime wording for those skills
- Refresh bundled Swift-DocC references and bundled source assets
- Refresh bundled Swift API Design source and thin reference routes
- Benchmark local skills against official OpenAI skill ecosystems
- Integrate a newly scaffolded skill into repo metadata after `$skill-creator` has already created the package

## Workflow
1) Route the request with `references/maintenance-router.md`.
2) For proactive `run`, follow `references/run-maintenance.md`.
3) For targeted upgrades, follow `references/skill-upgrade.md`.
4) For metadata/docs alignment, follow `references/metadata-sync.md`.
5) For structure and rules checks, follow `references/doc-consistency.md`.
6) For Codex dependency audits and portability-boundary checks, follow `references/codex-dependency-audit.md`.
7) For upstream benchmarking and structure proposals, follow `references/openai-skill-benchmark.md`.
8) For Swift-DocC bundled-reference refresh, follow `references/swift-docc-refresh.md`.
9) For Swift API Design bundled-reference refresh, follow `references/swift-api-design-refresh.md`.
10) Before finishing, run `references/release-checklist.md` and report pass/fail with actionable findings.

## References

- `references/maintenance-router.md`: route the request to the correct maintenance workflow first.
- `references/run-maintenance.md`: use for proactive repo maintenance across one or more existing skills.
- `references/skill-upgrade.md`: use for scoped improvements to one or more existing skills.
- `references/metadata-sync.md`: use for `SKILL.md`, `agents/openai.yaml`, and repo-doc alignment.
- `references/doc-consistency.md`: use for repository-wide structure and policy checks.
- `references/codex-dependency-audit.md`: use for Codex-dependency classification, portability-boundary checks, and Codex-tool wording audits.
- `references/openai-skill-benchmark.md`: use for OpenAI-first benchmark analysis and proposal generation.
- `references/swift-docc-refresh.md`: use for maintainer-only Swift-DocC bundled-reference refresh work.
- `references/swift-docc-runbook.md`: canonical refresh and review procedure for the `swift-docc` skill.
- `references/swift-api-design-refresh.md`: use for maintainer-only Swift API Design bundled-reference refresh work.
- `references/swift-api-design-runbook.md`: canonical refresh and review procedure for the `swift-api-design` skill.
- `references/release-checklist.md`: use at the end of mixed or multi-step maintenance tasks.

## Subagent Usage
- If the runtime exposes subagent tools and the user explicitly asks for delegation or parallel agent work, spawn multiple subagents for independent analysis slices or disjoint write scopes.
- Prefer explorer subagents for read-only inspection and worker subagents only when file ownership is clearly split.
- Good candidates for parallel delegation in this skill:
  - `run`: split reusable skills, project-local skills, and coupled repo-doc inspection into disjoint analysis buckets.
  - `benchmark`: split upstream repo analysis or shard per-skill review after baseline artifacts exist.
  - `sync` / `audit`: split metadata drift, README/install prompt drift, and script/reference or policy checks.
  - `upgrade`: split target skill packages from directly coupled repo docs only when write scopes do not overlap.
- Keep routing, final edit integration, final severity/result synthesis, and final git verification in the main agent.

## Guardrails
- Keep this skill focused on maintaining existing skills in this repository.
- Prefer concrete skill-level improvements over neutral orchestration language.
- Do not infer `benchmark`, `refresh`, or new-skill creation from bare `run`.
- Use `$skill-creator` first when the user wants to create a brand-new skill.
- Keep changes scoped to the selected or discovered skills.
- Only spawn subagents when delegation is explicitly allowed in the current run.
- If no meaningful updates are needed, return `PASS (NOOP)` and avoid persistent file edits.
