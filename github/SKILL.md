---
name: github
description: Use the GitHub CLI (`gh`) for repository-scoped issue, pull request, workflow, release, and tag operations. Default to the current git project unless another `owner/repo` is provided.
---

# GitHub CLI

## Trigger rules

- Use for repository-scoped GitHub operations via `gh` (issues, pull requests, workflow runs, releases, tags, and repo metadata).
- Default to the current repository unless the user explicitly provides another `owner/repo`.
- Reject or reroute organization-level or enterprise-level mutation requests.
- If a task does not require GitHub CLI operations, use a more direct non-`gh` workflow.

## Quick workflow

1. Determine project scope first.
   - If in a git repository: operate only on the current project unless explicitly asked to target another `owner/repo`.
   - If not in a git repository: pause and ask the user whether to:
     1) create a git repo first, or 2) proceed with non-project operations.
2. Enforce repository-only scope.
   - Allowed: repository-level read/write for issues, pull requests, runs, and repo labels.
   - Forbidden: organization-level or higher scope mutations (for example org settings, org rulesets, org membership, org secrets/variables, enterprise APIs).
   - If a request is forbidden, stop and ask for a repo-scoped alternative.
3. Use the read-only fast path when it is enough.
   - Skip full preflight for clearly read-only inspection such as:
     - `gh --help`, `<subcommand> --help`, `gh auth status`, `gh --version`
     - `gh repo view`, `gh pr view`, `gh issue view`, `gh run view`
     - read-only `gh api` or GraphQL lookups that inspect the current user, repository, or PR metadata
   - For repo-scoped reads, run from the target repository when practical, or pass explicit `--repo owner/repo` when the repo is not the current working directory.
   - If the command might mutate state, create side effects, or depends on project scripts/helpers, do not use the fast path; run full preflight instead.
4. Run preflight before mutating or context-sensitive `gh` actions:
   - Run preflight from the target repository working directory, not from the skill directory or an unrelated repository.
   - `scripts/preflight_gh.sh [--host github.com] [--min-version <version>] [--expect-repo <owner/repo>]`
   - When the target repo is known, prefer `--expect-repo <owner/repo>` to catch working-directory mismatches early.
   - If preflight was run from the wrong working directory, treat it as invalid and rerun it from the target repository before proceeding.
   - Use `--allow-non-project` only when the user explicitly requests a non-project operation.
   - For cross-repo issue transfers, prefer the dedicated helper scripts instead of manual `gh issue create/edit/close` sequences.
5. Run the narrowest `gh` command needed, then report only relevant output.
6. If the operation fails, return the command error and propose the next retry command from the retry matrix below.

## Common operations

- Repository actions
  - `gh repo view` and `gh repo clone <owner>/<repo>`
- Issue actions
  - `gh issue list`, `gh issue view`, `gh issue create`, `gh issue edit`, `gh issue comment`, `gh issue close`
  - `scripts/issues_copy.sh` and `scripts/issues_move.sh` for cross-repo issue transfers
- Pull request actions
  - `gh pr list`, `gh pr view`, `gh pr create`, `gh pr edit`, `gh pr comment`, `gh pr review`, `gh pr checkout`, `gh pr merge`, `gh pr checks`
  - Prefer `scripts/prs_update.sh` for PR metadata updates; it can fall back to `gh api` for `--title`, `--body`, and `--base` when `gh pr edit` hits the `read:project` scope issue.
- Workflow actions
  - `gh run list`, `gh run view`, `gh run watch`
- Release actions
  - `gh release list`, `gh release view`, `gh release create`, `gh release edit`, `gh release delete`
  - `scripts/release_plan.sh`, `scripts/release_create.sh`
- General
  - `gh alias`, `gh api`, `gh extension`

Use `--help` on the relevant command for options, and prefer `--json` and `--jq` when scripted output is needed.

## Scope rules

- This skill must not perform organization-level management or settings actions.
- Work on non-current repositories only when the user explicitly provides `owner/repo` (for commands or scripts that support `--repo`).

## Issue and pull request script reference

Use `references/script-summary.md` for the full list of reusable scripts (issues, pull requests, repo operations, and setup checks) with arguments and intent.

## Workflow templates

- `references/workflows.md`: Reusable, copy-ready end-to-end workflows, including PR review-comment, PR check triage, and release/tag creation with explicit default-branch and target-commit confirmation.
- `references/github_workflow_behaviors.md`: Decision policy for issue label suggestion and commit issue-link workflows.

Note (2026-03): issue transfer is standardized with dedicated copy/move scripts after manual transfers proved too easy to run from the wrong repo context.

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

## Issue close standard

- For issue closure, follow this sequence:
  1. verify issue state is open,
  2. post a concise closure note referencing implementation evidence,
  3. close the issue.
