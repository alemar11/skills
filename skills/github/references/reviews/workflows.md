# GitHub review workflows

Use this reference for review-thread inspection, reply flows, and review
submission. Keep reactions in umbrella `github`.

## review-thread-triage

Purpose: inspect review feedback with thread-aware context and identify what is
still actionable.

### Preconditions

- `gh` installed and authenticated.
- Repository scope is known.
- Run `scripts/ghops --json doctor` when repo context is uncertain before
  write operations.

### Operator policy

- Prefer `scripts/ghops reviews address` over manual `gh api graphql`
  rollups.
- Default to unresolved, non-outdated thread context.
- Use `--include-resolved` only when the user explicitly asks for historical
  context.
- Keep top-level PR comment follow-up in this skill when it is part of review
  work.

### Preferred command

```bash
scripts/ghops --json reviews address --pr <number> [--repo <owner/repo>]
```

## review-reply

Purpose: preview or post replies to selected review feedback.

### Operator policy

- Prefer `scripts/ghops reviews address --reply-body ... --dry-run` before a
  real write.
- Use either `--selection` or `--comment-ids` with `--reply-body`.
- Use `scripts/ghops reviews comment` for top-level PR comments when a direct
  review-comment reply is not the right fit.
- If the review-comment reply endpoint fails, document whether the helper fell
  back to a PR-level comment.

### Preferred commands

```bash
scripts/ghops reviews address --pr <number> --selection <rows> --reply-body <text> --dry-run [--repo <owner/repo>]
scripts/ghops reviews comment --pr <number> --body <text> [--repo <owner/repo>]
```

## review-submit

Purpose: submit an approve, request-changes, or comment review.

### Operator policy

- Restate the exact PR and review mode before mutation.
- Use `scripts/ghops reviews review` instead of manual `gh pr review` when you
  want the repo-owned interface.
- Do not submit a review unless the user explicitly asks for the write.

### Preferred command

```bash
scripts/ghops reviews review --pr <number> [--approve|--request-changes|--comment] [--body <text>] [--repo <owner/repo>]
```

## Retry notes

- Auth/session errors: `gh auth login && scripts/ghops --json doctor`
- Repository mismatch errors: rerun the command from the target repo root or
  pass `--repo owner/repo` explicitly.
- Reply-target ambiguity: rerun `scripts/ghops --json reviews address --pr <number>`
  first, then choose `--selection` or `--comment-ids` explicitly.
