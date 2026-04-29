---
name: Maintainer
description: Maintain and improve one or more skills or plugins in this repository with shared upgrade workflows and skill-specific refresh tasks.
---

# Maintainer

## Goal
Use this project-maintainer skill to maintain existing skills and plugins in this repository. Its primary job is to inspect one or more local packages, apply concrete docs, metadata, and workflow improvements, and keep repo-level maintainer docs aligned.
Treat maintenance as one unified task:
- repo-wide pass when the user invokes `$Maintainer` generically with a bare imperative such as `run` or `run your tasks`
- targeted maintenance when the user names one or more existing skills or plugins
- metadata-only maintenance when the user explicitly asks to align or sync docs/metadata

For the repo-wide pass, inspect the local skills and plugins, choose the ones with clear actionable drift, apply safe scoped upgrades, then run sync, audit, and release-style checks.
Treat domain-refresh work as explicit tasks, not default behavior. For brand-new skills, start with `$skill-creator`; this skill is for maintaining and integrating existing skill and plugin packages.

## User-facing Capability Summary
If the user asks what this skill can do, answer with these two capability groups:
1) Maintain one or more existing skills or plugins:
   - Inspect reusable and project-local skills for actionable drift.
   - Maintain targeted skills through `SKILL.md`, `agents/openai.yaml`, `references/*.md`, and directly coupled repo docs.
   - Compare and update local `SKILL.md`, `agents/openai.yaml`, `README.md`, and `AGENTS.md` when drift is found.
   - Audit which skills are Codex-dependent versus portable and tighten runtime-tool wording where needed.
   - Run consistency checks and report `PASS`, `PASS (NOOP)`, or `FAIL`.
   - Keep repo-local plugin manifests, marketplace metadata, and coupled repo docs aligned when plugin layout or naming changes.
2) Run skill-specific maintainer workflows:
   - Refresh bundled Swift-DocC authored sources and validate the fast-path reference layer.
   - Refresh the bundled Swift API Design guideline source and validate the thin reference layer.
   - Review TanStack Intent coverage for `plugins/tanstack/`, update the macro-area umbrella plus `references/` layout when new first-party Intent surfaces appear, and refresh the local fetch-source mapping for current TanStack package or doc versions.
   - Keep regeneration mechanics and maintainer-only internals out of runtime skills.

## Available Tasks (User Menu)
When the user asks what this skill can do, offer this task list:
1) `maintain skills`
   - Inspect one or more skills or plugins, ensure there is no meaningful drift, and compare or update local `SKILL.md`, `agents/openai.yaml`, `.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json`, `README.md`, and `AGENTS.md` as needed.
   - With no named targets, default scope is all local skills and repo-local plugins in this repository.
   - With named targets, keep the pass targeted to those skills or plugins.
   - With explicit metadata/docs wording, stay in metadata-only alignment mode.
   - Finish with audit and release-style reporting when the scope is broader than metadata-only alignment.
2) `audit consistency`
   - Run structure, rules, and reference checks across the repo or the touched skills.
3) `audit codex dependencies`
   - Verify which skills are Codex-dependent versus portable, keep the repo inventory current, and ensure Codex-specific tools or filesystem contracts are named precisely.
4) `refresh swift-docc references`
   - Check the bundled Swift-DocC manifest, refresh the local `DocCDocumentation.docc` asset tree when stale, and validate or tighten the local `references/*.md` fast paths.
5) `refresh swift-api-design references`
   - Check the bundled Swift API Design manifest, refresh the local guideline source file when stale, and validate the local `references/*.md` routing layer.
6) `refresh tanstack intent coverage`
   - Review the current TanStack Intent registry and relevant TanStack package skill pages for `plugins/tanstack/`.
   - Update local plugin metadata, umbrella `SKILL.md` routing, `references/*.md` fast paths, and related docs only when newly shipped first-party Intent coverage materially changes the right guidance.
   - Use the current TanStack umbrella layout: macro-area bundled skills stay as the primary entrypoints, with dense domain slices living under each umbrella's `references/` folder and focused bundled skills remaining available for direct triggering.
   - Keep this task explicit; do not fold it into generic repo-wide maintenance.

