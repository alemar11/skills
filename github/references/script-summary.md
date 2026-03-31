# GitHub umbrella script summary

Use this as the authoritative script catalog referenced by `github/SKILL.md`.
Route review follow-up to `github-reviews`, CI debugging to `github-ci`,
release/tag work to `github-releases`, and PR publish/lifecycle mutations to
`github-publish`.

## Fast helper picks

- Use `scripts/repos_view.sh` for repository orientation and
  `scripts/issues_view.sh --summary` / `scripts/prs_view.sh --summary` for
  concise issue or PR triage.
- Use `scripts/prs_patch_inspect.sh` for changed-file or per-file patch
  inspection.
- Use `scripts/reactions_manage.sh` for reactions, including PR review comment
  reactions.
- Use `scripts/prs_update.sh` for PR metadata edits.
- Use `scripts/issues_close_with_evidence.sh` for a close-with-evidence issue
  path.
- Use `scripts/issues_suggest_labels.sh` for issue label suggestions.
- Use `scripts/commit_issue_linker.sh` for commit-close wording previews.

## Repository setup and preflight

- `scripts/check_gh_installed.sh [--min-version <version>]`: Validate that `gh` is installed and meets a minimum version.
- `scripts/check_gh_authenticated.sh [--host github.com]`: Verify active GitHub CLI authentication.
- `scripts/preflight_gh.sh [--host github.com] [--min-version <version>] [--expect-repo <owner/repo>] [--allow-non-project]`: Run prerequisite checks before other `gh` operations.
- `scripts/check_docs_script_refs.sh [--skill-dir <path>]`: Verify docs reference existing scripts and documented flags are present in `--help` output.
- `scripts/issue_resolve_repo.sh [--repo <owner/repo>] [--allow-non-project]`: Resolve the target repository, defaulting to current git project.
- `scripts/repos_list.sh [--owner <owner>] [--type all|owner|member|public|private|forks|archived|sources] [--all] [--limit N] [--allow-non-project]`: List repositories available to current user or specified owner.
- `scripts/repos_view.sh [--repo <owner/repo>] [--json] [--allow-non-project]`: Show a normalized repository summary for triage and orientation work.

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
- `scripts/prs_patch_inspect.sh --pr <number> [--repo <owner/repo>] [--path <file>] [--include-patch] [--json] [--allow-non-project]`: Inspect changed files for a PR, optionally narrowed to one path and including patch text.
- `scripts/prs_update.sh --pr <number> [--title <text>] [--body <text>] [--base <branch>] [--milestone <name>] [--remove-milestone] [--add-labels <label1,label2>] [--remove-labels <label1,label2>] [--add-assignees <user1,user2>] [--remove-assignees <user1,user2>] [--add-reviewers <user1,user2>] [--remove-reviewers <user1,user2>] [--repo <owner/repo>] [--allow-non-project]`: Update PR metadata. When `gh pr edit` fails with `missing required scopes [read:project]`, this helper retries via `gh api` for title/body/base-only updates.
- `scripts/commit_issue_linker.sh --message <text> [--context <text>] [--branch <name>] [--repo <path|owner/repo>] [--issue-number <number>] [--token <fixes|closes|resolves>] [--dry-run|--execute] [--json]`: Preserve an existing close token when present, or infer one candidate and optionally execute the commit.

## Reactions

- `scripts/reactions_manage.sh --resource pr|issue|issue-comment|pr-review-comment --repo <owner/repo> [--number <n>|--comment-id <id>] [--list|--add <reaction>|--remove <reaction-id>] [--dry-run] [--json] [--allow-non-project]`: List, add, or remove reactions through one normalized helper.
