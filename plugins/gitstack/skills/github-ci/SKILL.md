---
name: github-ci
description: Handle focused GitHub CI work inside `gitstack`. Use plain `gh` for routine PR checks and Actions listing, and use `ghflow ci inspect` for reusable failing-PR triage.
---

# GitHub CI

## Overview

Use this bundled skill when the request is about failing checks, GitHub Actions
runs, or log-oriented CI triage.

Use plain `gh` commands for routine check reads and run inspection. Use
`ghflow ci inspect` when the job is specifically to gather failing GitHub
Actions evidence from a pull request. Keep review-thread work in
`github-reviews` and publish lifecycle work in the umbrella `github`.

## Direct commands first

- `gh pr checks <n> --repo <owner/repo>`
- `gh run list --repo <owner/repo>`
- `gh run view <run-id> --repo <owner/repo>`

## Fast path

- `ghflow ci inspect --pr <number-or-url>`
- `gh pr checks <n> --repo <owner/repo>`
- `gh run list --repo <owner/repo>`
- `gh run view <run-id> --repo <owner/repo>`
- `gh run view <run-id> --repo <owner/repo> --log-failed`

## Trigger rules

- Use for PR checks and generic Actions investigation.
- Distinguish PR-associated failures from generic branch, SHA, workflow, or
  explicit run-id investigations.
- Use `ghflow ci inspect` for repeated failing-PR triage that should fetch run
  metadata, fall back to job logs, and extract a concise failure snippet.
- Route release publication back to `github-releases`.

## References navigation

- Start at `references/script-summary.md` for the CI command map.
- Open `references/workflows.md` for PR-check triage and generic Actions flows.
