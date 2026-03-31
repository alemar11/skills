---
name: github-ci
description: Inspect PR checks and GitHub Actions failures through repo-owned `gh` helpers, keeping PR-check triage separate from generic run inspection.
---

# GitHub CI

## Overview

Use this skill for GitHub Actions and PR-check investigation. It owns
PR-associated check triage, generic Actions run inspection, log inspection,
and artifact-oriented follow-up when GitHub Actions data is the main task.

Prefer the repo-owned helpers first. Keep review-thread work, releases/tags,
issues, reactions, and PR lifecycle mutations out of this skill.

## Trigger rules

- Use when the user asks for failing PR checks, GitHub Actions logs, run
  inspection, or CI root-cause analysis.
- Use PR-check triage when the failure is tied to an open PR or the user
  explicitly asks for PR checks.
- Use generic Actions inspection when the failure is tied to a branch, commit
  SHA, workflow name, schedule/manual run, or explicit run ID.
- Treat non-GitHub Actions providers as report-only unless the user asks for a
  separate workflow.

## Workflow

1. Resolve repository scope and, when available, PR number or run ID.
2. Use `scripts/prs_checks.sh` or `scripts/inspect_pr_checks.py` for
   PR-associated failures.
3. Use `scripts/actions_run_inspect.sh` for non-PR Actions runs.
4. Summarize the observed failure or root cause before proposing any fix plan.
5. Call out missing logs, unavailable job associations, or external providers
   explicitly instead of over-claiming certainty.

## Guardrails

- Do not default to `gh pr checks` for branch-only workflows without an open
  PR.
- Keep non-GitHub Actions providers report-only.
- Do not imply that repo metadata or review context alone is enough to debug
  Actions failures.
- Keep fixes out of scope unless the user asks for them after the triage
  result.

## Fast paths

- Use `scripts/inspect_pr_checks.py` when you need failing PR check metadata,
  log snippets, and one normalized result.
- Use `scripts/actions_run_inspect.sh` for generic run, job, and artifact
  inspection.

## Reference map

- `references/script-summary.md`: CI-owned helper catalog and flags.
- `references/workflows.md`: PR checks, generic Actions inspection, and retry
  guidance.

## Examples

- "Inspect the failing checks on PR 482 and tell me the likely cause."
- "Look at the GitHub Actions run on this branch and summarize the failure."
- "Show me the failed job log for this run ID."
