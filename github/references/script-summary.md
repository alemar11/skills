# GitHub skill script summary

Use this as the authoritative script catalog referenced by `github/SKILL.md`.

## Fast helper picks

- Use `scripts/repos_view.sh` for repository orientation and `scripts/issues_view.sh --summary` / `scripts/prs_view.sh --summary` for concise issue or PR triage.
- Use raw `gh` read-only commands only for trivial inspection that does not need normalized output.
- Use `scripts/prs_patch_inspect.sh` for changed-file or per-file patch inspection.
- Use `scripts/prs_address_comments.sh` for review-thread and comment follow-up context.
- Use `scripts/reactions_manage.sh` for listing or mutating reactions.
- Use `scripts/prs_open_current_branch.sh` to open a PR from an already-pushed current branch.
- Use `scripts/inspect_pr_checks.py` for PR-associated CI failures.
- Use `scripts/actions_run_inspect.sh` for non-PR Actions run listing, run inspection, job logs, and artifact downloads.
- Use `scripts/release_plan.sh`, `scripts/release_notes_generate.sh`, and `scripts/release_create.sh` for release flows.

## Repository setup and preflight

- `scripts/check_gh_installed.sh [--min-version <version>]`: Validate that `gh` is installed and meets a minimum version.
- `scripts/check_gh_authenticated.sh [--host github.com]`: Verify active GitHub CLI authentication.
- `scripts/preflight_gh.sh [--host github.com] [--min-version <version>] [--expect-repo <owner/repo>] [--allow-non-project]`: Run prerequisite checks before other `gh` operations.
- `scripts/release_plan.sh [--repo <owner/repo>] [--target-branch <branch>] [--allow-non-project]`: Resolve the default branch, chosen target branch, target HEAD commit, and latest published release tag before creating a release.
- `scripts/release_notes_generate.sh --tag <tag> --target-ref <branch-or-sha> [--repo <owner/repo>] [--previous-tag <tag>] [--workdir <path>] [--title-file <path>] [--notes-file <path>] [--allow-non-project]`: Generate draft release title and notes through GitHub's release-notes API.
- `scripts/release_create.sh --tag <tag> --target-ref <branch-or-sha> --notes-mode <infer|blank|user> [--repo <owner/repo>] [--title <text>|--title-file <path>] [--notes-file <path>|--notes-text <text>] [--previous-tag <tag>] [--allow-non-project]`: Create a release with an explicit target and explicit notes strategy. This helper refuses to run without `--notes-mode`.
- `scripts/check_docs_script_refs.sh [--skill-dir <path>]`: Verify docs reference existing scripts and documented flags are present in `--help` output.
- `scripts/issue_resolve_repo.sh [--repo <owner/repo>] [--allow-non-project]`: Resolve the target repository, defaulting to current git project.
- `scripts/repos_list.sh [--owner <owner>] [--type all|owner|member|public|private|forks|archived|sources] [--all] [--limit N] [--allow-non-project]`: List repositories available to current user or specified owner.
- `scripts/repos_view.sh [--repo <owner/repo>] [--json] [--allow-non-project]`: Show a normalized repository summary for triage and orientation work.
- `scripts/actions_run_inspect.sh [--repo <owner/repo>] [--run-id <id>] [--job-id <id>] [--artifact-name <name>] [--download-dir <path>] [--branch <branch>] [--commit <sha>] [--workflow <name>] [--event <event>] [--status <status>] [--limit N] [--all] [--summary-only] [--allow-non-project]`: List recent non-PR workflow runs or inspect one run/job/artifact path in a single helper.

## Issue scripts

