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
- When new durable rules are discovered while creating or updating skills, add them to this AGENTS.md under the appropriate skill section.
- Use this section only as a fallback when no more appropriate section exists in AGENTS.md.
- In `references/` folders, keep `.md` filenames lowercase except for `README.md` and `AGENTS.md`.
- If `brand_color` isn’t provided, pick a random hex color not already used by other skills in this repo and set it in `agents/openai.yaml`.

### Postgres skill
- Keep Postgres runtime behavior and operator-facing rules in `postgres/SKILL.md` and `postgres/references/*` (not duplicated here).
- Keep best-practices regeneration orchestration in `.agents/skills/tools` and use `.agents/skills/tools/references/postgres-best-practices-runbook.md` as the canonical refresh procedure.
- If the user asks to upgrade or refresh Postgres best-practices docs, route through the `tools` skill workflow.

### Tools skill
- The `.agents/skills/tools` skill is the default orchestrator for maintenance, optimization, refactor, and upstream benchmark tasks affecting skills in this repository.
- Keep `tools` self-contained: workflow markdown guidance must live under `.agents/skills/tools/references/`.
- When updating skill metadata/docs across the repo, route through the `tools` playbooks and keep README/openai metadata text aligned.
