# Repository Guidelines

## Overview
This repository hosts reusable Codex skills and project maintainer skills. Reusable skills live in top-level directories, while project maintainer skills live under `.agents/skills/`. Every skill is documented by a `SKILL.md` entrypoint. Keep guidance lightweight and focused on building and evolving skills.
Agent skills follow the specification at `https://agentskills.io/specification`.
Codex skills reference: `https://developers.openai.com/codex/skills/`.

## How to Create a Skill
- Create a dedicated directory per skill with a clear, stable name.
- Place reusable skills at the repository top level; place project maintainer skills under `.agents/skills/<name>/`.
- Add a `SKILL.md` that defines purpose, triggers, and the workflow to follow.
- Add `agents/openai.yaml` with UI metadata for the skill.
- Use the specification at `https://agentskills.io/specification` and `https://developers.openai.com/codex/skills/` when creating new skills.
- Keep `README.md` updated with current reusable and project skill lists, with a one-line description for each.

## Git Commits
- If changes affect multiple skills, split them into separate, meaningful commits.

## Rules
- Keep README.md skill descriptions, list, and install prompts in sync with `agents/openai.yaml` and any skill adds/removes/renames.
- Keep a `Skill Dependencies` section in `README.md` only when one or more skills explicitly require loading other skills at runtime; list each such skill and the required companion skills, update the section when those requirements change, and remove or omit the section entirely when no such requirements exist.
- When new durable rules are discovered while creating or updating skills, add them to this AGENTS.md under the appropriate skill section.
- Use this section only as a fallback when no more appropriate section exists in AGENTS.md.
- In `references/` folders, keep `.md` filenames lowercase except for `README.md` and `AGENTS.md`.
- If `brand_color` isn’t provided, pick a random hex color not already used by other skills in this repo and set it in `agents/openai.yaml`.
- Runtime skills must stay unaware of `.agents/skills/skills-maintainer`: do not reference it, its runbooks, or maintainer-routing instructions from runtime `SKILL.md` files or runtime usage references. Keep that routing only in repo-level maintainer docs such as this `AGENTS.md`.
- Runtime skills may surface runtime learnings or durable guidance candidates, but they must not perform self-upgrade, metadata-sync, reference-refresh, or other repo-maintenance workflows from their own runtime instructions.
- Route skill-maintenance and repo-maintenance work through `.agents/skills/skills-maintainer` from repo-level maintainer docs, not from runtime `SKILL.md` files.

### Postgres skill
- Keep Postgres runtime behavior and operator-facing rules in `postgres/SKILL.md` and `postgres/references/*` (not duplicated here).
- The runtime `postgres` skill must not describe or perform self-upgrade, best-practices refresh, or other package-maintenance workflows. It may still expose runtime learnings that could later be promoted into durable runtime guidance.
- Keep best-practices regeneration orchestration in `.agents/skills/skills-maintainer` and use `.agents/skills/skills-maintainer/references/postgres-best-practices-runbook.md` as the canonical refresh procedure.
- Route maintainer-only Postgres best-practices refresh work through repo-level maintainer docs and the `skills-maintainer` skill workflow, not through runtime skill instructions.

### Swift-DocC skill
- Keep the runtime `swift-docc` skill focused on bundled authored content (`assets/DocCDocumentation.docc`), `references/*.md` fast paths, and manifest metadata only.
- The runtime `swift-docc` skill must not describe or perform self-upgrade, bundled asset refresh, or reference-layer maintenance workflows.
- Keep Swift-DocC bundled-asset refresh and reference integrity checks in `.agents/skills/skills-maintainer`, and use `.agents/skills/skills-maintainer/references/swift-docc-runbook.md` as the canonical procedure.
- Route maintainer-only Swift-DocC refresh work through repo-level maintainer docs and the `skills-maintainer` skill workflow, not through runtime skill instructions.
- Keep `swift-docc/references/*.md` biased toward thin, high-frequency task routes such as package API docs, async or stateful API docs, and local preview or render workflows. (Codex learning)

### Swift API Design skill
- Keep the runtime `swift-api-design` skill focused on the bundled upstream guideline source (`assets/api-design-guidelines.md`), `references/*.md` fast paths, and manifest metadata only.
- The runtime `swift-api-design` skill must not describe or perform self-upgrade, bundled asset refresh, or reference-layer maintenance workflows.
- Keep Swift API Design bundled-asset refresh and reference integrity checks in `.agents/skills/skills-maintainer`, and use `.agents/skills/skills-maintainer/references/swift-api-design-runbook.md` as the canonical procedure.
- Route maintainer-only Swift API Design refresh work through repo-level maintainer docs and the `skills-maintainer` skill workflow, not through runtime skill instructions.
- Refresh `swift-api-design` from `swiftlang/swift-org-website/documentation/api-design-guidelines/index.md` until the live Swift.org page demonstrably migrates to a different substantive source. (Codex learning)

### Plan Hard skill
- Keep the runtime `plan-hard` skill planning-only: it must create and refine plans, not implement the requested work. (Codex learning)
- By default, `plan-hard` must save generated plans inside `plans/` under the current working directory and create that directory if it does not exist. (Codex learning)