## Trigger Rules
Use this skill when users ask to:
- Invoke `$Maintainer` generically to maintain existing skills or plugins in this repository
- Maintain, upgrade, sync, tighten, or clean up one or more existing skills or plugins
- Maintain, upgrade, sync, tighten, or clean up repo-local plugins or shared repo structure around skills and plugins
- Optimize skill docs, metadata, workflow clarity, or maintainability
- Run a proactive skill maintenance pass before release
- Sync `SKILL.md`, `agents/openai.yaml`, and repository docs for one or more skills
- Audit which skills are Codex-dependent versus portable, or tighten Codex-tool/runtime wording for those skills
- Refresh bundled Swift-DocC references and bundled source assets
- Refresh bundled Swift API Design source and thin reference routes
- Refresh TanStack Intent coverage for the local `plugins/tanstack/` plugin when upstream alpha coverage changes
- Refresh the TanStack plugin's umbrella-skill `references/` layout or upstream-version fetch guidance when official TanStack Router, Start, CLI, or Intent surfaces change
- Integrate a newly scaffolded skill or plugin into repo metadata after `$skill-creator` or `$plugin-creator` has already created the package

## Workflow
1) Route the request with `references/maintenance-router.md`.
2) For unified maintenance requests, let the router choose the internal mode:
   - repo-wide pass -> `references/run-maintenance.md`
   - targeted maintenance -> `references/skill-upgrade.md`
   - metadata-only alignment -> `references/metadata-sync.md`
3) For structure and rules checks, follow `references/doc-consistency.md`.
4) For Codex dependency audits and portability-boundary checks, follow `references/codex-dependency-audit.md`.
5) For Swift-DocC bundled-reference refresh, follow `references/swift-docc-refresh.md`.
6) For Swift API Design bundled-reference refresh, follow `references/swift-api-design-refresh.md`.
7) For TanStack Intent coverage refresh on `plugins/tanstack/`, follow `references/tanstack-intent-refresh.md`.
8) Before finishing, run `references/release-checklist.md` and report pass/fail with actionable findings.

## References

- `references/maintenance-router.md`: route the request to the correct maintenance workflow first.
- `references/run-maintenance.md`: use for proactive repo maintenance across one or more existing skills or plugins.
- `references/skill-upgrade.md`: use for scoped improvements to one or more existing skills or plugins.
- `references/metadata-sync.md`: use for `SKILL.md`, `agents/openai.yaml`, and repo-doc alignment.
- `references/doc-consistency.md`: use for repository-wide structure and policy checks.
- `references/codex-dependency-audit.md`: use for Codex-dependency classification, portability-boundary checks, and Codex-tool wording audits.
- `references/swift-docc-refresh.md`: use for maintainer-only Swift-DocC bundled-reference refresh work.
- `references/swift-docc-runbook.md`: canonical refresh and review procedure for the `swift-docc` skill.
- `references/swift-api-design-refresh.md`: use for maintainer-only Swift API Design bundled-reference refresh work.
- `references/swift-api-design-runbook.md`: canonical refresh and review procedure for the `swift-api-design` skill.
- `references/tanstack-intent-refresh.md`: use for maintainer-only review of new TanStack Intent coverage relevant to `plugins/tanstack/`.
- `references/release-checklist.md`: use at the end of mixed or multi-step maintenance tasks.

## Subagent Usage
- If the runtime exposes subagent tools and the user explicitly asks for delegation or parallel agent work, spawn multiple subagents for independent analysis slices or disjoint write scopes.
- Prefer explorer subagents for read-only inspection and worker subagents only when file ownership is clearly split.
- Good candidates for parallel delegation in this skill:
  - unified maintenance: split reusable skills, project-local skills, coupled repo-doc inspection, or metadata-only verification into disjoint analysis buckets.
  - `audit`: split metadata drift, README/install prompt drift, and script/reference or policy checks.
  - targeted maintenance: split target skill packages from directly coupled repo docs only when write scopes do not overlap.
- Keep routing, final edit integration, final severity/result synthesis, and final git verification in the main agent.

## Guardrails
- Keep this skill focused on maintaining existing skills and plugins in this repository.
- Prefer concrete skill-level improvements over neutral orchestration language.
- Do not infer `refresh` or new-skill creation from generic maintenance requests.
- Use `$skill-creator` first when the user wants to create a brand-new skill.
- Keep changes scoped to the selected or discovered skills.
- Only spawn subagents when delegation is explicitly allowed in the current run.
- If no meaningful updates are needed, return `PASS (NOOP)` and avoid persistent file edits.
