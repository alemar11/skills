# GitHub CI workflows

Use this reference for CI-domain GitHub flows.

## PR-associated checks

- `gh pr checks <n> --repo <owner/repo>`
- `ghflow ci inspect --pr <number-or-url>`

## Generic Actions runs

- `gh run list --repo <owner/repo>`
- `gh run view <run-id> --repo <owner/repo>`
- `gh run view <run-id> --repo <owner/repo> --log-failed`

Prefer `gh pr checks` only for PR-associated runs. Prefer `gh run ...` for
branch, SHA, workflow, schedule, manual, or explicit run-id investigations.
Use `ghflow ci inspect` when the task is to summarize failing PR checks, fetch
GitHub Actions logs, fall back to job logs, and extract a failure snippet.
