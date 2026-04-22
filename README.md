# Skills

This directory contains reusable skills, repo-local plugins, and project maintainer skills—task-specific packages of instructions, resources, and optional scripts that help agents follow workflows reliably.

## Plugins
- `plugins/gitstack/` — Preferred bundled install surface for linked git authoring, GitHub workflows, and Yeet around the shared `ghops` CLI, with host `gh` required for GitHub-backed operations.
  Bundled skills: `git-commit`, `github`, `github-triage`, `github-reviews`, `github-ci`, `github-releases`, `yeet`.
- `plugins/tanstack/` — Bundled TanStack React install surface for Query, Router, Start, and cross-stack integration guidance, biased toward current TanStack React APIs and official skill surfaces when available.
  Bundled skills: `tanstack-query`, `tanstack-router`, `tanstack-start`, `tanstack-integration`.

## Skills
- `skills/skill-cli-creator/` — Build host-aware embedded CLIs that live inside a skill or plugin, run from an owner-root-relative shipped artifact under `scripts/`, and can grow into a maintenance-only project at `projects/<tool>/`.
- `skills/codex-changelog/` — Check the installed Codex CLI and Codex App versions, then print CLI notes from `openai/codex/releases` and app notes from the OpenAI Codex changelog page.
- `skills/xcode-changelog/` — Resolve the active Xcode, look up a requested version, or list the available Apple Xcode release notes.
- `skills/plan-harder/` — Create a higher-rigor implementation plan with minimal high-signal clarification, a gotcha pass, and a saved `plans/<topic>-plan.md` output.
- `skills/learn/` — Capture durable corrections or preferences and write confirmed learnings only to `AGENTS.md` when the user sets lasting guidance.
- `skills/postgres/` — Connect to Postgres databases, run SQL and diagnostics, inspect schemas and migrations, review query performance, and use common PostGIS or pgvector patterns.
- `skills/skill-audit/` — Audit installed Codex skills, plugin packages, and bundled plugin skills using repo evidence, memory, sessions, and current context to plan updates, additions, merges, or disables.
- `skills/swift-api-design/` — Design or review Swift APIs using curated local summaries and a bundled upstream copy of the official Swift API Design Guidelines.
- `skills/swift-docc/` — Write, structure, review, and publish Swift-DocC documentation using curated local summaries and a bundled upstream DocC source tree.

## Project Skills
- `.agents/skills/Maintainer/` — Maintain and improve one or more skills or plugins in this repository with shared upgrade workflows and skill-specific refresh tasks.
Project skills are repository-local and are not included in the reusable install examples below.

## Codex

### Preferred Plugin Install
The preferred full-stack surface for linked git + GitHub workflows is the
repo-local `plugins/gitstack/` plugin, registered through
`.agents/plugins/marketplace.json`.

`plugins/gitstack/` expects GitHub CLI `gh` to be installed on the host before
GitHub-backed commands run. Use
`plugins/gitstack/skills/github/references/core/installation.md` for the
cross-platform install paths and `command -v gh && gh --version` to confirm the
binary is on `PATH`.

For TanStack React application work, install the repo-local `plugins/tanstack/`
plugin to get the bundled Query, Router, Start, and integration skills from one
surface instead of copying advice piecemeal from mixed community sources.

For a global local-plugin install from this repo, run `./link.sh`. It keeps
the existing skill symlink behavior, creates per-plugin symlinks under
`~/.agents/plugins/plugins/`, and merges this repo's plugin entries into
`~/.agents/plugins/marketplace.json` instead of replacing that personal
marketplace file. Each marketplace entry points directly at the symlinked
plugin path, which keeps the installed plugin paths live against this checkout.

### Install Reusable Skills With skill-installer (Codex-only)
These prompts are for use inside Codex only.
Copy/paste one of these prompts:

- `Use $skill-installer to install skills from alemar11/dotagents --path skills/skill-cli-creator skills/codex-changelog skills/xcode-changelog skills/plan-harder skills/learn skills/postgres skills/skill-audit skills/swift-api-design skills/swift-docc`
- `Use $skill-installer to install skills from alemar11/dotagents --path skills/skill-cli-creator`
- `Use $skill-installer to install skills from alemar11/dotagents --path skills/codex-changelog`
- `Use $skill-installer to install skills from alemar11/dotagents --path skills/xcode-changelog`
- `Use $skill-installer to install skills from alemar11/dotagents --path skills/plan-harder`
- `Use $skill-installer to install skills from alemar11/dotagents --path skills/learn`
- `Use $skill-installer to install skills from alemar11/dotagents --path skills/postgres`
- `Use $skill-installer to install skills from alemar11/dotagents --path skills/skill-audit`
- `Use $skill-installer to install skills from alemar11/dotagents --path skills/swift-api-design`
- `Use $skill-installer to install skills from alemar11/dotagents --path skills/swift-docc`

### Install With `npx skills` (Vercel Skills CLI)
These commands use the [`vercel-labs/skills`](https://github.com/vercel-labs/skills) CLI and target Codex directly.

List the skills available in this repository:

```sh
npx skills add alemar11/dotagents --list
```

Install all reusable skills globally for Codex:

```sh
npx skills add alemar11/dotagents -a codex -g -y \
  --skill skill-cli-creator \
  --skill codex-changelog \
  --skill xcode-changelog \
  --skill plan-harder \
  --skill learn \
  --skill postgres \
  --skill skill-audit \
  --skill swift-api-design \
  --skill swift-docc
```

Install an individual skill globally for Codex:

```sh
npx skills add alemar11/dotagents -a codex -g -y --skill skill-cli-creator
```

```sh
npx skills add alemar11/dotagents -a codex -g -y --skill xcode-changelog
```

```sh
npx skills add alemar11/dotagents -a codex -g -y --skill swift-api-design
```

```sh
npx skills add alemar11/dotagents -a codex -g -y --skill swift-docc
```

```sh
npx skills add alemar11/dotagents -a codex -g -y --skill plan-harder
```

Omit `-g` to install into the current project's `.agents/skills/` instead of your global `~/.codex/skills/`.
For linked git + GitHub workflows, install the bundled `plugins/gitstack/`
surface instead of looking for separate standalone `git-commit`, `github`, or
`yeet` skills in this repo.
The repository-local `Maintainer` skill is intentionally excluded from these commands.

Restart Codex to pick up new skills.
