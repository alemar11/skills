# GitHub skill script summary

Use this as the authoritative script catalog referenced by `github/SKILL.md`.

## Repository setup and preflight

- `scripts/check_gh_installed.sh [--min-version <version>]`: Validate that `gh` is installed and meets a minimum version.
- `scripts/check_gh_authenticated.sh [--host github.com]`: Verify active GitHub CLI authentication.
- `scripts/preflight_gh.sh [--host github.com] [--min-version <version>] [--allow-non-project]`: Run prerequisite checks before other `gh` operations.
- `scripts/issue_resolve_repo.sh [--repo <owner/repo>] [--allow-non-project]`: Resolve the target repository, defaulting to current git project.
- `scripts/repos_list.sh [--owner <owner>] [--type all|public|private|forks|archived|sources|member] [--all] [--limit N] [--allow-non-project]`: List repositories available to current user or specified owner.

## Issue scripts

- `scripts/issues_list.sh [--state open|closed|all] [--labels <label1,label2>] [--limit N] [--repo <owner/repo>] [--allow-non-project]` (default state: open)
- `scripts/issues_view.sh --issue <number> [--repo <owner/repo>] [--allow-non-project]`
- `scripts/issues_create.sh --title <text> [--body <text>] [--labels <label1,label2>] [--assignees <user1,user2>] [--repo <owner/repo>] [--allow-non-project]`
- `scripts/issues_update.sh --issue <number> [--title <text>] [--body <text>] [--state open|closed] [--type bug|task|none] [--milestone <name>|--milestone-id <number>] [--remove-milestone] [--type-label-bug <label>] [--type-label-task <label>] [--add-labels <label1,label2>] [--remove-labels <label1,label2>] [--assignees <user1,user2>] [--remove-assignees <user1,user2>] [--repo <owner/repo>] [--allow-non-project]`
- `scripts/issues_comment_add.sh --issue <number> --body <text> [--repo <owner/repo>] [--allow-non-project]`
- `scripts/issues_comments_list.sh --issue <number> [--repo <owner/repo>] [--allow-non-project]`
- `scripts/issues_lock.sh --issue <number> [--reason <reason>] [--repo <owner/repo>] [--allow-non-project]`
- `scripts/issues_unlock.sh --issue <number> [--repo <owner/repo>] [--allow-non-project]`
- `scripts/issues_pin.sh --issue <number> [--repo <owner/repo>] [--allow-non-project]`
- `scripts/issues_unpin.sh --issue <number> [--repo <owner/repo>] [--allow-non-project]`
- `scripts/issues_close.sh --issue <number> [--repo <owner/repo>] [--allow-non-project]`
- `scripts/issues_reopen.sh --issue <number> [--repo <owner/repo>] [--allow-non-project]`
- `scripts/issues_labels.sh [--repo <owner/repo>] [--allow-non-project]`
- `scripts/issues_labels_create.sh --name <label> [--color <rrggbb>] [--description <text>] [--repo <owner/repo>] [--allow-non-project]`
- `scripts/issues_labels_update.sh --name <label> [--new-name <label>] [--color <rrggbb>] [--description <text>] [--repo <owner/repo>] [--allow-non-project]`
- `scripts/issues_labels_delete.sh --name <label> [--repo <owner/repo>] [--allow-non-project]`
- `scripts/issues_milestones_list.sh [--repo <owner/repo>] [--state open|closed|all] [--limit N] [--allow-non-project]`

## Pull request scripts

- `scripts/prs_list.sh [--state open|closed|merged|all] [--author <user>] [--label <label>] [--base <branch>] [--head <branch>] [--search <query>] [--limit N] [--repo <owner/repo>] [--allow-non-project]`
- `scripts/prs_view.sh --pr <number> [--repo <owner/repo>] [--allow-non-project]`
- `scripts/prs_create.sh --title <text> [--body <text>] [--base <branch>] [--head <branch>] [--draft] [--labels <label1,label2>] [--repo <owner/repo>] [--allow-non-project]`
- `scripts/prs_update.sh --pr <number> [--title <text>] [--body <text>] [--base <branch>] [--milestone <name>] [--remove-milestone] [--add-labels <label1,label2>] [--remove-labels <label1,label2>] [--add-assignees <user1,user2>] [--remove-assignees <user1,user2>] [--add-reviewers <user1,user2>] [--remove-reviewers <user1,user2>] [--repo <owner/repo>] [--allow-non-project]`
- `scripts/prs_ready.sh --pr <number> [--repo <owner/repo>] [--allow-non-project]`
- `scripts/prs_draft.sh --pr <number> [--repo <owner/repo>] [--allow-non-project]`
- `scripts/prs_checkout.sh --pr <number> [--branch <name>] [--detach] [--force] [--recurse-submodules] [--repo <owner/repo>] [--allow-non-project]`
- `scripts/prs_comment_add.sh --pr <number> --body <text> [--repo <owner/repo>] [--allow-non-project]`
- `scripts/prs_comments_list.sh --pr <number> [--repo <owner/repo>] [--allow-non-project]`
- `scripts/prs_review_comments_list.sh --pr <number> [--repo <owner/repo>] [--allow-non-project]`
- `scripts/prs_review.sh --pr <number> [--approve|--request-changes|--comment] [--body <text>] [--repo <owner/repo>] [--allow-non-project]`
- `scripts/prs_checks.sh --pr <number> [--required] [--watch] [--interval <seconds>] [--fail-fast] [--json <fields>] [--repo <owner/repo>] [--allow-non-project]`
- `scripts/prs_merge.sh --pr <number> [--merge|--squash|--rebase] [--delete-branch] [--admin] [--auto] [--repo <owner/repo>] [--allow-non-project]`
- `scripts/prs_close.sh --pr <number> [--repo <owner/repo>] [--allow-non-project]`
- `scripts/prs_reopen.sh --pr <number> [--repo <owner/repo>] [--allow-non-project]`
- `scripts/inspect_pr_checks.py [--repo <path>] [--pr <number|url>] [--max-lines <N>] [--context <N>] [--json]`
