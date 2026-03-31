# GitHub umbrella workflows

Use this reference for umbrella-owned GitHub flows only. Route review-thread
work to `github-reviews`, CI/Actions investigation to `github-ci`,
release/tag work to `github-releases`, and PR publish/lifecycle mutations to
`github-publish`.

## pr-update-metadata

Purpose: update PR title, body, or base without getting blocked by the recent
`gh pr edit` project-scope read behavior.

### Operator policy

- Prefer `scripts/prs_update.sh` over ad-hoc `gh pr edit`.
- If `gh pr edit` fails with `missing required scopes [read:project]`, the
  helper retries through `gh api` for title/body/base-only updates.
- Run `scripts/preflight_gh.sh --expect-repo <owner/repo>` from the target repo
  root before mutation.

### Preferred helper

```bash
scripts/prs_update.sh --pr <number> [--title <text>] [--body <text>] [--base <branch>] [--repo <owner/repo>]
```

## issue-copy-or-move

Purpose: continue issue work in another repository without losing source
context.

### Operator policy

- Choose copy when the source issue should stay open.
- Choose move when work should continue only in the target repository.
- Use `references/issue-workflows.md` for move-note shape and source-close
  behavior.

### Preferred helpers

```bash
scripts/issues_copy.sh --issue <number> --source-repo <owner/repo> --target-repo <owner/repo> [--dry-run]
scripts/issues_move.sh --issue <number> --source-repo <owner/repo> --target-repo <owner/repo> [--dry-run]
```

## issue-close-with-evidence

Purpose: close an issue with traceable implementation evidence.

### Operator policy

- Verify the issue is still open before mutation.
- Add the evidence comment before closing the issue.
- Prefer commit and PR links together when both exist.

### Preferred helper

```bash
scripts/issues_close_with_evidence.sh --issue <number> --commit-sha <sha> [--commit-url <url>] [--pr-url <url>] [--repo <owner/repo>] [--dry-run]
```

## pr-patch-inspect

Purpose: inspect PR changed files or a file-specific patch without leaving the
umbrella triage path.

### Operator policy

- Prefer `scripts/prs_patch_inspect.sh` over ad-hoc pull-request file API
  calls.
- Use `--path` when the user only cares about one file.

### Preferred helper

```bash
scripts/prs_patch_inspect.sh --pr <number> [--repo <owner/repo>] [--path <file>] [--include-patch] [--json]
```

## reactions-manage

Purpose: list or mutate reactions on PRs, issues, issue comments, or PR review
comments.

### Operator policy

- Keep reactions in the umbrella, including PR review comment reactions.
- Use `--dry-run` before writes when the user wants a preview.

### Preferred helper

```bash
scripts/reactions_manage.sh --resource pr|issue|issue-comment|pr-review-comment --repo <owner/repo> [--number <n>|--comment-id <id>] [--list|--add <reaction>|--remove <reaction-id>] [--dry-run]
```

## issue-create-label-suggestions

Purpose: suggest labels for a new issue before creation.

### Operator policy

- Suggest existing repo labels first.
- Only create fallback reusable labels when explicitly enabled.
- Treat suggestion output as informational until the user confirms selection.

### Preferred helper

```bash
scripts/issues_suggest_labels.sh --repo <owner/repo> --title <text> [--body <text>] [--max-suggestions N] [--min-score <float>] [--allow-new-label] [--new-label-color <rrggbb>] [--new-label-description <text>] [--json]
```

## commit-with-issue-close

Purpose: preview or execute commit wording that closes an issue with a close
token when that intent is clear.

### Operator policy

- Default to preview with `--dry-run`.
- Preserve an existing close token when one is already present.
- Surface ambiguity instead of guessing when multiple issue candidates appear.

### Preferred helper

```bash
scripts/commit_issue_linker.sh --message <text> [--context <text>] [--branch <name>] [--repo <path|owner/repo>] [--issue-number <number>] [--token <fixes|closes|resolves>] [--dry-run|--execute] [--json]
```