- Prefer the dedicated helper script:
  - `scripts/issues_close_with_evidence.sh --issue <number> --commit-sha <sha> [--commit-url <url>] [--pr-url <url>] [--repo <owner/repo>] [--allow-non-project]`
- Closure note template:
  - `Implemented in commit <short_sha> (<commit_url>).`
  - `Implemented via PR <pr_url>.`
- Prefer including both commit and PR links when available.

## Issue transfer standard

- Prefer `scripts/issues_copy.sh` when the source issue should stay open and work should continue in both places.
- Prefer `scripts/issues_move.sh` when work should continue only in the target repository.
- Standard target-body note for copies:
  - `Copied from <source_repo>#<issue> (<source_url>).`
- Standard target-body note for moves:
  - `Moved from <source_repo>#<issue> (<source_url>).`
- Standard source backlink comment for moves:
  - `Moved to <target_repo>#<new_issue> (<new_url>). Continuing work there.`
- Standard move behavior:
  1. create the target issue,
  2. add the backlink comment on the source issue,
  3. close the source issue if it is still open.

## `gh issue view --json` field pitfalls

- `gh issue view --json projects` is invalid and returns `Unknown JSON field: "projects"`.
- Use `projectItems` and/or `projectCards` instead.
- If fields are uncertain, run once with an intentionally invalid field and use the CLI's returned “Available fields” list.

## Repository listing

- Use `scripts/repos_list.sh` for repository discovery commands.

## Installation and setup

- `references/installation.md`: Check whether `gh` is installed and how to install it on common OSes.
- `scripts/check_gh_installed.sh [--min-version <version>]`: Validate that `gh` exists and meets a minimum version.
- `scripts/check_gh_authenticated.sh [--host github.com]`: Verify the active `gh` authentication session for the host.
- `scripts/preflight_gh.sh [--host github.com] [--min-version <version>] [--expect-repo <owner/repo>] [--allow-non-project]`: Run prerequisite checks before other `gh` operations.
- `scripts/release_plan.sh [--repo <owner/repo>] [--target-branch <branch>] [--allow-non-project]`: Resolve the default release target and latest published release tag before mutation.
- `scripts/release_create.sh --tag <tag> --target-ref <branch-or-sha> --notes-mode <infer|blank|user> [--repo <owner/repo>] [--title <text>|--title-file <path>] [--notes-file <path>|--notes-text <text>] [--previous-tag <tag>] [--allow-non-project]`: Create a release with explicit target and explicit notes strategy.
- `scripts/check_docs_script_refs.sh [--skill-dir <path>]`: Verify docs reference valid scripts and documented flags.

## Failure retry matrix

- Auth/session errors (`gh auth status` fails, 401/403 auth):
  - Retry command: `gh auth login && scripts/preflight_gh.sh --host github.com`
- Repository context errors (not a git repo, cannot resolve repo):
  - Retry command: `gh repo view --json nameWithOwner` in the target repo directory, or pass explicit `--repo owner/repo`.
- Repository mismatch errors (`--expect-repo` does not match current directory):
  - Retry command: `scripts/preflight_gh.sh --host github.com --expect-repo owner/repo` from the target repo root, or use `scripts/issues_copy.sh` / `scripts/issues_move.sh` with explicit repo arguments for cross-repo transfers.
- Invalid JSON field errors (for example `Unknown JSON field: "projects"`):
  - Retry command: replace with supported fields, e.g. `gh issue view <n> --json number,title,state,projectItems,projectCards`.
- PR edit scope errors (`gh pr edit` fails with `missing required scopes [read:project]`):
  - Retry command: `scripts/prs_update.sh --pr <n> [--title ...] [--body ...] [--base ...] [--repo owner/repo]` from the target repo root; this helper retries via `gh api` for title/body/base-only updates.
- Transient API/network failures (502/503/timeouts):
  - Retry command: re-run the same `gh ...` command after a short delay; keep scope unchanged.

## Learn

- If command usage or output from `gh` differs from expected behavior, treat the skill as stale.
- When stale behavior is found:
  1. Update the relevant script(s) under `github/scripts/` first.
  2. Update `github/SKILL.md` and `github/references/` docs in the same change set so the instructions stay current.
  3. Record the correction in a short note in the updated docs so future runs use the new behavior.
- Correction note (2026-03): release creation now uses dedicated helper scripts and explicitly distinguishes user silence from explicit delegation when choosing release notes strategy.
- Correction note (2026-03): `gh pr edit` may require `read:project` even for simple metadata updates; `scripts/prs_update.sh` now falls back to `gh api` for title/body/base-only changes when that scope is missing.
- Keep user-facing guidance in `references/` and workflow logic in scripts aligned with tested real-world usage.
