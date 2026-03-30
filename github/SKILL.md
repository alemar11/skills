---
name: github
description: Handle repo-scoped GitHub triage, review follow-up, CI, reactions, releases, tags, and opening a PR from an already-pushed branch through repo-owned `gh` helpers.
---

# GitHub

## Overview

Use this skill as the repo-owned umbrella entrypoint for repository-scoped
GitHub work. It covers repository or PR triage, review-comment follow-up, CI
investigation, reactions, releases and tags, and opening a PR from an
already-pushed current branch. Keep the workflow centered on the smallest
helper or `gh` path that solves the request cleanly.

Prefer the maintained helper scripts first. Drop to raw `gh`, `gh api`, or
GraphQL only when the helper layer does not already cover the job.

Keep commit authoring and staging discipline with the separate `commit` skill.
This skill may open a PR from an already-pushed branch, but it does not create
commits or orchestrate a full publish flow.

## Trigger rules

- Use for repository-scoped GitHub work in the current repository or an
  explicitly provided `owner/repo`.
- Use when the user wants repository orientation, issue or PR summaries, patch
  inspection, review-thread context, PR checks or Actions logs, reactions,
  release or tag work, or to open a PR from the current pushed branch.
- Default to the current repository unless the user explicitly provides another `owner/repo`.
- Reject or reroute organization-level or enterprise-level mutation requests.
- If a task does not require GitHub work, use a more direct non-GitHub workflow.

## Quick workflow

1. Determine project scope first.
   - If in a git repository: operate only on the current project unless explicitly asked to target another `owner/repo`.
   - If not in a git repository: pause and ask the user whether to:
     1) create a git repo first, or 2) proceed with non-project operations.
2. Enforce repository-only scope.
   - Allowed: repository-level read/write for issues, pull requests, runs, and repo labels.
   - Forbidden: organization-level or higher scope mutations (for example org settings, org rulesets, org membership, org secrets/variables, enterprise APIs).
   - If a request is forbidden, stop and ask for a repo-scoped alternative.
3. Classify the request before choosing a helper.
   - `repo or PR triage`: repository orientation, issue or PR summaries, or patch inspection
   - `review follow-up`: actionable review comments or unresolved thread context
   - `CI debugging`: PR checks or non-PR Actions run investigation
   - `reactions`: list, add, or remove reactions on PRs, issues, or comments
   - `release or tag`: release-backed tags, tag-only refs, or release-note generation
   - `open PR`: open a PR from the current branch after it is already pushed
4. Choose the narrowest owned helper first.
   - `scripts/repos_view.sh` for repository orientation
   - `scripts/issues_view.sh --summary` and `scripts/prs_view.sh --summary` for concise issue or PR triage
   - `scripts/prs_patch_inspect.sh` for changed-file and patch inspection
   - `scripts/prs_address_comments.sh` for review-thread and comment follow-up context
   - `scripts/inspect_pr_checks.py` for PR-associated CI failures
   - `scripts/actions_run_inspect.sh` for non-PR Actions runs
   - `scripts/reactions_manage.sh` for reactions
   - `scripts/prs_open_current_branch.sh` to open a PR from the already-pushed current branch
   - `scripts/release_plan.sh`, `scripts/release_notes_generate.sh`, and `scripts/release_create.sh` for release flows
5. Use the read-only fast path when it is enough.
   - Skip full preflight for clearly read-only inspection such as:
     - `gh --help`, `<subcommand> --help`, `gh auth status`, `gh --version`
     - `scripts/repos_view.sh`, `scripts/issues_view.sh --summary`, `scripts/prs_view.sh --summary`
     - `gh repo view`, `gh pr view`, `gh issue view`, `gh run list`, `gh run view`
     - read-only `gh api` or GraphQL lookups that inspect the current user, repository, or PR metadata
   - For repo-scoped reads, run from the target repository when practical. If
     the repo is not the current working directory, use the subcommand's
     supported repo-targeting form explicitly:
     - many `gh` subcommands accept `--repo owner/repo`
     - `gh repo view` itself expects positional `gh repo view owner/repo`
   - If the command might mutate state, create side effects, or depends on project scripts/helpers, do not use the fast path; run full preflight instead.