- Recommended close sequence: `issues_close_with_evidence.sh` (single-step verify/comment/close).
- `scripts/issues_list.sh [--state open|closed|all] [--labels <label1,label2>] [--limit N] [--repo <owner/repo>] [--allow-non-project]` (default state: open)
- `scripts/issues_view.sh --issue <number> [--summary] [--repo <owner/repo>] [--allow-non-project]`
- `scripts/issues_create.sh --title <text> [--body <text>] [--labels <label1,label2>] [--assignees <user1,user2>] [--repo <owner/repo>] [--allow-non-project]`
- `scripts/issues_copy.sh --issue <number> --source-repo <owner/repo> --target-repo <owner/repo> [--dry-run]`
- `scripts/issues_move.sh --issue <number> --source-repo <owner/repo> --target-repo <owner/repo> [--dry-run]`
- `scripts/issues_suggest_labels.sh --repo <owner/repo> --title <text> [--body <text>] [--max-suggestions N] [--min-score <float>] [--allow-new-label] [--new-label-color <rrggbb>] [--new-label-description <text>] [--json]`: Suggest existing repo labels first; reusable fallback labels are explicit and opt-in.
- `scripts/issues_update.sh --issue <number> [--title <text>] [--body <text>] [--state open|closed] [--type bug|task|none] [--milestone <name>|--milestone-id <number>] [--remove-milestone] [--type-label-bug <label>] [--type-label-task <label>] [--add-labels <label1,label2>] [--remove-labels <label1,label2>] [--assignees <user1,user2>] [--remove-assignees <user1,user2>] [--repo <owner/repo>] [--allow-non-project]`: Convenience wrapper for repos that use generic `bug` / `task` label taxonomies; override `--type-label-*` or use raw label edits for other schemes.
- `scripts/issues_close_with_evidence.sh --issue <number> --commit-sha <sha> [--commit-url <url>] [--pr-url <url>] [--repo <owner/repo>] [--allow-non-project] [--dry-run]`
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
- `scripts/prs_view.sh --pr <number> [--summary] [--repo <owner/repo>] [--allow-non-project]`
- `scripts/prs_create.sh --title <text> [--body <text>] [--base <branch>] [--head <branch>] [--draft] [--labels <label1,label2>] [--repo <owner/repo>] [--allow-non-project]`
- `scripts/prs_open_current_branch.sh --title <text> [--body <text>] [--base <branch>] [--draft] [--repo <owner/repo>] [--dry-run] [--allow-non-project]`: Open a PR from the already-pushed current branch without staging, committing, or pushing.
- `scripts/prs_update.sh --pr <number> [--title <text>] [--body <text>] [--base <branch>] [--milestone <name>] [--remove-milestone] [--add-labels <label1,label2>] [--remove-labels <label1,label2>] [--add-assignees <user1,user2>] [--remove-assignees <user1,user2>] [--add-reviewers <user1,user2>] [--remove-reviewers <user1,user2>] [--repo <owner/repo>] [--allow-non-project]`: Update PR metadata. When `gh pr edit` fails with `missing required scopes [read:project]`, this helper retries via `gh api` for title/body/base-only updates.
- `scripts/prs_ready.sh --pr <number> [--repo <owner/repo>] [--allow-non-project]`
- `scripts/prs_draft.sh --pr <number> [--repo <owner/repo>] [--allow-non-project]`
- `scripts/prs_checkout.sh --pr <number> [--branch <name>] [--detach] [--force] [--recurse-submodules] [--repo <owner/repo>] [--allow-non-project]`
- `scripts/prs_comment_add.sh --pr <number> --body <text> [--repo <owner/repo>] [--allow-non-project]`
- `scripts/prs_address_comments.sh --pr <number> [--repo <owner/repo>] [--include-resolved] [--json] [--selection <rows>] [--comment-ids <ids>] [--reply-body <text>] [--dry-run] [--allow-non-project]`: Fetch normalized PR conversation, review-comment, and review-thread context; optionally reply to selected comments.
- `scripts/prs_comments_list.sh --pr <number> [--repo <owner/repo>] [--allow-non-project]`
- `scripts/prs_review_comments_list.sh --pr <number> [--repo <owner/repo>] [--allow-non-project]`
- `scripts/prs_patch_inspect.sh --pr <number> [--repo <owner/repo>] [--path <file>] [--include-patch] [--json] [--allow-non-project]`: Inspect changed files for a PR, optionally narrowed to one path and including patch text.
- `scripts/prs_review.sh --pr <number> [--approve|--request-changes|--comment] [--body <text>] [--repo <owner/repo>] [--allow-non-project]`
- `scripts/prs_checks.sh --pr <number> [--required] [--watch] [--interval <seconds>] [--fail-fast] [--json <fields>] [--repo <owner/repo>] [--allow-non-project]`
- `scripts/prs_merge.sh --pr <number> [--merge|--squash|--rebase] [--delete-branch] [--admin] [--auto] [--repo <owner/repo>] [--allow-non-project]`
- `scripts/prs_close.sh --pr <number> [--repo <owner/repo>] [--allow-non-project]`
- `scripts/prs_reopen.sh --pr <number> [--repo <owner/repo>] [--allow-non-project]`
- `scripts/inspect_pr_checks.py [--repo <path>] [--pr <number|url>] [--max-lines <N>] [--context <N>] [--json]`: PR-focused CI triage helper. For non-PR Actions runs, prefer `scripts/actions_run_inspect.sh`.
- `scripts/commit_issue_linker.sh --message <text> [--context <text>] [--branch <name>] [--repo <path|owner/repo>] [--issue-number <number>] [--token <fixes|closes|resolves>] [--dry-run|--execute] [--json]`: Preserve an existing close token when present, or infer one candidate and optionally execute the commit.

## Reactions

- `scripts/reactions_manage.sh --resource pr|issue|issue-comment|pr-review-comment --repo <owner/repo> [--number <n>|--comment-id <id>] [--list|--add <reaction>|--remove <reaction-id>] [--dry-run] [--json] [--allow-non-project]`: List, add, or remove reactions through one normalized helper.
