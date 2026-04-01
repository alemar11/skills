# GitHub publish script summary

Use this as the authoritative publish-domain script catalog referenced by
`github/SKILL.md`.

## Fast helper picks

- Use `scripts/publish/publish_context.sh` for already-pushed current-branch
  context, including long-lived-branch detection and recommended PR base.
- Use `scripts/publish/prs_open_current_branch.sh` for already-pushed current-branch
  PR opening or reuse, especially when the intended base branch is already
  known.
- Use `scripts/publish/prs_create.sh` for explicit PR creation.
- Use the PR lifecycle helpers for draft, ready, merge, close, reopen, and
  checkout flows.

## Repository setup and preflight

- `scripts/core/check_gh_installed.sh [--min-version <version>]`: Validate that `gh` is installed and meets a minimum version.
- `scripts/core/check_gh_authenticated.sh [--host github.com]`: Verify active GitHub CLI authentication.
- `scripts/core/preflight_gh.sh [--host github.com] [--min-version <version>] [--expect-repo <owner/repo>] [--allow-non-project]`: Run prerequisite checks before other `gh` operations.
- `scripts/core/check_docs_script_refs.sh [--skill-dir <path>]`: Verify docs reference existing scripts and documented flags are present in `--help` output.
- `scripts/core/issue_resolve_repo.sh [--repo <owner/repo>] [--allow-non-project]`: Resolve the target repository, defaulting to current git project.

## Publish scripts

- `scripts/publish/publish_context.sh [--repo <owner/repo>] [--json] [--allow-non-project]`: Show current repo, branch, upstream, change-count, long-lived-branch state, recommended PR base, and open-PR context for the local checkout.
- `scripts/publish/prs_open_current_branch.sh [--title <text>] [--body <text>] [--body-from-head] [--base <branch>] [--draft] [--repo <owner/repo>] [--dry-run] [--allow-non-project]`: Open or reuse a PR from the already-pushed current branch without staging, committing, or pushing; when `--base` is explicit, refuse to silently reuse an existing PR targeting a different base.
- `scripts/publish/prs_create.sh --title <text> [--body <text>] [--base <branch>] [--head <branch>] [--draft] [--labels <label1,label2>] [--repo <owner/repo>] [--allow-non-project]`
- `scripts/publish/prs_draft.sh --pr <number> [--repo <owner/repo>] [--allow-non-project]`
- `scripts/publish/prs_ready.sh --pr <number> [--repo <owner/repo>] [--allow-non-project]`
- `scripts/publish/prs_merge.sh --pr <number> [--merge|--squash|--rebase] [--delete-branch] [--admin] [--auto] [--repo <owner/repo>] [--allow-non-project]`
- `scripts/publish/prs_close.sh --pr <number> [--repo <owner/repo>] [--allow-non-project]`
- `scripts/publish/prs_reopen.sh --pr <number> [--repo <owner/repo>] [--allow-non-project]`
- `scripts/publish/prs_checkout.sh --pr <number> [--branch <name>] [--detach] [--force] [--recurse-submodules] [--repo <owner/repo>] [--allow-non-project]`: Check out a pull request locally. This mutates the local checkout state.
