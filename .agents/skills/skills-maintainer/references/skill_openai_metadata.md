# OpenAI Skill Metadata and Bootstrap Reference

This file is the bootstrap reference for the new-skill workflow.

## Skill Metadata (`agents/openai.yaml`)

Optional UI metadata for a skill. `SKILL.md` remains the required entrypoint for triggers and workflow. Metadata lives in `agents/openai.yaml` for every skill that exposes UI fields.

## Minimal Interface
```yaml
interface:
  display_name: "My Skill"
  short_description: "One line shown in the UI."
  icon_small: "assets/icon-32.png"
  icon_large: "assets/icon-128.png"
  brand_color: "#123456"
  default_prompt: "You are a helpful specialist for this skill."
```

Notes:
- Icons must be relative paths under the skill's `assets/` directory.
- Keep `short_description` concise and user-facing; use `SKILL.md` for trigger wording.

## Bootstrap a New Skill

When adding a reusable skill:
1. Start with `$skill-creator` to initialize the skill scaffold (recommended path and resources).
2. Create a top-level skill directory with a stable lowercase name (or `.agents/skills/` for maintainer skills).
3. Add `SKILL.md` with frontmatter `name` and `description`, plus purpose, workflow, and triggers.
4. Add `agents/openai.yaml` with the interface fields above (at minimum `display_name`, `short_description`, `default_prompt`).
5. Add optional supporting files as needed (`references/*.md`, `assets/`, `scripts/`).
6. Update top-level `README.md` and any installer guidance that lists this skill.
7. Update `AGENTS.md` only when the change adds new durable repository guidance.
8. Run `references/metadata-sync.md` and a focused check from `references/doc-consistency.md`.

For project maintainer skills, place the skill under `.agents/skills/` instead of the top level.

## Where To Check For Updates
- Skill specification: `https://agentskills.io/specification`
- Codex skills docs: `https://developers.openai.com/codex/skills/`
- Codex repo changes: search for `openai.yaml` or `interface` in recent commits/PRs.
