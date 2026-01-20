# SKILL.toml Reference

Optional UI metadata for a skill. `SKILL.md` remains the required entrypoint for triggers and workflow.

## Minimal Interface
```toml
[interface]
display_name = "My Skill"
short_description = "One line shown in the UI."
icon_small = "assets/icon-32.png"
icon_large = "assets/icon-128.png"
brand_color = "#123456"
default_prompt = "You are a helpful specialist for this skill."
```

Notes:
- Icons must be relative paths under the skill's `assets/` directory.
- Keep `short_description` concise and user-facing; use `SKILL.md` for trigger wording.

## Where To Check For Updates
- Skill specification: `https://agentskills.io/specification`
- Codex skills docs: `https://developers.openai.com/codex/skills/`
- Codex repo changes: search for `SKILL.toml` or `interface` in recent commits/PRs.
