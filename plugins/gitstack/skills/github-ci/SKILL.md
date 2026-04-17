---
name: github-ci
description: Use the shared `ghops` CLI bundled in the `gitstack` plugin for PR checks and generic GitHub Actions investigation.
---

# GitHub CI

## Overview

Use this bundled skill when the request is about failing checks, GitHub Actions
runs, or log-oriented CI triage.

The shared runtime lives at `ghops`. Keep review-thread
work in `github-reviews` and publish lifecycle work in the umbrella `github`.

## Fast path

- `ghops --json doctor`
- `ghops --json checks pr --pr <n> --repo <owner/repo>`
- `ghops --json actions list --repo <owner/repo>`
- `ghops --json actions inspect --repo <owner/repo> --run-id <id>`

## Trigger rules

- Use for PR checks and generic Actions investigation.
- Distinguish PR-associated failures from generic branch, SHA, workflow, or
  explicit run-id investigations.
- Route release publication back to `github-releases`.

## References navigation

- Start at `references/script-summary.md` for the CI command map.
- Open `references/workflows.md` for PR-check triage and generic Actions flows.
