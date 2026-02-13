# Skills

This directory contains reusable skills—task-specific packages of instructions, resources, and optional scripts that help agents follow workflows reliably.

## Skills
- `ask-questions-if-underspecified/` — Clarify requirements before implementing when a request is underspecified.
- `codex-changelog/` — Show release notes for the installed Codex CLI version.
- `github/` — Use the GitHub CLI (`gh`) to manage repositories, issues, pull requests, and workflows.
- `learn/` — Capture durable corrections or preferences and write them to AGENTS.md.
- `postgres/` — Connect to Postgres, run queries/diagnostics, and lookup official docs on explicit request.

## Codex

### Install With skill-installer (Codex-only)
These prompts are for use inside Codex only.
Copy/paste one of these prompts:

- `Use $skill-installer to install skills from alemar11/skills --path ask-questions-if-underspecified codex-changelog github learn postgres`
- `Use $skill-installer to install skills from alemar11/skills --path github`
- `Use $skill-installer to install skills from alemar11/skills --path ask-questions-if-underspecified`
- `Use $skill-installer to install skills from alemar11/skills --path codex-changelog`
- `Use $skill-installer to install skills from alemar11/skills --path learn`
- `Use $skill-installer to install skills from alemar11/skills --path postgres`

Restart Codex to pick up new skills.
