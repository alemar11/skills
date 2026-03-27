---
name: tools
description: Orchestrate targeted skill upgrades, metadata/doc sync, consistency checks, and upstream benchmark workflows for skills in this repository.
---

# Tools

## Goal
Use this project-maintainer skill to keep skills aligned, healthy, and releasable. Primary maintainer outcome: improve local skill markdown quality (`SKILL.md` and `references/*.md`) through structured analysis and actionable optimization proposals. This skill orchestrates maintenance workflows; it does not replace domain skills.
When a user asks to "upgrade" a skill, treat that as a scoped request to improve the named skill's docs, metadata, and workflow clarity while preserving intent.
When a user invokes `$tools` generically with a bare imperative such as "run" or "run your tasks" and does not name a task, treat that as a safe mixed maintenance pass: `sync metadata/docs` -> `audit consistency` -> `references/release-checklist.md`.

## User-facing Capability Summary
If the user asks what this skill can do, answer with these three capability groups:
1) Maintain and upgrade local skills:
   - Upgrade an existing skill with scoped improvements to `SKILL.md`, `agents/openai.yaml`, `references/*.md`, and directly coupled repo docs.
   - Keep skill docs and metadata aligned (`SKILL.md`, `agents/openai.yaml`, `README.md`, `AGENTS.md`).
   - Run structure/consistency checks and flag issues.
   - Propose meaningful optimization/refactor updates and report PASS/FAIL.
2) Benchmark local skills against official OpenAI skill ecosystems first (`openai/skills` and `openai/plugins`) and propose meaningful structure improvements.
   - Download/update the OpenAI upstream repos into `.cache/upstream-skills/`.
   - Study official OpenAI `SKILL.md` structure patterns (frontmatter, sections, workflow/trigger clarity, and layout), including plugin skill packages under `plugins/*/skills/*`.
   - Audit local skills including hidden `.agents/skills/*`.
   - Generate markdown-focused optimization proposals for local skill docs (`SKILL.md`, `references/*.md`, and related maintainer docs) with no auto-applied refactors.
   - Use non-OpenAI repos only as optional comparison context when the user asks for a broader benchmark.
   - If subagents are available and the user explicitly requested parallel work, delegate repo-specific analysis or shard per-skill review across multiple subagents; keep artifact generation and final synthesis in the parent agent.
3) Bootstrap new skills:
   - Create skill scaffolds with required files and metadata assets.
   - Start by invoking `$skill-creator` to initialize the skill template and required metadata.
   - Align README/install prompts and maintainer metadata.
   - Run consistency and sync checks to avoid drift.

## Available Tasks (User Menu)
When the user asks what this skill can do, offer this task list:
If the user invokes `$tools` generically and does not name one of these tasks, default to `sync metadata/docs`, then `audit consistency`, and finish with `references/release-checklist.md`.
1) `upgrade skill`
   - Improve an existing skill's docs, metadata, and workflow clarity while preserving intent.
   - Run focused sync/audit checks for the touched skill and return `PASS`, `PASS (NOOP)`, or `FAIL`.
2) `sync metadata/docs`
   - Align `SKILL.md`, `agents/openai.yaml`, `README.md`, and `AGENTS.md`.
3) `audit consistency`
   - Run structure/rules checks across skills and report findings by severity.
4) `bootstrap skill`
   - Use `$skill-creator` to initialize the new skill scaffold, then add required files and run metadata/docs checks.
5) `refresh postgres references`
   - Execute Postgres best-practices refresh workflow defined in this skill references.
6) `benchmark against upstream`
   - Download/update `openai/skills` and `openai/plugins`, study official OpenAI `SKILL.md` patterns, compare local skills, and propose markdown optimization updates (no auto-apply).
   - Accept additional non-OpenAI repos only as optional comparison baselines when the user explicitly requests them.
   - After artifacts are generated, review local skills one by one and state whether each skill needs changes (`CHANGE`) or not (`NOOP`), with concrete proposals when needed.
   - If subagents are available and the user explicitly requested parallel work, split upstream analysis by repo or shard per-skill review, but keep the shared benchmark script run and final result merge centralized.

## Trigger rules
Use this skill when users ask to:
- Invoke `$tools` generically to run a maintenance pass without naming a more specific task
- Upgrade, modernize, or tighten an existing skill
- Maintain or clean up one or more skills
- Optimize one or more skills (quality, consistency, or maintainability)
- Refactor skill structure or instructions while preserving intent
- Bootstrap a new skill (reusable or maintainer)
- Benchmark local skills against official OpenAI skill ecosystems (for example `openai/skills` and `openai/plugins`), with optional comparison repos when explicitly requested
- Sync `SKILL.md`, `agents/openai.yaml`, and repository docs
- Run a maintenance pass before release
- Refresh Postgres best-practices references

## Workflow
1) Route the request with `references/maintenance-router.md`.
2) For targeted skill upgrades, follow `references/skill-upgrade.md`.
3) For metadata/docs alignment, follow `references/metadata-sync.md`.
4) For repository-wide structure and rules checks, follow `references/doc-consistency.md`.
5) For skill bootstrap, follow `references/skill_openai_metadata.md` then `references/metadata-sync.md`.
6) For upstream benchmarking and structure proposals, follow `references/openai-skill-benchmark.md` (clone/update the OpenAI upstream repos first, then analyze top-level and plugin-packaged skill artifacts and propose per-skill updates one by one).
7) For Postgres best-practices refresh, follow `references/postgres-refresh.md` (self-contained workflow in this skill).
8) Before finishing, run `references/release-checklist.md` and report pass/fail with actionable findings.

## Subagent Usage
- If the runtime exposes subagent tools and the user explicitly asks for delegation or parallel agent work, spawn multiple subagents for independent analysis slices or disjoint write scopes.
- Prefer explorer subagents for read-only inspection and worker subagents only when file ownership is clearly split.
- Good candidates for parallel delegation in this skill:
  - `benchmark`: one subagent per upstream repo and additional subagents for disjoint local-skill review buckets after baseline artifacts exist.
  - `sync` / `audit`: separate subagents for metadata drift, README/install prompt drift, and script/reference or policy checks.
  - `upgrade`: one subagent for the target skill package and one for directly coupled repo docs when those write scopes do not overlap.
- Keep routing, final edit integration, final severity/result synthesis, and final git verification in the main agent.

## Guardrails
- Keep this skill orchestration-only in v1.
- Prefer repeatable commands and documented checks in this skill before inventing ad-hoc flows.
- Do not depend on markdown guidance outside this skill's `references/` folder.
- Keep changes scoped to requested maintenance outcomes.
- Treat plain-language "upgrade" requests as targeted-skill work by default; do not silently escalate them into repo-wide benchmark or refresh flows.
- Treat generic bare imperatives like "run" as the default mixed maintenance pass only; do not infer `bootstrap`, `refresh`, or `benchmark` from them.
- Only spawn subagents when delegation is explicitly allowed in the current run; otherwise execute the same workflow locally.
- Keep task boundaries explicit: run only the requested task (`upgrade`, `sync`, `audit`, `bootstrap`, `refresh`, `benchmark`) unless the user requests a mixed flow.
- If no meaningful updates are needed, return `PASS (NOOP)` and avoid persistent file edits.
