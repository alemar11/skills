# GitHub CI workflows

Use this reference for PR-check triage and generic GitHub Actions run
inspection.

## pr-check-triage

Purpose: inspect failing checks tied to an open PR.

### Preconditions

- `gh` installed and authenticated.
- Repository scope is known.
- PR number or URL is known, or can be resolved from the current branch.

### Operator policy

- Start with `scripts/ghops checks pr` for a quick check-state view.
- Prefer `scripts/ghops actions inspect` when you need log snippets plus run
  metadata in one step.
- Keep non-GitHub Actions providers report-only and state that clearly in the
  summary.
- Summarize the likely root cause before proposing a fix plan.

### Preferred commands

```bash
scripts/ghops --json checks pr --pr <number> [--repo <owner/repo>]
scripts/ghops --json actions inspect --repo <owner/repo> --run-id <id>
```

## actions-run-inspect

Purpose: inspect a generic GitHub Actions run that is not necessarily tied to
an open PR.

### Operator policy

- Use this path for branch, SHA, workflow, scheduled/manual, or explicit
  run-id investigations.
- Start with `scripts/ghops actions list` when you only need recent candidate
  runs.
- Use `scripts/ghops actions inspect` when run-level summary output or log
  snippets matter more than a raw `gh run` dump.
- Do not fall back to `gh pr checks` when no PR exists.

### Preferred commands

```bash
scripts/ghops --json actions list [--repo <owner/repo>] [--branch <branch>] [--commit <sha>] [--workflow <name>] [--event <event>] [--status <status>]
scripts/ghops --json actions inspect [--repo <owner/repo>] --run-id <id>
```

## Retry notes

- Auth/session errors: `gh auth login && scripts/ghops --json doctor`
- Repository mismatch errors: rerun the command from the target repo root or
  pass `--repo owner/repo` explicitly.
- Actions log retrieval limitations: rerun
  `scripts/ghops --json actions inspect --run-id <id>` after confirming the
  target run id.
