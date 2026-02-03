# Repository Guidelines

## Overview
This repository hosts reusable Codex skills. Each skill lives in its own top-level directory and is documented by a `SKILL.md` entrypoint. Keep guidance lightweight and focused on building and evolving skills.
Agent skills follow the specification at `https://agentskills.io/specification`.
Codex skills reference: `https://developers.openai.com/codex/skills/`.

## How to Create a Skill
- Create a dedicated directory per skill with a clear, stable name.
- Add a `SKILL.md` that defines purpose, triggers, and the workflow to follow.
- Add `agents/openai.yaml` with UI metadata for the skill.
- Use the specification at `https://agentskills.io/specification` and `https://developers.openai.com/codex/skills/` when creating new skills.
- Keep `README.md` updated with the current skill list and a one-line description for each.

## Git Commits
- If changes affect multiple skills, split them into separate, meaningful commits.

## Codex Learnings
### Global
- Keep README.md skill descriptions, list, and install prompts in sync with `agents/openai.yaml` and any skill adds/removes/renames.
- When new durable rules are discovered while creating or updating skills, add them to this AGENTS.md under the appropriate skill section.
- In `references/` folders, keep `.md` filenames lowercase except for `README.md` and `AGENTS.md`.
- If `brand_color` isn’t provided, pick a random hex color not already used by other skills in this repo and set it in `agents/openai.yaml`.

### Postgres skill
- Keep TOML schemas versioned: bump `[configuration].schema_version` in `postgres.toml.example`, update `postgres/references/postgres_skill_schema.md`, and add migrations for every prior version in `postgres/scripts/migrate_toml_schema.sh`.
- Treat missing `schema_version` as pre-1 and require migration; `pg_bin_path` is required and must point to a directory containing `psql` (migration fails if it cannot be determined).
- Keep `postgres.toml.example` as the canonical current schema; keep `postgres/SKILL.md` brief and link to the example + schema reference.
