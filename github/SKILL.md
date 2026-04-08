---
name: github
description: Handle repo-scoped GitHub work plus authenticated-user star and star-list workflows through one repo-owned skill covering triage, reviews, CI, releases, and PR publish or lifecycle flows, with `yeet` reserved for full local-worktree publish.
---

# GitHub

## Overview

Use this skill as the repo-owned umbrella entrypoint for repository-scoped
GitHub work plus authenticated-user star and star-list workflows. It owns
repository orientation, issue lifecycle work, reactions, personal stars and
star lists, PR patch inspection, PR metadata edits, review follow-up, CI
investigation, release or tag flows, and PR publish or lifecycle work.

Breaking change: the GitHub runtime surface is now consolidated. Install
`github` for repo-scoped GitHub work, and add `yeet` plus `git-commit` only
when full local-worktree publish is needed.

Prefer the maintained helper scripts first. Drop to raw `gh` or `gh api` only
when the helper layer does not already cover the job.

Keep commit authoring and staging discipline with the separate `git-commit`
skill, and keep full local-worktree publish in `yeet`.

## Internal domains

| Request type | Domain |
| --- | --- |
| Repository orientation, issue/PR summaries, personal stars and star lists, patch inspection, issue lifecycle, reactions, PR metadata | `triage` |
| Review follow-up, reply, and review submission | `reviews` |
| PR checks and GitHub Actions investigation | `ci` |
| Release-backed tags and tag-only flows | `releases` |
| Current-branch PR open or reuse and PR lifecycle mutations | `publish` |
| Full publish from local checkout to draft PR | `yeet` |

## Trigger rules

- Use for repository-scoped GitHub work in the current repository, an
  explicitly provided `owner/repo`, or authenticated-user star and star-list
  workflows.
- Classify each request into one internal domain: `triage`, `reviews`, `ci`,
  `releases`, or `publish`.
- Route only full publish-from-worktree requests out to `yeet`.
- Reject or reroute organization-level or enterprise-level mutation requests.

## Quick workflow

1. Determine whether the request is repository-scoped or authenticated-user scoped.
2. Enforce repository-only scope for repo mutations and authenticated-user-only scope for stars and star lists.
3. Classify the request by internal domain.
4. Choose the narrowest local helper inside that domain.
5. Route only full local-worktree publish to `yeet`.
6. Use the read-only fast path when it is enough.
7. Run `scripts/core/preflight_gh.sh` before mutating `gh` actions.
8. Restate the resolved target repository, list, PR, issue, or reaction target before mutating anything.

## Scope rules

- This skill must not perform organization-level management or settings actions.
- Work on non-current repositories only when the user explicitly provides
  `owner/repo`.
  - Use each command's supported repo-targeting form or the matching helper's
    `--repo owner/repo` option.
- Authenticated-user star and star-list helpers may run outside a git checkout.
  - For repo-targeted star or list membership operations, require explicit
    `owner/repo` targets.

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
- Use `references/triage/issue-workflows.md` for the exact comment templates,
  move behavior, and `gh issue view --json` field pitfalls.

## Speed defaults

- Use `scripts/triage/repos_view.sh`,
  `scripts/triage/issues_view.sh --summary`, and
  `scripts/triage/prs_view.sh --summary` for routine triage and orientation.
- Use `scripts/triage/stars_manage.sh` for listing, starring, and unstarring
  repositories.
- Use `scripts/triage/lists_manage.sh` for star-list reads, create/delete,
  and repo-to-list membership changes.
- Use `scripts/triage/prs_patch_inspect.sh` for changed-file inspection.
- Use `scripts/reviews/prs_address_comments.sh` for actionable review-thread
  inspection.
- Use `scripts/ci/prs_checks.sh` or `scripts/ci/actions_run_inspect.sh` for
  CI and Actions work.
- Use `scripts/releases/release_plan.sh` for release or tag planning.
- Use `scripts/publish/publish_context.sh` and
  `scripts/publish/prs_open_current_branch.sh` for PR publish or lifecycle
  work after the branch is already ready; pass `--base <branch>` when the
  intended target is a long-lived branch or otherwise differs from the
  repository default branch.
- Use `references/script-summary.md` as the first helper picker; open
  `references/workflows.md` only when the chosen domain needs a fuller runbook.

## Reference map

- `references/script-summary.md`: grouped index of domain helper catalogs.
- `references/workflows.md`: grouped index of domain runbooks.
- `references/triage/issue-workflows.md`: issue close/update/transfer
  standards and issue-view JSON field pitfalls.
- `references/triage/github_workflow_behaviors.md`: decision policy for issue
  label suggestion and commit issue-link workflows.
- `references/core/installation.md`: GitHub CLI installation, auth, and
  preflight setup.
- `references/core/failure-retries.md`: retry commands for auth, repo, and
  helper failure modes.

## References navigation

- Start at `references/script-summary.md` to pick the smallest helper for the
  request.
- Open `references/workflows.md` when you need the full domain runbook before
  executing the task.
- When issue routing is the core problem, open
  `references/triage/issue-workflows.md` first.
- When authentication, CLI setup, or retry behavior is uncertain, open
  `references/core/installation.md` or `references/core/failure-retries.md`.

## Output Expectations

- Restate the resolved target repository, PR, issue, or reaction target before
  mutating anything.
- For repository, issue, or PR triage, prefer concise normalized summaries over
  raw JSON or raw command output.
- For star or star-list work, prefer normalized list summaries and per-repo
  result reporting over raw GraphQL payloads.
- For reaction mutations, report the exact selected targets and whether the run
  was a preview (`--dry-run`) or a real write.
- For read-only requests, return the relevant facts and next useful command or
  action, not raw command noise.
- For failed commands, report the concrete error and the retry command from
  `references/core/failure-retries.md` when one applies.

## Repository listing

- Use `scripts/triage/repos_list.sh` for repository discovery commands.
- Use `scripts/triage/repos_view.sh` for repository orientation in the current
  repo or an explicit `owner/repo`.
- Outside a git repository, pass `--allow-non-project` explicitly for deliberate non-project discovery.

## Learn

- If repeated runtime GitHub work suggests a better helper script, routing
  rule, or reference update, treat that as a runtime learning signal; see
  `references/core/github_skill_learn.md`.
- Prefer improving an existing helper before proposing a new script.
- Keep user-facing guidance in `references/` and workflow logic in scripts aligned with tested real-world usage.

## Examples

- "Summarize this repo and tell me what matters first."
- "Show me the open PRs for this repo and summarize which one needs attention."
- "Show me my starred repos."
- "Show me my GitHub star lists."
- "Add these repositories to my Agent Skills list."
- "Create a list for MCP repos and star this batch."
- "Show me what changed in PR 482."
- "Close issue 77 with the implementation evidence from this commit."
- "Add a thumbs-up reaction to this PR review comment."
- "Debug the failing PR checks."
- "Create a release-backed tag without guessing the target ref."
- "Update the PR title and body without changing review state."
- "Yeet this worktree into a draft PR."
