---
name: github-reviews
description: Inspect unresolved PR review feedback, cluster actionable threads, draft or post replies, and submit reviews through repo-owned `gh` helpers.
---

# GitHub Reviews

## Overview

Use this skill for pull-request review follow-up work. It owns thread-aware
review inspection, actionable feedback clustering, top-level PR comment
follow-up, reply preview/write flows, and review submission.

Prefer `scripts/prs_address_comments.sh` for normalized thread-aware context.
Keep reactions, PR metadata edits, CI debugging, release/tag work, and PR
lifecycle mutations out of this skill.

## Trigger rules

- Use when the user wants unresolved review-thread context, requested-changes
  triage, PR review-comment inspection, top-level PR comment follow-up tied to
  review work, reply drafting, or review submission.
- Default to unresolved, non-outdated review context.
- Use `--include-resolved` only when the user explicitly asks for historical
  or resolved thread context.
- Keep reactions in umbrella `github`, even for PR review comments.

## Workflow

1. Resolve repository and PR scope first.
2. Inspect review context with
   `scripts/prs_address_comments.sh --pr <number> [--repo <owner/repo>]`.
3. Separate actionable feedback from resolved, outdated, informational, or
   duplicate comments.
4. If the user wants a reply, select comments explicitly and prefer
   `--dry-run` before a real write.
5. If the user wants to submit a review, use `scripts/prs_review.sh` and
   restate the PR and review mode before mutating.
6. Report which threads or comments were inspected, which remained actionable,
   and whether the result was inspection-only, preview, or real write.

## Guardrails

- Do not treat flat PR comments as a full replacement for thread-aware review
  state.
- Do not reply, resolve, or submit a review unless the user explicitly asks
  for the write.
- Keep PR title/body/base, labels, assignees, reviewers, and other metadata in
  umbrella `github`.
- Surface conflicting or ambiguous feedback instead of guessing which comment
  should win.

## Fast paths

- Use `scripts/prs_address_comments.sh` for review-thread inspection and reply
  previews.
- Use `scripts/prs_comment_add.sh` for top-level PR comment follow-up.
- Use `scripts/prs_review.sh` for approve/request-changes/comment review
  submission.

## Reference map

- `references/script-summary.md`: review-owned helper catalog and flags.
- `references/workflows.md`: review inspection, reply, and review-submission
  flows.

## Examples

- "Tell me which review comments on PR 482 are still actionable."
- "Draft replies for comments 12 and 14, but preview first."
- "Submit a request-changes review on PR 482 with this summary."