6. Run preflight before mutating or context-sensitive `gh` actions:
   - Run preflight from the target repository working directory, not from the skill directory or an unrelated repository.
   - `scripts/preflight_gh.sh [--host github.com] [--min-version <version>] [--expect-repo <owner/repo>]`
   - When the target repo is known, prefer `--expect-repo <owner/repo>` to catch working-directory mismatches early.
   - If preflight was run from the wrong working directory, treat it as invalid and rerun it from the target repository before proceeding.
   - Use `--allow-non-project` only when the user explicitly requests a non-project operation.
   - For cross-repo issue transfers, prefer the dedicated helper scripts instead of manual `gh issue create/edit/close` sequences.
7. Restate the resolved target repository, PR, issue, release, tag, run ID, or
   comment target before mutating anything.
8. Run the narrowest helper or `gh` command needed, then report only relevant output.
9. If the operation fails, return the command error and propose the next retry
   command from `references/failure-retries.md`.

## Speed defaults

- Use `scripts/repos_view.sh`, `scripts/issues_view.sh --summary`, and
  `scripts/prs_view.sh --summary` for routine triage and orientation.
- Use `scripts/prs_patch_inspect.sh` for changed-file inspection instead of ad
  hoc pull-request file API calls.
- Use `scripts/prs_address_comments.sh` for actionable review-comment work
  instead of rebuilding temporary GraphQL rollups.
- Use `scripts/reactions_manage.sh` for all reaction work.
- Use `scripts/prs_open_current_branch.sh` for opening a PR from the current
  pushed branch; keep staging, commit creation, and push outside this skill.
- Prefer `scripts/inspect_pr_checks.py` for PR-associated CI failures.
- Prefer `scripts/actions_run_inspect.sh` for non-PR Actions run inspection.
- Prefer `scripts/release_plan.sh`, `scripts/release_notes_generate.sh`, and `scripts/release_create.sh` for release flows instead of rebuilding the same API steps ad hoc.
- Use `references/script-summary.md` as the first helper picker; open `references/workflows.md` only when no helper already covers the task.

## Actions triage standard

- Separate PR-check triage from generic Actions run inspection.
- Use PR-check triage when the failing workflow is tied to an open PR or the user explicitly asks for PR checks.
  - Start with `gh pr checks`.
  - Prefer `scripts/inspect_pr_checks.py` when you need failing log snippets plus run metadata.
- Use generic Actions run inspection when the failing workflow is tied to a branch, commit SHA, workflow name, scheduled/manual run, or explicit run ID, or when no PR exists.
  - Start with `gh run list` and add only the filters you know (`--branch`, `--commit`, `--workflow`, `--event`, `--status`).
  - Inspect summary metadata with `gh run view <run-id> --json databaseId,workflowName,status,conclusion,headBranch,headSha,displayTitle,url`.
  - Inspect failure context with `gh run view <run-id> --log-failed`.
  - Inspect a single job with `gh run view --job <job-id> --log`.
  - Download artifacts with `gh run download <run-id> -n <artifact>` when artifacts matter.
- Do not default to `gh pr checks` for branch workflows without an open PR. `gh run ...` is the correct path for non-PR Actions failures.

## Review follow-up standard

- Use `scripts/prs_address_comments.sh --pr <number> [--repo <owner/repo>]`
  first for review follow-up work.
- The default read-only mode is the standard starting point.
- By default, prioritize unresolved, non-outdated review-thread context before
  orphan review comments and PR conversation comments.
- Use `--include-resolved` only when the user explicitly asks for historical
  thread context.
- When replying, prefer `--dry-run` before posting unless the user explicitly
  wants the write immediately.

## Open PR standard

- Use `scripts/prs_open_current_branch.sh` only when the current branch is
  already pushed to a same-name remote branch.
- Do not stretch this helper into branch creation, staging, commit creation, or
  push orchestration.
- If the branch is not pushed yet, stop and tell the user to push it before
  using the helper.

## Scope rules

- This skill must not perform organization-level management or settings actions.
- Work on non-current repositories only when the user explicitly provides
  `owner/repo`.
  - Use each command's supported repo-targeting form:
    - `gh repo view owner/repo`
    - `gh issue ... --repo owner/repo`
    - `gh pr ... --repo owner/repo`
    - helper scripts that accept `--repo owner/repo`

## Issue mutation standard

- Choose the issue path before mutating:
  - `close with evidence`: implementation is complete and the issue should be
    closed
  - `implementation update`: work is implemented or prepared, but the issue
    should remain open
  - `transfer`: work should continue in another repository
- Prefer `issues_close_with_evidence.sh` for the close-with-evidence path.
- Prefer `issues_copy.sh` when the source issue stays open and `issues_move.sh`
  when work should continue only in the target repository.
- Use `references/issue-workflows.md` for the exact comment templates, move
  behavior, and `gh issue view --json` field pitfalls.

