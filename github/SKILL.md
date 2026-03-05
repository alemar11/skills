---
name: github
description: Use the GitHub CLI (`gh`) for repository-scoped issue, pull request, and workflow operations only. Default to the current git project unless another `owner/repo` is provided.
---

# GitHub CLI

## Trigger rules

- Use for repository-scoped GitHub operations via `gh` (issues, pull requests, workflow runs, and repo metadata).
- Default to the current repository unless the user explicitly provides another `owner/repo`.
- Reject or reroute organization-level or enterprise-level mutation requests.
- If a task does not require GitHub CLI operations, use a more direct non-`gh` workflow.

## Quick workflow

1. Determine project scope first.
   - If in a git repository: operate only on the current project unless explicitly asked to target another `owner/repo`.
   - If not in a git repository: pause and ask the user whether to:
     1) create a git repo first, or 2) proceed with non-project operations.
2. Enforce repository-only scope.
   - Allowed: repository-level read/write for issues, pull requests, runs, and repo labels.
   - Forbidden: organization-level or higher scope mutations (for example org settings, org rulesets, org membership, org secrets/variables, enterprise APIs).
   - If a request is forbidden, stop and ask for a repo-scoped alternative.
3. Run preflight before any `gh` action:
   - `scripts/preflight_gh.sh [--host github.com] [--min-version <version>]`
   - Use `--allow-non-project` only when the user explicitly requests a non-project operation.
4. Run the narrowest `gh` command needed, then report only relevant output.
5. If the operation fails, return the command error and propose the next retry command from the retry matrix below.

## Common operations

- Repository actions
  - `gh repo view` and `gh repo clone <owner>/<repo>`
- Issue actions
  - `gh issue list`, `gh issue view`, `gh issue create`, `gh issue edit`, `gh issue comment`, `gh issue close`
- Pull request actions
  - `gh pr list`, `gh pr view`, `gh pr create`, `gh pr edit`, `gh pr comment`, `gh pr review`, `gh pr checkout`, `gh pr merge`, `gh pr checks`
- Workflow actions
  - `gh run list`, `gh run view`, `gh run watch`
- General
  - `gh alias`, `gh api`, `gh extension`

Use `--help` on the relevant command for options, and prefer `--json` and `--jq` when scripted output is needed.

## Scope rules

- This skill must not perform organization-level management or settings actions.
- Work on non-current repositories only when the user explicitly provides `owner/repo` (for commands or scripts that support `--repo`).

## Issue and pull request script reference

Use `references/script-summary.md` for the full list of reusable scripts (issues, pull requests, repo operations, and setup checks) with arguments and intent.

## Workflow templates

- `references/workflows.md`: Reusable, copy-ready end-to-end workflows (for example, PR review-comment and PR check triage flows on the current branch).
- `references/github_workflow_behaviors.md`: Decision policy for issue label suggestion and commit issue-link workflows.

## Issue close standard

- For issue closure, follow this sequence:
  1. verify issue state is open,
  2. post a concise closure note referencing implementation evidence,
  3. close the issue.
- Prefer the dedicated helper script:
  - `scripts/issues_close_with_evidence.sh --issue <number> --commit-sha <sha> [--commit-url <url>] [--pr-url <url>] [--repo <owner/repo>] [--allow-non-project]`
- Closure note template:
  - `Implemented in commit <short_sha> (<commit_url>).`
  - `Implemented via PR <pr_url>.`
- Prefer including both commit and PR links when available.

## `gh issue view --json` field pitfalls

- `gh issue view --json projects` is invalid and returns `Unknown JSON field: "projects"`.
- Use `projectItems` and/or `projectCards` instead.
- If fields are uncertain, run once with an intentionally invalid field and use the CLI's returned “Available fields” list.

## Repository listing

- Use `scripts/repos_list.sh` for repository discovery commands.

## Installation and setup

- `references/installation.md`: Check whether `gh` is installed and how to install it on common OSes.
- `scripts/check_gh_installed.sh [--min-version <version>]`: Validate that `gh` exists and meets a minimum version.
- `scripts/check_gh_authenticated.sh [--host github.com]`: Verify the active `gh` authentication session for the host.
- `scripts/preflight_gh.sh [--host github.com] [--min-version <version>] [--allow-non-project]`: Run prerequisite checks before other `gh` operations.
- `scripts/check_docs_script_refs.sh [--skill-dir <path>]`: Verify docs reference valid scripts and documented flags.

## Failure retry matrix

- Auth/session errors (`gh auth status` fails, 401/403 auth):
  - Retry command: `gh auth login && scripts/preflight_gh.sh --host github.com`
- Repository context errors (not a git repo, cannot resolve repo):
  - Retry command: `gh repo view --json nameWithOwner` in the target repo directory, or pass explicit `--repo owner/repo`.
- Invalid JSON field errors (for example `Unknown JSON field: "projects"`):
  - Retry command: replace with supported fields, e.g. `gh issue view <n> --json number,title,state,projectItems,projectCards`.
- Transient API/network failures (502/503/timeouts):
  - Retry command: re-run the same `gh ...` command after a short delay; keep scope unchanged.

## Learn

- If command usage or output from `gh` differs from expected behavior, treat the skill as stale.
- When stale behavior is found:
  1. Update the relevant script(s) under `github/scripts/` first.
  2. Update `github/SKILL.md` and `github/references/` docs in the same change set so the instructions stay current.
  3. Record the correction in a short note in the updated docs so future runs use the new behavior.
- Keep user-facing guidance in `references/` and workflow logic in scripts aligned with tested real-world usage.
