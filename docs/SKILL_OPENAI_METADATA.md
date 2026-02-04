# Skill Metadata (openai.yaml)

Optional UI metadata for a skill. `SKILL.md` remains the required entrypoint for triggers and workflow. Metadata now lives in `agents/openai.yaml`.

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

## Where To Check For Updates
- Skill specification: `https://agentskills.io/specification`
- Codex skills docs: `https://developers.openai.com/codex/skills/`
- Codex repo changes: search for `openai.yaml` or `interface` in recent commits/PRs.
