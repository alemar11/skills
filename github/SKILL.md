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
- Working on other repositories is allowed only via explicit `--repo owner/repo` passed to issue scripts.

## Issue battery

Use these scripts for reusable issue workflows.

- Read and filter issues:
  - Use `scripts/issues_list.sh --state open|closed|all [--labels <label1,label2>] [--limit N]` for listing (default: open).
  - Use `scripts/issues_view.sh --issue <number>` when you need the full issue JSON payload.
  - Use `scripts/issues_comments_list.sh --issue <number>` when you need threaded comment history.
- Change lifecycle and assignment:
  - Use `scripts/issues_update.sh --issue <number>` to change title, body, state, labels, assignees, or type mapping.
  - Use `scripts/issues_close.sh --issue <number>` and `scripts/issues_reopen.sh --issue <number>` for status transitions.
  - Use `scripts/issues_lock.sh --issue <number>` and `scripts/issues_unlock.sh --issue <number>` for conversation controls.
- Create and annotate issues:
  - Use `scripts/issues_create.sh --title <text> [--body <text>] [--labels ...]` to create new issues.
  - Use `scripts/issues_comment_add.sh --issue <number> --body <comment>` to post a reply.
  - Use `scripts/issues_pin.sh --issue <number>` / `scripts/issues_unpin.sh --issue <number>` to pin and unpin.
- Label management:
  - Use `scripts/issues_labels.sh` to list repository labels.
  - Use `scripts/issues_labels_create.sh --name <label>` to add a new repo-scoped label.
  - Use `scripts/issues_labels_update.sh --name <label>` to rename/color/describe a label.
  - Use `scripts/issues_labels_delete.sh --name <label>` to remove a label.
- `scripts/issue_resolve_repo.sh [--repo <owner/repo>] [--allow-non-project]`: Resolve target repo, defaulting to current git project.
- `scripts/issues_close.sh --issue <number> [--repo <owner/repo>] [--allow-non-project]`: Close an issue.
- `scripts/issues_reopen.sh --issue <number> [--repo <owner/repo>] [--allow-non-project]`: Reopen an issue.
- `scripts/issues_lock.sh --issue <number> [--reason <reason>] [--repo <owner/repo>] [--allow-non-project]`: Lock an issue.
- `scripts/issues_unlock.sh --issue <number> [--repo <owner/repo>] [--allow-non-project]`: Unlock an issue.
- `scripts/issues_pin.sh --issue <number> [--repo <owner/repo>] [--allow-non-project]`: Pin an issue.
- `scripts/issues_unpin.sh --issue <number> [--repo <owner/repo>] [--allow-non-project]`: Unpin an issue.
- `scripts/issues_labels.sh [--repo <owner/repo>] [--allow-non-project]`: List project labels.
- `scripts/issues_labels_create.sh --name <label> [--color <rrggbb>] [--description <text>] [--repo <owner/repo>] [--allow-non-project]`: Create a project label.
- `scripts/issues_labels_update.sh --name <label> [--new-name <label>] [--color <rrggbb>] [--description <text>] [--repo <owner/repo>] [--allow-non-project]`: Update a label.
- `scripts/issues_labels_delete.sh --name <label> [--repo <owner/repo>] [--allow-non-project]`: Delete a project label.
- `scripts/issues_milestones_list.sh [--repo <owner/repo>] [--state open|closed|all] [--limit N] [--allow-non-project]`: List milestones.
- `scripts/issues_list.sh [--state open|closed|all] [--labels <label1,label2>] [--limit N] [--repo <owner/repo>] [--allow-non-project]` (default: open): Read issues.
- `scripts/issues_view.sh --issue <number> [--repo <owner/repo>] [--allow-non-project]`: Read a full issue payload.
- `scripts/issues_create.sh --title <text> [--body <text>] [--labels <label1,label2>] [--assignees <user1,user2>] [--repo <owner/repo>] [--allow-non-project]`: Create issue.
- `scripts/issues_comment_add.sh --issue <number> --body <text> [--repo <owner/repo>] [--allow-non-project]`: Add a comment.
- `scripts/issues_comments_list.sh --issue <number> [--repo <owner/repo>] [--allow-non-project]`: Read issue comments.
- `scripts/issues_update.sh --issue <number> [--title <text>] [--body <text>] [--state open|closed] [--type bug|task|none] [--milestone <name>|--milestone-id <number>] [--remove-milestone] [--type-label-bug <label>] [--type-label-task <label>] [--add-labels <label1,label2>] [--remove-labels <label1,label2>] [--assignees <user1,user2>] [--remove-assignees <user1,user2>] [--repo <owner/repo>] [--allow-non-project]`: Update issue fields.

