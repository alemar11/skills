---
name: github
description: Handle repo-scoped GitHub work plus authenticated-user star and star-list workflows inside the `gitstack` plugin. Prefer plain `gh` for straightforward reads and writes, and use the shared `ghflow` helpers when workflows need extra orchestration, shared JSON contracts, API-heavy behavior, or focused failing-PR CI triage.
---

# GitHub

## Overview

Use this as the umbrella GitHub skill inside the `gitstack` plugin.

Use `github` as the default GitHub surface when the request is mixed,
ambiguous, or already-pushed-branch lifecycle work.

Default command preference:

- plain `gh` for straightforward repo, issue, PR, and release operations
- plain `git` for local checkout state and branch operations
- shared `ghflow` helpers only when the job needs extra orchestration, shared
  JSON contracts, authenticated-user star or list GraphQL behavior, or the
  repo-aware publish helpers or focused CI inspector that multiple bundled
  skills reuse

`gitstack` bundles one shared helper runtime:

- `ghflow`

It also bundles focused routing skills that all reuse that helper:

- `github-triage`
- `github-reviews`
- `github-ci`
- `github-releases`

Keep `github` as the default for mixed or ambiguous requests, publish or
lifecycle work on already-pushed branches, or any time the user just says
"GitHub."

## Host prerequisites

- `git` and `gh` are required host dependencies for umbrella GitHub work in
  this plugin.
- Confirm both are on `PATH`:
  - `command -v git && git --version`
  - `command -v gh && gh --version`
- Confirm the authenticated GitHub session before writes:
  - `gh auth status`
- If either is missing, use `references/core/installation.md`.
- `ghflow --version` is the shared-helper version check.
- The maintained shared implementation lives under
  `<plugin-root>/projects/ghflow/src/ghflow/`.
- Specialist bundled skills are routing layers only; they do not own separate
  runtime copies.

## Domain routing

| Request type | Preferred skill |
| --- | --- |
| Mixed GitHub work, publish lifecycle, or ambiguous routing | `github` |
| Repo orientation, issues, PR metadata, authenticated-user stars or star lists, or raw cross-repo issue transfer | `github-triage` |
| Review follow-up, thread replies, review submission | `github-reviews` |
| PR checks and GitHub Actions investigation | `github-ci` |
| Release planning, notes, and publication with plain `git`/`gh` | `github-releases` |
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

## Command selection

Use direct commands first when they already express the job clearly:

- Repo or PR orientation:
  - `gh repo view --json nameWithOwner,description,defaultBranchRef,url`
  - `gh pr view <n> --repo <owner/repo> --json number,title,state,url`
- Issues:
  - `gh issue view <n> --repo <owner/repo>`
  - `gh issue create --repo <owner/repo> ...`
- Simple PR metadata edits:
  - `gh pr edit <n> --repo <owner/repo> ...`
- Release reads:
  - `gh release view <tag> --repo <owner/repo>`

Use `ghflow` when one of these applies:

- the workflow is reused across multiple bundled skills
- the job needs repo-aware publish context or PR open-or-reuse behavior
- the job needs normalized JSON output across subdomains
- the job needs authenticated-user star or list GraphQL behavior
- the job needs focused failing-PR CI inspection beyond a single direct `gh`
  status command
- the job needs review-thread routing or higher-level reply handling beyond
  plain `gh`

## Quick workflow

1. Ensure `git` and `gh` are installed; use
   `references/core/installation.md` if not.
2. Start with direct `gh` or `git` commands when they already fit the task.
3. When install or auth state is uncertain, confirm it directly with
   `command -v git`, `git --version`, `command -v gh`, `gh --version`, and
   `gh auth status`.
4. Use the narrowest shared helper only when the direct commands would require
   repeated shell glue, shared GraphQL flows, or normalized output shaping.
5. Prefer `--json` for `gh` or `ghflow` when parsing or relaying structured
   output.
6. Route full local-worktree publish to `yeet`, not to a new `github-publish`
   skill.

## Fast path

- Direct orientation:
  - `gh repo view --json nameWithOwner,description,defaultBranchRef,url`
  - `gh pr view <n> --repo <owner/repo> --json number,title,state,url`
- Direct mutation:
  - `gh issue create --repo <owner/repo> ...`
  - `gh pr edit <n> --repo <owner/repo> ...`
- Shared helper workflows:
  - `ghflow ci inspect --pr <number-or-url>`
  - `ghflow --json publish context`
  - `ghflow publish open --draft`
  - `ghflow --json stars list`
  - `ghflow --json stars lists list`
- Triage specialist:
  - `../github-triage/references/script-summary.md`
- Reviews specialist:
  - `../github-reviews/references/script-summary.md`
- CI specialist:
  - `../github-ci/references/script-summary.md`
- Releases specialist:
  - `../github-releases/references/script-summary.md`

## References navigation

- Start at `references/script-summary.md` for the shared `ghflow` entrypoint.
- Open `references/workflows.md` when you need the full umbrella runbook.
- For pure domain work, jump into the specialist skill references:
  - `../github-triage/references/`
  - `../github-reviews/references/`
  - `../github-ci/references/`
  - `../github-releases/references/`
- When authentication or retry behavior is uncertain, use
  `references/core/installation.md` and `references/core/failure-retries.md`.

## CLI Maintenance

- Keep normal execution on direct host binaries plus the shared plugin-owned
  helper artifact:
  - `git`
  - `gh`
  - `ghflow`
- Treat `<plugin-root>/projects/ghflow/` as the maintained Python project
  behind that artifact.
- Keep runtime logic in `<plugin-root>/projects/ghflow/src/ghflow/`.
- Keep skill docs sample-first around `git` and `gh`; use `ghflow` only for
  shared higher-level behavior such as failing-PR CI inspection, review-thread
  routing, stars, lists, and publish helpers.
- Do not add skill-local runtime copies under bundled GitHub skills.
- Do not add compatibility aliases or reintroduce public per-domain script
  entrypoints.
- Re-verify through the shipped artifact with:
  - `git --version`
  - `gh --version`
  - `gh auth status`
  - `ghflow --help`
  - `ghflow --version`

## Examples

- "Summarize this repo and tell me what matters first."
- "Show me the open PRs for this repo and summarize which one needs attention."
- "Show me my starred repos."
- "Update the PR title and body without changing review state."
- "Open or reuse the PR for this already-pushed branch."
