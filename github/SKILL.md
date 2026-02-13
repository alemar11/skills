---
name: github
description: Use the GitHub CLI (`gh`) for repository-scoped issue, pull request, and workflow operations only. Default to the current git project unless another `owner/repo` is provided.
---

# GitHub CLI

## Quick workflow

1. Determine project scope first.
   - If in a git repository: operate only on the current project unless explicitly asked to target another `owner/repo`.
   - If not in a git repository: pause and ask the user whether to:
     1) create a git repo first, or 2) proceed with non-project operations.
2. Enforce repository-only scope.
   - Allowed: repository-level read/write for issues, pull requests, runs, and repo labels.
   - Forbidden: organization-level or higher scope mutations (for example org settings, org rulesets, org membership, org secrets/variables, enterprise APIs).
   - If a request is forbidden, stop and ask for a repo-scoped alternative.
3. Ensure `gh` is available and authenticated before running any action.
4. Run the narrowest `gh` command needed, then report only relevant output.
5. If the operation fails, return the command error and propose the next retry command.

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

## Repository listing

- Use `scripts/repos_list.sh` for repository discovery commands.

## Installation and setup

- `references/installation.md`: Check whether `gh` is installed and how to install it on common OSes.
- `scripts/check_gh_installed.sh [--min-version <version>]`: Validate that `gh` exists and meets a minimum version.
- `scripts/check_gh_authenticated.sh [--host github.com]`: Verify the active `gh` authentication session for the host.
- `scripts/preflight_gh.sh [--host github.com] [--min-version <version>] [--allow-non-project]`: Run prerequisite checks before other `gh` operations.

## Learn

- If command usage or output from `gh` differs from expected behavior, treat the skill as stale.
- When stale behavior is found:
  1. Update the relevant script(s) under `github/scripts/` first.
  2. Update `github/SKILL.md` and `github/references/` docs in the same change set so the instructions stay current.
  3. Record the correction in a short note in the updated docs so future runs use the new behavior.
- Keep user-facing guidance in `references/` and workflow logic in scripts aligned with tested real-world usage.
