# Skills

This directory contains reusable skills and project maintainer skills—task-specific packages of instructions, resources, and optional scripts that help agents follow workflows reliably.

## Skills
- `git-commit/` — Create a well-formed git commit with rationale, explicit staging, and monorepo-safe scope.
- `ask-questions-if-underspecified/` — Clarify requirements before implementing when a request is underspecified or the user asks for clarification.
- `cli-creator/` — Create durable, composable CLIs for Codex from APIs, SDKs, curl traces, apps, or local scripts.
- `codex-changelog/` — Check the installed Codex CLI and Codex App versions, then print CLI notes from `openai/codex/releases` and app notes from the OpenAI Codex changelog page.
- `xcode-changelog/` — Resolve the active Xcode, look up a requested version, or list the available Apple Xcode release notes.
- `plan-hard/` — Create a higher-rigor implementation plan with deeper clarification, a gotcha pass, and a saved `plans/<topic>-plan.md` output.
- `github/` (`GitHub`) — Handle repo-scoped GitHub work plus authenticated-user stars and star lists across triage, reviews, CI, releases, and PR publish or lifecycle flows.
- `yeet/` (`Yeet`) — Orchestrate full publish from a local checkout by choosing branch strategy, using `git-commit` for commit discipline, pushing, and handing off to `github` for PR opening or reuse against the right base branch.
- `learn/` — Capture durable corrections or preferences and write confirmed learnings only to `AGENTS.md` when the user sets lasting guidance.
- `postgres/` — Connect to Postgres databases, design schemas and indexes, review SQL/query performance, and use common PostGIS or pgvector patterns.
- `skill-audit/` — Audit installed or user-specified Codex skills using repo evidence, memory, and current context to plan updates, merges, or disables.
- `swift-api-design/` — Design or review Swift APIs using curated local summaries and a bundled upstream copy of the official Swift API Design Guidelines.
- `swift-docc/` — Write, structure, review, and publish Swift-DocC documentation using curated local summaries and a bundled upstream DocC source tree.

## Skill Dependencies
- `yeet/` requires `git-commit/` and `github/` as companion skills for commit discipline and post-push PR handling.

## Project Skills
- `.agents/skills/skills-maintainer/` — Maintain and improve one or more skills in this repository with shared upgrade workflows and skill-specific refresh tasks.
Project skills are repository-local and are not included in the reusable install examples below.

## Codex

### Install With skill-installer (Codex-only)
These prompts are for use inside Codex only.
Copy/paste one of these prompts:

- `Use $skill-installer to install skills from alemar11/skills --path git-commit ask-questions-if-underspecified cli-creator codex-changelog xcode-changelog plan-hard github yeet learn postgres skill-audit swift-api-design swift-docc`
- `Use $skill-installer to install skills from alemar11/skills --path github`
- `Use $skill-installer to install skills from alemar11/skills --path git-commit github yeet`
- `Use $skill-installer to install skills from alemar11/skills --path git-commit`
- `Use $skill-installer to install skills from alemar11/skills --path ask-questions-if-underspecified`
- `Use $skill-installer to install skills from alemar11/skills --path cli-creator`
- `Use $skill-installer to install skills from alemar11/skills --path codex-changelog`
- `Use $skill-installer to install skills from alemar11/skills --path xcode-changelog`
- `Use $skill-installer to install skills from alemar11/skills --path plan-hard`
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
  --skill ask-questions-if-underspecified \
  --skill cli-creator \
  --skill codex-changelog \
  --skill xcode-changelog \
  --skill plan-hard \
  --skill github \
  --skill yeet \
  --skill learn \
  --skill postgres \
  --skill skill-audit \
  --skill swift-api-design \
  --skill swift-docc
```

Install the full GitHub publish stack globally for Codex:

```sh
npx skills add alemar11/skills -a codex -g -y \
  --skill git-commit \
  --skill github \
  --skill yeet
```

Breaking change: the GitHub runtime surface is now `github` plus `yeet`.
Install `github` for repo-scoped GitHub work plus authenticated-user stars and
star lists, and add `git-commit` plus
`yeet` when full local-worktree publish is needed.

Install an individual skill globally for Codex:

```sh
npx skills add alemar11/skills -a codex -g -y --skill cli-creator
```

```sh
npx skills add alemar11/skills -a codex -g -y --skill github
```

```sh
npx skills add alemar11/skills -a codex -g -y --skill xcode-changelog
```

```sh
npx skills add alemar11/skills -a codex -g -y --skill git-commit --skill github --skill yeet
```

```sh
npx skills add alemar11/skills -a codex -g -y --skill swift-api-design
```

```sh
npx skills add alemar11/skills -a codex -g -y --skill swift-docc
```

```sh
npx skills add alemar11/skills -a codex -g -y --skill plan-hard
```

Omit `-g` to install into the current project's `.agents/skills/` instead of your global `~/.codex/skills/`.
For GitHub workflows, install `github` for repo-scoped work plus
authenticated-user stars/lists and add
`git-commit + yeet` for full publish.
The repository-local `skills-maintainer` skill is intentionally excluded from these commands.

Restart Codex to pick up new skills.