## Reference map

- `references/script-summary.md`: authoritative helper catalog and documented
  script flags.
- `references/workflows.md`: reusable copy-paste workflows for PR, Actions,
  reaction, and release tasks.
- `references/issue-workflows.md`: issue close/update/transfer standards and
  issue-view JSON field pitfalls.
- `references/github_workflow_behaviors.md`: decision policy for issue label
  suggestion and commit issue-link workflows.
- `references/installation.md`: GitHub CLI installation, auth, and preflight
  setup.
- `references/failure-retries.md`: retry commands for common auth, repo,
  Actions, and API failure modes.

Note (2026-03): issue transfer is standardized with dedicated copy/move
scripts after manual transfers proved too easy to run from the wrong repo
context.

## Output Expectations

- Restate the resolved target repository, PR, issue, release, tag, or run ID
  before mutating anything.
- For repository, issue, or PR triage, prefer concise normalized summaries over
  raw JSON or raw command output.
- For review-comment and reaction mutations, report the exact selected targets
  and whether the run was a preview (`--dry-run`) or a real write.
- For read-only requests, return the relevant facts and next useful command or
  action, not raw command noise.
- For failed commands, report the concrete error and the retry command from
  `references/failure-retries.md` when one applies.

## Release and tag creation standard

- First determine whether the user wants:
  - a GitHub release that may create a missing tag, or
  - a tag only.
- For `gh release create`, do not rely on its implicit target selection.
  - Resolve the repository default branch explicitly.
  - Resolve the exact HEAD commit of that branch explicitly.
- When the user does not specify a branch or commit, show the proposed default target before mutating:
  - default branch name
  - target commit short SHA
  - target commit subject line
- Do not hardcode `main`. Use the repository's actual default branch.
- For release creation, choose the notes strategy before publishing.
  - If the user does not specify a notes strategy, offer exactly these three options:
    1. infer notes by diffing since the last published release tag,
    2. keep the release notes blank,
    3. use user-provided notes.
  - Do not treat user silence as delegation. Ask for the notes strategy unless the user explicitly says to choose for them.
  - Default to option 1 only when the user explicitly delegates the choice.
  - For option 1, resolve the latest published release tag when one exists and generate the proposed title/body for the new tag from that prior release range.
- Prefer `scripts/release_plan.sh` to resolve the default branch, target commit, and previous release tag before asking for confirmation.
- Prefer `scripts/release_create.sh` for release creation because it requires an explicit `--notes-mode` and explicit `--target-ref`.
- If the user does not want the default target:
  - pick the branch first,
  - then pick the commit on that branch.
- For release-backed tags, prefer an explicit target even when the user confirms the default:
  - `gh release create <tag> --target <branch-or-sha>`
- `gh release create <tag>` creates the release and auto-creates the tag if the tag does not already exist in the remote repository.
- Prefer an explicit previous tag for generated notes when one exists:
  - `gh release create <tag> --target <branch-or-sha> --generate-notes --notes-start-tag <previous_tag>`
- For tag-only creation:
  - use `git tag` plus `git push origin <tag>` when working from a local clone,
  - use `gh api` only when GitHub API-specific behavior is required.
- If the user wants an annotated tag to drive release notes:
  - create and push the annotated tag first,
  - then use `gh release create <tag> --verify-tag --notes-from-tag`.
- Always report the chosen notes strategy, the previous tag used for release-note generation when applicable, plus the final tag name, resolved target SHA, and release URL.

## Repository listing

- Use `scripts/repos_list.sh` for repository discovery commands.
- Use `scripts/repos_view.sh` for repository orientation in the current repo or
  an explicit `owner/repo`.
- Outside a git repository, pass `--allow-non-project` explicitly for deliberate non-project discovery.

## Learn

- If repeated runtime GitHub work suggests a better helper script, routing rule, or reference update, treat that as a runtime learning signal; see `references/github_skill_learn.md`.
- Prefer improving an existing helper before proposing a new script.
- Keep user-facing guidance in `references/` and workflow logic in scripts aligned with tested real-world usage.

## Examples

- "Summarize this repo and tell me what matters first."
- "Show me the open PRs for this repo and summarize which one needs attention."
- "Show me what changed in PR 482."
- "Tell me which review comments on PR 482 are still actionable."
- "Inspect the failing Actions run on this branch and tell me the likely cause."
- "Add a thumbs-up reaction to this PR review comment."
- "Open a draft PR from my current pushed branch."
- "Create a release for this tag, but confirm the target branch and notes strategy first."