### Skills Maintainer skill
- The `.agents/skills/skills-maintainer` skill is the default maintainer for improving existing skills in this repository through shared upgrade tasks and skill-specific refresh workflows.
- `skills-maintainer` is the only maintainer skill that should orchestrate upgrades, metadata sync, reference refresh, and other repository maintenance for existing skills in this repository.
- Keep `skills-maintainer` self-contained: workflow markdown guidance must live under `.agents/skills/skills-maintainer/references/`.
- Keep the dependency direction one-way: runtime skills must not depend on, reference, or route users to `.agents/skills/skills-maintainer`; only repo-level maintainer docs may route work to `skills-maintainer`.
- When updating skill metadata/docs across the repo, route through the `skills-maintainer` playbooks and keep README/openai metadata text aligned.
- Treat plain-language "upgrade this skill" requests as targeted-skill maintenance first; only expand to repo-wide benchmark or refresh flows when the user asks for them explicitly.
- Treat generic `$skills-maintainer` imperatives like "run" or "run your tasks" as a proactive maintenance pass across existing skills: inspect the repo, choose skills with clear actionable drift, upgrade them, then run sync, audit, and `release-checklist.md`; do not infer new-skill creation, `refresh`, or `benchmark`. (Codex learning)
- For brand-new skill creation, use `$skill-creator` first; use `skills-maintainer` afterward only for repo integration or follow-up maintenance. (Codex learning)
- When delegation is explicitly requested and the runtime supports subagents, `skills-maintainer` may spawn multiple subagents only for independent analysis or disjoint write scopes; keep routing, final synthesis, and git verification in the main agent. (Codex learning)
- For `skills-maintainer` benchmark work, make official OpenAI skills the primary benchmark source: use `openai/skills` and `openai/plugins` by default, inspect plugin-packaged skills under `plugins/*/skills/*`, and treat non-OpenAI repos only as optional comparison baselines.

### Codex Changelog skill
- Split `codex-changelog` output into `Codex CLI` and `Codex App` sections when reporting release notes. (Codex learning)
- Always fetch Codex CLI notes from `openai/codex` GitHub releases, even if the OpenAI Codex changelog page also lists CLI entries. (Codex learning)
- Fetch Codex App notes from `https://developers.openai.com/codex/changelog` and match the installed desktop app version when possible. (Codex learning)

### GitHub skill
- Keep the runtime `github` skill as the umbrella entrypoint for repo triage, issue lifecycle, reactions, and PR metadata, and route specialist work to `github-reviews`, `github-ci`, `github-releases`, and `github-publish`.
- Treat the GitHub split as intentionally breaking: the supported install path for specialist GitHub workflows is the full suite (`github`, `github-reviews`, `github-ci`, `github-releases`, and `github-publish`).
- Do not reintroduce standalone `github` install prompts or `--skill github` / `--path github` examples while review, CI, release, and PR publish workflows remain companion-owned.
- Keep the runtime `github` skill self-owned and self-sufficient; do not require the upstream GitHub plugin for runtime routing or execution.
- Benchmark GitHub-skill parity work against the upstream `openai/plugins` GitHub bundle when useful, but keep runtime instructions and helper flows fully repo-local.
- Keep PR review follow-up guidance in `github-reviews/SKILL.md` and `github-reviews/references/*`, not in the umbrella docs. (Codex learning)
- Keep GitHub Actions investigation guidance in `github-ci/SKILL.md` and `github-ci/references/*`, not in the umbrella docs. (Codex learning)
- Keep release/tag guidance in `github-releases/SKILL.md` and `github-releases/references/*`, not in the umbrella docs. (Codex learning)
- Keep PR publish and lifecycle guidance in `github-publish/SKILL.md` and `github-publish/references/*`, not in the umbrella docs. (Codex learning)
- For release-backed tag creation in `github-releases`, resolve the repository default branch explicitly and surface the exact target SHA before mutation; do not hardcode `main`.
- For release creation in `github-releases`, standardize the notes choice as three options: infer from the last published release tag, keep blank, or use user-provided notes; recommend infer when the user leaves it unspecified.
- For tag-creation requests in `github-releases`, distinguish "release-backed tag" (`gh release create`) from "tag-only" (`git tag` / `gh api`) before choosing commands.
- For GitHub Actions investigations in `github-ci`, distinguish PR-associated failures from generic branch, SHA, workflow, schedule, manual, or explicit run-id runs; use `gh pr checks` only for PR-associated runs and prefer `gh run list` / `gh run view` otherwise.

### Learn skill
- Keep `learn` scoped to `AGENTS.md` writes only; do not instruct it to write `MEMORY.md`, `memory_summary.md`, or other memory files.
- When `learn` writes to `AGENTS.md`, place entries in the most appropriate existing section when possible, otherwise create a fitting section; use `## Codex Learnings` only as a fallback, and suffix each inserted bullet with ` (Codex learning)`.

### Skill Audit skill
- Keep `skill-audit` biased toward improving shared skills first, especially for broad reusable skills such as `postgres`.
- When a gap is project-specific but lightweight, prefer project docs, `AGENTS.md`, repo references, or memory over proposing a project-local specialization.
- Recommend a project-local specialization only as a last resort when the workflow is highly stable, repeatedly needed, and too project-specific to fit cleanly in the shared skill or repo docs.
- In full-portfolio audits, require `skill-audit` to ignore itself by default, propose suggestions for the other audited skills first, then ask the user whether they want a follow-up audit of `skill-audit` too.
- In user-targeted audits, require `skill-audit` to audit only the explicitly requested skills and ignore itself unless `skill-audit` was explicitly requested too.
