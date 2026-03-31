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

- Start with `scripts/prs_checks.sh` for a quick check-state view.
- Prefer `scripts/inspect_pr_checks.py` when you need log snippets plus run
  metadata in one step.
- Keep non-GitHub Actions providers report-only and state that clearly in the
  summary.
- Summarize the likely root cause before proposing a fix plan.

### Preferred helpers

```bash
scripts/prs_checks.sh --pr <number> [--repo <owner/repo>]
python3 scripts/inspect_pr_checks.py --repo . --pr <number-or-url>
```

## actions-run-inspect

Purpose: inspect a generic GitHub Actions run that is not necessarily tied to
an open PR.

### Operator policy

- Use this path for branch, SHA, workflow, scheduled/manual, or explicit
  run-id investigations.
- Start with `gh run list` behavior through
  `scripts/actions_run_inspect.sh --summary-only` when you only need recent
  candidates.
- Use `gh run view --job ... --log` behavior through the helper when job-level
  logs matter more than run-level summary output.
- Do not fall back to `gh pr checks` when no PR exists.

### Preferred helper

```bash
scripts/actions_run_inspect.sh [--repo <owner/repo>] [--run-id <id>] [--job-id <id>] [--branch <branch>] [--commit <sha>] [--workflow <name>] [--event <event>] [--status <status>]
```

## Retry notes

- Auth/session errors: `gh auth login && scripts/preflight_gh.sh --host github.com`
- Repository mismatch errors: rerun
  `scripts/preflight_gh.sh --host github.com --expect-repo owner/repo` from
  the target repo root.
- Actions log retrieval limitations: rerun
  `scripts/actions_run_inspect.sh --run-id <id> --job-id <job-id> [--repo <owner/repo>]`
  or use `gh run download <run-id> -n <artifact>` when artifacts matter more
  than logs.
