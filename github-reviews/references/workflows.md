# GitHub review workflows

Use this reference for review-thread inspection, reply flows, and review
submission. Keep reactions in umbrella `github`.

## review-thread-triage

Purpose: inspect review feedback with thread-aware context and identify what is
still actionable.

### Preconditions

- `gh` installed and authenticated.
- Repository scope is known.
- Run `scripts/preflight_gh.sh --expect-repo <owner/repo>` from the target
  repo root before write operations.

### Operator policy

- Prefer `scripts/prs_address_comments.sh` over manual `gh api graphql`
  rollups.
- Default to unresolved, non-outdated thread context.
- Use `--include-resolved` only when the user explicitly asks for historical
  context.
- Keep top-level PR comment follow-up in this skill when it is part of review
  work.

### Preferred helper

```bash
scripts/prs_address_comments.sh --pr <number> [--repo <owner/repo>] [--json]
```

## review-reply

Purpose: preview or post replies to selected review feedback.

### Operator policy

- Prefer `scripts/prs_address_comments.sh --reply-body ... --dry-run` before a
  real write.
- Use either `--selection` or `--comment-ids` with `--reply-body`.
- Use `scripts/prs_comment_add.sh` for top-level PR comments when a direct
  review-comment reply is not the right fit.
- If the review-comment reply endpoint fails, document whether the helper fell
  back to a PR-level comment.

### Preferred helpers

```bash
scripts/prs_address_comments.sh --pr <number> --selection <rows> --reply-body <text> --dry-run [--repo <owner/repo>]
scripts/prs_comment_add.sh --pr <number> --body <text> [--repo <owner/repo>]
```

## review-submit

Purpose: submit an approve, request-changes, or comment review.

### Operator policy

- Restate the exact PR and review mode before mutation.
- Use `scripts/prs_review.sh` instead of manual `gh pr review` when you want
  the repo-owned interface.
- Do not submit a review unless the user explicitly asks for the write.

### Preferred helper

```bash
scripts/prs_review.sh --pr <number> [--approve|--request-changes|--comment] [--body <text>] [--repo <owner/repo>]
```

## Retry notes

- Auth/session errors: `gh auth login && scripts/preflight_gh.sh --host github.com`
- Repository mismatch errors: rerun
  `scripts/preflight_gh.sh --host github.com --expect-repo owner/repo` from
  the target repo root.
- Reply-target ambiguity: rerun `scripts/prs_address_comments.sh --pr <number>
  --json` first, then choose `--selection` or `--comment-ids` explicitly.
