---
name: github
description: Handle repo-scoped GitHub work plus authenticated-user star and star-list workflows through the shared `ghops` CLI bundled in the `gitstack` plugin, with specialist bundled skills for triage, reviews, CI, and releases and `yeet` reserved for full local-worktree publish.
---

# GitHub

## Overview

Use this as the umbrella GitHub skill inside the `gitstack` plugin.

`gitstack` bundles one shared GitHub runtime:

- `ghops`

It also bundles focused routing skills that all reuse that same runtime:

- `github-triage`
- `github-reviews`
- `github-ci`
- `github-releases`

Keep `github` as the default for mixed or ambiguous requests, publish or
lifecycle work on already-pushed branches, or any time the user just says
"GitHub."

## Runtime surface

- Resolve the installed plugin root first, then run `ghops`.
- `ghops --version` is the runtime version check.
- `ghops --json doctor` is the runtime readiness check.
- The maintained runtime implementation lives under
  `<plugin-root>/projects/ghops/src/ghops/`.
- Specialist bundled skills are routing layers only; they do not own separate
  runtime copies.

## Domain routing

| Request type | Preferred skill |
| --- | --- |
| Mixed GitHub work, publish lifecycle, or ambiguous routing | `github` |
| Repo orientation, issues, PR metadata, reactions, stars, lists | `github-triage` |
| Review follow-up, replies, review submission | `github-reviews` |
| PR checks and generic Actions investigation | `github-ci` |
| Release planning, notes, and publication | `github-releases` |
| Full publish from local checkout to draft PR | `yeet` |

## Trigger rules

- Use for repository-scoped GitHub work in the current repository, an
  explicitly provided `owner/repo`, or authenticated-user star and star-list
  workflows.
- Stay in `github` for mixed-domain work and for PR publish or lifecycle work
  on already-pushed branches.
- Prefer the specialist bundled skills when the request is clearly focused on
  one domain slice.
- Route only full publish-from-worktree requests out to `yeet`.
- Reject or reroute organization-level or enterprise-level mutation requests.

## Quick workflow

1. Resolve the plugin-owned `ghops` artifact.
2. Start with `ghops --json doctor` when auth or repo context is uncertain.
3. Choose the narrowest `ghops` noun or verb for the task.
4. Prefer `--json` when parsing or relaying structured output.
5. Route full local-worktree publish to `yeet`, not to a new `github-publish`
   skill.

## Fast path

- Runtime readiness:
  - `ghops --json doctor`
- Mixed repo orientation:
  - `ghops repos view`
  - `ghops --json repos list --limit 20`
- Pull-request lifecycle on already-pushed branches:
  - `ghops --json publish context`
  - `ghops publish open --draft`
- Triage specialist:
  - `../github-triage/references/script-summary.md`
- Reviews specialist:
  - `../github-reviews/references/script-summary.md`
- CI specialist:
  - `../github-ci/references/script-summary.md`
- Releases specialist:
  - `../github-releases/references/script-summary.md`

## References navigation

- Start at `references/script-summary.md` for the shared `ghops` entrypoint.
- Open `references/workflows.md` when you need the full umbrella runbook.
- For pure domain work, jump into the specialist skill references:
  - `../github-triage/references/`
  - `../github-reviews/references/`
  - `../github-ci/references/`
  - `../github-releases/references/`
- When authentication or retry behavior is uncertain, use
  `references/core/installation.md` and `references/core/failure-retries.md`.

## CLI Maintenance

- Keep normal execution on the shared plugin-owned artifact:
  `ghops`.
- Treat `<plugin-root>/projects/ghops/` as the maintained Python project
  behind that artifact.
- Keep runtime logic in `<plugin-root>/projects/ghops/src/ghops/`.
- Do not add skill-local runtime copies under bundled GitHub skills.
- Do not add compatibility aliases or reintroduce public per-domain script
  entrypoints.
- Re-verify through the shipped artifact with:
  - `ghops --help`
  - `ghops --version`
  - `ghops --json doctor`

## Examples

- "Summarize this repo and tell me what matters first."
- "Show me the open PRs for this repo and summarize which one needs attention."
- "Show me my starred repos."
- "Update the PR title and body without changing review state."
- "Open or reuse the PR for this already-pushed branch."
