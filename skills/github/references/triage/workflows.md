# GitHub triage workflows

Use this reference for triage-domain GitHub flows inside the consolidated
`github` skill.

## stars-manage

Purpose: list, star, and unstar repositories for the authenticated GitHub user.

### Operator policy

- Treat stars as authenticated-user scope, not repository-scope mutations.
- Allow non-project execution; explicit `owner/repo` targets are required for
  writes.
- Keep batch star and unstar runs best-effort and report per-repo outcomes.

### Preferred commands

```bash
scripts/ghops --json stars list [--by-list <slug-or-name>|--list-id <id>] [--limit N|--all]
scripts/ghops --json stars add --repo <owner/repo> [--repo <owner/repo>]... [--repos-file <path>] [--dry-run]
scripts/ghops --json stars remove --repo <owner/repo> [--repo <owner/repo>]... [--repos-file <path>] [--dry-run]
```

## star-lists-manage

Purpose: inspect, create, delete, and manage membership for GitHub star lists.

### Operator policy

- Treat star lists as authenticated-user scope and allow non-project
  execution.
- Resolve `--list` by exact slug first, then exact name; require `--list-id`
  when the selector is ambiguous.
- Use read-modify-write list membership updates so unrelated list memberships
  stay intact.
- Keep batch assign and unassign runs best-effort and report per-repo
  outcomes.

### Preferred commands

```bash
scripts/ghops --json lists list [--limit N|--all]
scripts/ghops --json lists items --list <slug-or-name>|--list-id <id> [--limit N|--all]
scripts/ghops --json lists create --name <text> [--description <text>] [--visibility private|public] [--dry-run]
scripts/ghops --json lists delete --list <slug-or-name>|--list-id <id> [--dry-run]
scripts/ghops --json lists assign --list <slug-or-name>|--list-id <id> --repo <owner/repo> [--repo <owner/repo>]... [--repos-file <path>] [--dry-run]
scripts/ghops --json lists unassign --list <slug-or-name>|--list-id <id> --repo <owner/repo> [--repo <owner/repo>]... [--repos-file <path>] [--dry-run]
```

## pr-update-metadata

Purpose: update PR title, body, or base without getting blocked by the recent
`gh pr edit` project-scope read behavior.

### Operator policy

- Prefer `scripts/ghops prs update` over ad-hoc `gh pr edit`.
- If `gh pr edit` fails with `missing required scopes [read:project]`, `ghops`
  retries through `gh api` for title/body/base-only updates.
- Use `scripts/ghops --json doctor` first when repo context is uncertain.

### Preferred command

```bash
scripts/ghops prs update --pr <number> [--title <text>] [--body <text>] [--base <branch>] [--repo <owner/repo>]
```

## issue-copy-or-move

Purpose: continue issue work in another repository without losing source
context.

### Operator policy

- Choose copy when the source issue should stay open.
- Choose move when work should continue only in the target repository.
- Use `references/triage/issue-workflows.md` for move-note shape and
  source-close behavior.

### Preferred commands

```bash
scripts/ghops issues copy --issue <number> --source-repo <owner/repo> --target-repo <owner/repo> [--dry-run]
scripts/ghops issues move --issue <number> --source-repo <owner/repo> --target-repo <owner/repo> [--dry-run]
```

## issue-close-with-evidence

Purpose: close an issue with traceable implementation evidence.

### Operator policy

- Verify the issue is still open before mutation.
- Add the evidence comment before closing the issue.
- Prefer commit and PR links together when both exist.

### Preferred command

```bash
scripts/ghops issues close-with-evidence --issue <number> --commit-sha <sha> [--commit-url <url>] [--pr-url <url>] [--repo <owner/repo>] [--dry-run]
```

## pr-patch-inspect

Purpose: inspect PR changed files or a file-specific patch without leaving the
umbrella triage path.

### Operator policy

- Prefer `scripts/ghops prs patch` over ad-hoc pull-request file API calls.
- Use `--path` when the user only cares about one file.

### Preferred command

```bash
scripts/ghops --json prs patch --pr <number> [--repo <owner/repo>] [--path <file>] [--include-patch]
```

## reactions-manage

Purpose: list or mutate reactions on PRs, issues, issue comments, or PR review
comments.

### Operator policy

- Keep reactions in the umbrella, including PR review comment reactions.
- Use `--dry-run` before writes when the user wants a preview.

### Preferred commands

```bash
scripts/ghops --json reactions list --resource pr|issue|issue-comment|pr-review-comment --repo <owner/repo> [--number <n>|--comment-id <id>]
scripts/ghops --json reactions add <reaction> --resource pr|issue|issue-comment|pr-review-comment --repo <owner/repo> [--number <n>|--comment-id <id>] [--dry-run]
scripts/ghops --json reactions remove <reaction-id> --resource pr|issue|issue-comment|pr-review-comment --repo <owner/repo> [--number <n>|--comment-id <id>] [--dry-run]
```

## issue-create-label-suggestions

Purpose: suggest labels for a new issue before creation.

### Operator policy

- Suggest existing repo labels first.
- Only create fallback reusable labels when explicitly enabled.
- Treat suggestion output as informational until the user confirms selection.

### Preferred command

```bash
scripts/ghops --json issues suggest-labels --repo <owner/repo> --title <text> [--body <text>] [--max-suggestions N] [--min-score <float>] [--allow-new-label] [--new-label-color <rrggbb>] [--new-label-description <text>]
```
