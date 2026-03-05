---
name: tools
description: Orchestrate maintenance, optimization, refactor, and upstream benchmark workflows for skills in this repository, including metadata/doc sync and consistency checks.
---

# Tools

## Goal
Use this project-maintainer skill to keep skills aligned, healthy, and releasable. Primary maintainer outcome: improve local skill markdown quality (`SKILL.md` and `references/*.md`) through structured analysis and actionable optimization proposals. This skill orchestrates maintenance workflows; it does not replace domain skills.

## User-facing Capability Summary
If the user asks what this skill can do, answer with these two capability groups:
1) Maintain local skills:
   - Keep skill docs and metadata aligned (`SKILL.md`, `agents/openai.yaml`, `README.md`, `AGENTS.md`).
   - Run structure/consistency checks and flag issues.
   - Propose meaningful optimization/refactor updates and report PASS/FAIL.
2) Benchmark local skills against upstream ecosystems (`openai/skills` and `anthropics/skills`) and propose meaningful structure improvements.
   - Download/update both upstream repos into `.cache/upstream-skills/`.
   - Study upstream `SKILL.md` structure patterns (frontmatter, sections, workflow/trigger clarity, and layout).
   - Audit local skills including hidden `.agents/skills/*`.
   - Generate markdown-focused optimization proposals for local skill docs (`SKILL.md`, `references/*.md`, and related maintainer docs) with no auto-applied refactors.

## Available Tasks (User Menu)
When the user asks what this skill can do, offer this task list:
1) `sync metadata/docs`
   - Align `SKILL.md`, `agents/openai.yaml`, `README.md`, and `AGENTS.md`.
2) `audit consistency`
   - Run structure/rules checks across skills and report findings by severity.
3) `refresh postgres references`
   - Execute Postgres best-practices refresh workflow defined in this skill references.
4) `benchmark against upstream`
   - Download/update `openai/skills` and `anthropics/skills`, study `SKILL.md` patterns, compare local skills, and propose markdown optimization updates (no auto-apply).

## Trigger rules
Use this skill when users ask to:
- Maintain or clean up one or more skills
- Optimize one or more skills (quality, consistency, or maintainability)
- Refactor skill structure or instructions while preserving intent
- Benchmark local skills against upstream skill ecosystems (for example `openai/skills` and `anthropics/skills`)
- Sync `SKILL.md`, `agents/openai.yaml`, and repository docs
- Run a maintenance pass before release
- Refresh Postgres best-practices references

## Workflow
1) Route the request with `references/maintenance-router.md`.
2) For metadata/docs alignment, follow `references/metadata-sync.md`.
3) For repository-wide structure and rules checks, follow `references/doc-consistency.md`.
4) For upstream benchmarking and structure proposals, follow `references/openai-skill-benchmark.md` (clone/update upstream repos first, then analyze and propose).
5) For Postgres best-practices refresh, follow `references/postgres-refresh.md` (self-contained workflow in this skill).
6) Before finishing, run `references/release-checklist.md` and report pass/fail with actionable findings.

## Guardrails
- Keep this skill orchestration-only in v1.
- Prefer repeatable commands and documented checks in this skill before inventing ad-hoc flows.
- Do not depend on markdown guidance outside this skill's `references/` folder.
- Keep changes scoped to requested maintenance outcomes.
- If no meaningful updates are needed, return `PASS (NOOP)` and avoid persistent file edits.