All issue scripts run `scripts/preflight_gh.sh` first and therefore inherit repo-scoping by default.

## Pull request battery

- Read and inspect:
  - `scripts/prs_list.sh [--state open|closed|merged|all] [--author <user>] [--label <label>] [--base <branch>] [--head <branch>] [--search <query>] [--limit N] [--repo <owner/repo>] [--allow-non-project]`: List pull requests.
  - `scripts/prs_view.sh --pr <number> [--repo <owner/repo>] [--allow-non-project]`: Read a PR payload.
  - `scripts/prs_comments_list.sh --pr <number> [--repo <owner/repo>] [--allow-non-project]`: Read PR comments.
  - `scripts/prs_review_comments_list.sh --pr <number> [--repo <owner/repo>] [--allow-non-project]`: Read PR review comments.
  - `scripts/prs_checks.sh --pr <number> [--required] [--watch] [--interval <seconds>] [--json <fields>] [--repo <owner/repo>] [--allow-non-project]`: Check PR CI status and required checks.
- Author and lifecycle:
  - `scripts/prs_create.sh --title <text> [--body <text>] [--base <branch>] [--head <branch>] [--draft] [--labels <label1,label2>] [--repo <owner/repo>] [--allow-non-project]`: Create a PR.
  - `scripts/prs_update.sh --pr <number> [--title <text>] [--body <text>] [--base <branch>] [--milestone <name>] [--remove-milestone] [--add-labels <label1,label2>] [--remove-labels <label1,label2>] [--add-assignees <user1,user2>] [--remove-assignees <user1,user2>] [--add-reviewers <user1,user2>] [--remove-reviewers <user1,user2>] [--repo <owner/repo>] [--allow-non-project]`: Update PR metadata.
  - `scripts/prs_ready.sh --pr <number> [--repo <owner/repo>] [--allow-non-project]`: Mark PR as ready for review.
  - `scripts/prs_draft.sh --pr <number> [--repo <owner/repo>] [--allow-non-project]`: Mark PR as draft.
  - `scripts/prs_checkout.sh --pr <number> [--branch <name>] [--detach] [--force] [--recurse-submodules] [--repo <owner/repo>] [--allow-non-project]`: Check out PR branch.
  - `scripts/prs_close.sh --pr <number> [--repo <owner/repo>] [--allow-non-project]`: Close a PR.
  - `scripts/prs_reopen.sh --pr <number> [--repo <owner/repo>] [--allow-non-project]`: Reopen a PR.
  - `scripts/prs_merge.sh --pr <number> [--merge|--squash|--rebase] [--delete-branch] [--admin] [--auto] [--repo <owner/repo>] [--allow-non-project]`: Merge PR.
- Collaboration:
  - `scripts/prs_comment_add.sh --pr <number> --body <text> [--repo <owner/repo>] [--allow-non-project]`: Add a PR comment.
  - `scripts/prs_review.sh --pr <number> [--approve|--request-changes|--comment] [--body <text>] [--repo <owner/repo>] [--allow-non-project]`: Add a review or approval.

## Repository listing

- `scripts/repos_list.sh [--owner <owner>] [--type all|public|private|forks|archived|sources|member] [--all] [--limit N] [--allow-non-project]`: List repositories available to the current user (default) or to the provided owner.

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
