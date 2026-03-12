# Skills

This directory contains reusable skills and project maintainer skills—task-specific packages of instructions, resources, and optional scripts that help agents follow workflows reliably.

## Skills
- `commit/` — Create a well-formed git commit from current changes with rationale and summary when asked to commit, prepare a commit message, or finalize staged work.
- `ask-questions-if-underspecified/` — Clarify requirements before implementing when a request is underspecified or the user asks for clarification.
- `codex-changelog/` — Check the installed Codex CLI version and fetch/print the matching GitHub Releases changelog from `openai/codex/releases`.
- `github/` — Use the GitHub CLI (`gh`) for repository-scoped issue, pull request, workflow, release, and tag operations; default to the current git project unless another `owner/repo` is provided.
- `learn/` — Capture durable corrections or preferences and write confirmed learnings to `AGENTS.md` when the user sets lasting guidance.
- `postgres/` — Connect to Postgres databases, run queries/diagnostics, and search official PostgreSQL docs only when explicitly requested.

## Project Skills
- `.agents/skills/tools/` — Orchestrate maintenance, optimization, refactor, and upstream benchmark workflows for skills in this repository, including metadata/doc sync and consistency checks.
Project skills are repository-local and are not included in the reusable install examples below.

## Codex

### Install With skill-installer (Codex-only)
These prompts are for use inside Codex only.
Copy/paste one of these prompts:

- `Use $skill-installer to install skills from alemar11/skills --path commit ask-questions-if-underspecified codex-changelog github learn postgres`
- `Use $skill-installer to install skills from alemar11/skills --path github`
- `Use $skill-installer to install skills from alemar11/skills --path commit`
- `Use $skill-installer to install skills from alemar11/skills --path ask-questions-if-underspecified`
- `Use $skill-installer to install skills from alemar11/skills --path codex-changelog`
- `Use $skill-installer to install skills from alemar11/skills --path learn`
- `Use $skill-installer to install skills from alemar11/skills --path postgres`

### Install With `npx skills` (Vercel Skills CLI)
These commands use the [`vercel-labs/skills`](https://github.com/vercel-labs/skills) CLI and target Codex directly.

List the skills available in this repository:

```sh
npx skills add alemar11/skills --list
```

Install all reusable skills globally for Codex:

```sh
npx skills add alemar11/skills -a codex -g -y \
  --skill commit \
  --skill ask-questions-if-underspecified \
  --skill codex-changelog \
  --skill github \
  --skill learn \
  --skill postgres
```

Install a single skill globally for Codex:

```sh
npx skills add alemar11/skills -a codex -g -y --skill github
```

Omit `-g` to install into the current project's `.agents/skills/` instead of your global `~/.codex/skills/`.
The repository-local `tools` maintainer skill is intentionally excluded from these commands.

Restart Codex to pick up new skills.
