# Skills

This directory contains reusable skills, repo-local plugins, and project maintainer skills—task-specific packages of instructions, resources, and optional scripts that help agents follow workflows reliably.

## Plugins
- `plugins/gitstack/` — Preferred bundled install surface for linked git authoring, GitHub workflows, and Yeet around the shared `ghops` CLI.
  Bundled skills: `git-commit`, `github`, `github-triage`, `github-reviews`, `github-ci`, `github-releases`, `yeet`.

## Skills
- `git-commit/` — Create a well-formed git commit with rationale, explicit staging, and monorepo-safe scope.
- `skill-cli-creator/` — Build host-aware embedded CLIs that live inside a skill or plugin, run from `scripts/`, and can grow into a maintenance-only project at `projects/<tool>/`.
- `codex-changelog/` — Check the installed Codex CLI and Codex App versions, then print CLI notes from `openai/codex/releases` and app notes from the OpenAI Codex changelog page.
- `xcode-changelog/` — Resolve the active Xcode, look up a requested version, or list the available Apple Xcode release notes.
- `plan-harder/` — Create a higher-rigor implementation plan with minimal high-signal clarification, a gotcha pass, and a saved `plans/<topic>-plan.md` output.
- `github/` (`GitHub`) — Handle repo-scoped GitHub work plus authenticated-user stars and star lists across triage, reviews, CI, releases, and PR publish or lifecycle flows.
- `yeet/` (`Yeet`) — Orchestrate full publish from a local checkout by choosing branch strategy, using `git-commit` for commit discipline, pushing, and handing off to `github` for PR opening or reuse against the right base branch.
- `learn/` — Capture durable corrections or preferences and write confirmed learnings only to `AGENTS.md` when the user sets lasting guidance.
- `postgres/` — Connect to Postgres databases, run SQL and diagnostics, inspect schemas and migrations, review query performance, and use common PostGIS or pgvector patterns.
- `skill-audit/` — Audit installed or user-specified Codex skills using repo evidence, memory, and current context to plan updates, merges, or disables.
- `swift-api-design/` — Design or review Swift APIs using curated local summaries and a bundled upstream copy of the official Swift API Design Guidelines.
- `swift-docc/` — Write, structure, review, and publish Swift-DocC documentation using curated local summaries and a bundled upstream DocC source tree.

## Skill Dependencies
- `yeet/` requires `git-commit/` and `github/` as companion skills for commit discipline and post-push PR handling.

## Project Skills
- `.agents/skills/skills-maintainer/` — Maintain and improve one or more skills in this repository with shared upgrade workflows and skill-specific refresh tasks.
Project skills are repository-local and are not included in the reusable install examples below.

## Codex

### Preferred Plugin Install
The preferred full-stack surface for linked git + GitHub workflows is the
repo-local `plugins/gitstack/` plugin, registered through
`.agents/plugins/marketplace.json`.

Use the standalone `git-commit`, `github`, and `yeet` skill installs below
only when you explicitly want the source-level standalone skills instead of the
bundled plugin.

### Install Standalone Skills With skill-installer (Codex-only)
These prompts are for use inside Codex only.
Copy/paste one of these prompts:

- `Use $skill-installer to install skills from alemar11/skills --path git-commit skill-cli-creator codex-changelog xcode-changelog plan-harder github yeet learn postgres skill-audit swift-api-design swift-docc`
- `Use $skill-installer to install skills from alemar11/skills --path skill-cli-creator`
- `Use $skill-installer to install skills from alemar11/skills --path codex-changelog`
- `Use $skill-installer to install skills from alemar11/skills --path xcode-changelog`
- `Use $skill-installer to install skills from alemar11/skills --path plan-harder`
- `Use $skill-installer to install skills from alemar11/skills --path learn`
- `Use $skill-installer to install skills from alemar11/skills --path postgres`
- `Use $skill-installer to install skills from alemar11/skills --path skill-audit`
- `Use $skill-installer to install skills from alemar11/skills --path swift-api-design`
- `Use $skill-installer to install skills from alemar11/skills --path swift-docc`

### Install With `npx skills` (Vercel Skills CLI)
These commands use the [`vercel-labs/skills`](https://github.com/vercel-labs/skills) CLI and target Codex directly.

List the skills available in this repository:

```sh
npx skills add alemar11/skills --list
```

Install all reusable skills globally for Codex:

```sh
npx skills add alemar11/skills -a codex -g -y \
  --skill git-commit \
  --skill skill-cli-creator \
  --skill codex-changelog \
  --skill xcode-changelog \
  --skill plan-harder \
  --skill github \
  --skill yeet \
  --skill learn \
  --skill postgres \
  --skill skill-audit \
  --skill swift-api-design \
  --skill swift-docc
```

Install an individual skill globally for Codex:

```sh
npx skills add alemar11/skills -a codex -g -y --skill skill-cli-creator
```

```sh
npx skills add alemar11/skills -a codex -g -y --skill xcode-changelog
```

```sh
npx skills add alemar11/skills -a codex -g -y --skill swift-api-design
```

```sh
npx skills add alemar11/skills -a codex -g -y --skill swift-docc
```

```sh
npx skills add alemar11/skills -a codex -g -y --skill plan-harder
```

Omit `-g` to install into the current project's `.agents/skills/` instead of your global `~/.codex/skills/`.
For linked git + GitHub workflows, prefer the bundled `plugins/gitstack/`
surface instead of assembling standalone `git-commit + github + yeet`.
The repository-local `skills-maintainer` skill is intentionally excluded from these commands.

Restart Codex to pick up new skills.
