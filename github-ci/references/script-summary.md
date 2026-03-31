# GitHub CI script summary

Use this as the authoritative script catalog referenced by `github-ci/SKILL.md`.

## Fast helper picks

- Use `scripts/prs_checks.sh` for a quick PR-check status view.
- Use `scripts/inspect_pr_checks.py` for PR-focused CI triage with log
  snippets.
- Use `scripts/actions_run_inspect.sh` for generic Actions run, job, and
  artifact inspection.

## Repository setup and preflight

- `scripts/check_gh_installed.sh [--min-version <version>]`: Validate that `gh` is installed and meets a minimum version.
- `scripts/check_gh_authenticated.sh [--host github.com]`: Verify active GitHub CLI authentication.
- `scripts/preflight_gh.sh [--host github.com] [--min-version <version>] [--expect-repo <owner/repo>] [--allow-non-project]`: Run prerequisite checks before other `gh` operations.
- `scripts/check_docs_script_refs.sh [--skill-dir <path>]`: Verify docs reference existing scripts and documented flags are present in `--help` output.
- `scripts/issue_resolve_repo.sh [--repo <owner/repo>] [--allow-non-project]`: Resolve the target repository, defaulting to current git project.

## CI scripts

- `scripts/prs_checks.sh --pr <number> [--required] [--watch] [--interval <seconds>] [--fail-fast] [--json <fields>] [--repo <owner/repo>] [--allow-non-project]`
- `scripts/inspect_pr_checks.py [--repo <path>] [--pr <number|url>] [--max-lines <N>] [--context <N>] [--json]`: PR-focused CI triage helper. For non-PR Actions runs, prefer `scripts/actions_run_inspect.sh`.
- `scripts/actions_run_inspect.sh [--repo <owner/repo>] [--run-id <id>] [--job-id <id>] [--artifact-name <name>] [--download-dir <path>] [--branch <branch>] [--commit <sha>] [--workflow <name>] [--event <event>] [--status <status>] [--limit N] [--all] [--summary-only] [--allow-non-project]`: List recent non-PR workflow runs or inspect one run/job/artifact path in a single helper.
