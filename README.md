# Skills

This directory contains reusable skills and project maintainer skills—task-specific packages of instructions, resources, and optional scripts that help agents follow workflows reliably.

## Skills
- `ask-questions-if-underspecified/` — Clarify requirements before implementing when a request is underspecified or the user asks for clarification.
- `codex-changelog/` — Check the installed Codex CLI version and fetch/print the matching GitHub Releases changelog from `openai/codex/releases`.
- `github/` — Use the GitHub CLI (`gh`) for repository-scoped issue, pull request, workflow, release, and tag operations; default to the current git project unless another `owner/repo` is provided.
- `learn/` — Capture durable corrections or preferences and write confirmed learnings to `AGENTS.md` when the user sets lasting guidance.
- `postgres/` — Connect to Postgres databases, run queries/diagnostics, and search official PostgreSQL docs only when explicitly requested.

## Project Skills
- `.agents/skills/tools/` — Orchestrate maintenance, optimization, refactor, and upstream benchmark workflows for skills in this repository, including metadata/doc sync and consistency checks.
Project skills are repository-local and are not included in the reusable `skill-installer` prompts below.

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
