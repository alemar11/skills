# Repository Guidelines

## Overview
This repository hosts reusable Codex skills. Each skill lives in its own top-level directory and is documented by a `SKILL.md` entrypoint. Keep guidance lightweight and focused on building and evolving skills.

## How to Create a Skill
- Create a dedicated directory per skill with a clear, stable name.
- Add a `SKILL.md` that defines purpose, triggers, and the workflow to follow.
- Add a `SKILL.toml` with UI metadata for the skill.
- Use the specification at `https://agentskills.io/specification` and `https://developers.openai.com/codex/skills/` when creating new skills.
- Keep `README.md` updated with the current skill list and a one-line description for each.

## Git Commits
- If changes affect multiple skills, split them into separate, meaningful commits.

## Codex Learnings
- Keep README skill descriptions in sync with each skill's `SKILL.toml` `interface.short_description`.
