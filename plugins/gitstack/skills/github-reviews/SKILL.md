---
name: github-reviews
description: Use the shared `ghops` CLI bundled in the `gitstack` plugin for review-thread inspection, replies, top-level PR comment follow-up, and review submission.
---

# GitHub Reviews

## Overview

Use this bundled skill when the request is clearly about review comments,
review threads, replies, or submitting a review.

The shared runtime lives at `ghops`. Keep reactions and
mixed-domain GitHub work in the umbrella `github` skill.

## Fast path

- `ghops --json doctor`
- `ghops --json reviews address --pr <n> --repo <owner/repo>`
- `ghops reviews comment --pr <n> --body <text> --repo <owner/repo>`
- `ghops reviews review --pr <n> --approve --repo <owner/repo>`

## Trigger rules

- Use for review-thread triage, reply drafting, reply posting, and review
  submission.
- Route reactions and non-review PR metadata back to `github`.
- Route CI failures to `github-ci`.

## References navigation

- Start at `references/script-summary.md` for the reviews command map.
- Open `references/workflows.md` for thread-triage, reply, and review-submit
  flows.
