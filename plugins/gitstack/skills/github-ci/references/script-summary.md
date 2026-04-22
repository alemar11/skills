# GitHub CI command summary

Use this as the authoritative CI-domain command map referenced by the bundled
`github-ci` skill.

## Shared `ghflow` helper

- `ghflow ci inspect [--pr <number-or-url>] [--repo <owner/repo>] [--allow-non-project] [--max-lines <count>] [--context <count>]`

## Direct `gh` commands

- `gh pr checks <n> --repo <owner/repo>`
- `gh run list --repo <owner/repo>`
- `gh run view <run-id> --repo <owner/repo>`
- `gh run view <run-id> --repo <owner/repo> --log-failed`
