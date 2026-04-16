---
name: github
description: Handle repo-scoped GitHub work plus authenticated-user star and star-list workflows through one repo-owned skill covering triage, reviews, CI, releases, and PR publish or lifecycle flows, with `yeet` reserved for full local-worktree publish.
---

# GitHub

## Overview

Use this skill as the repo-owned GitHub runtime entrypoint for repository-scoped
GitHub work plus authenticated-user star and star-list workflows.

Breaking change: the only supported runtime entrypoint is `scripts/ghops`.
Do not use or reintroduce the older per-domain `scripts/{triage,reviews,ci,releases,publish}/...`
surface as a public runtime path.

Keep commit authoring and staging discipline with the separate `git-commit`
skill, and keep full local-worktree publish in `yeet`.

## Runtime surface

- `scripts/ghops` is the only supported runtime entrypoint.
- When the current checkout does not contain `scripts/ghops`, resolve the
  installed `github` skill root first and run `<skill-root>/scripts/ghops`
  instead of falling back to legacy per-domain scripts.
- `scripts/ghops --version` is the runtime version check.
- `scripts/ghops --json doctor` is the runtime readiness check.
- The maintained runtime implementation lives under `projects/ghops/src/ghops/`.
- Do not treat `scripts/{triage,reviews,ci,releases,publish}/...` as the public
  runtime surface.

## Internal domains

These still organize the implementation and references behind `ghops`:

| Request type | Domain |
| --- | --- |
| Repository orientation, issue/PR summaries, personal stars and star lists, patch inspection, issue lifecycle, reactions, PR metadata | `triage` |
| Review follow-up, reply, and review submission | `reviews` |
| PR checks | `checks` |
| Generic GitHub Actions investigation | `actions` |
| Release-backed tags and tag-only flows | `releases` |
| Current-branch PR open or reuse and PR lifecycle mutations | `publish` |
| Full publish from local checkout to draft PR | `yeet` |

## Trigger rules

- Use for repository-scoped GitHub work in the current repository, an
  explicitly provided `owner/repo`, or authenticated-user star and star-list
  workflows.
- Stay in `github` for triage, reviews, checks, generic Actions, releases, and
  publish or lifecycle work.
- Route only full publish-from-worktree requests out to `yeet`.
- Reject or reroute organization-level or enterprise-level mutation requests.

## Quick workflow

1. Determine whether the request is repository-scoped or authenticated-user scoped.
2. Resolve the shipped `ghops` artifact. Use `scripts/ghops` when the current
   checkout has it; otherwise run `<resolved-skill-root>/scripts/ghops`.
3. Start with `scripts/ghops --json doctor` when auth or repo context is uncertain.
4. Choose the narrowest `ghops` noun/verb for the task.
5. Use `--json` when parsing or relaying structured results.
6. Route only full local-worktree publish to `yeet`.
7. Restate the resolved target repository, list, PR, issue, or reaction target before mutating anything.

## Fast path

- Runtime readiness:
  - `scripts/ghops --json doctor`
- Repository orientation:
  - `scripts/ghops repos view`
  - `scripts/ghops --json repos list --limit 20`
- Issue triage:
  - `scripts/ghops issues view --issue 123 --repo owner/repo`
  - `scripts/ghops --json issues list --repo owner/repo --state open --limit 20`
- Pull request triage:
  - `scripts/ghops prs view --pr 42 --repo owner/repo`
  - `scripts/ghops --json prs patch --pr 42 --repo owner/repo`
- Review follow-up:
  - `scripts/ghops reviews address --pr 42 --repo owner/repo`
- PR checks:
  - `scripts/ghops --json checks pr --pr 42 --repo owner/repo`
- Generic Actions runs:
  - `scripts/ghops --json actions list --repo owner/repo --limit 10`
- Authenticated-user stars and star lists:
  - `scripts/ghops --json stars list`
  - `scripts/ghops --json lists list`
- Release planning:
  - `scripts/ghops releases plan --repo owner/repo`
- Current-branch PR publish lifecycle:
  - `scripts/ghops --json publish context`
  - `scripts/ghops publish open --draft`

## Command map

- `doctor`
  - Runtime readiness, `gh` install/auth state, and local repo detection.
- `repos`
  - `list`, `view`
- `issues`
  - `list`, `view`, `create`, `update`, `comment`, `comments`, `close`,
    `reopen`, `close-with-evidence`, `copy`, `move`, `lock`, `unlock`,
    `pin`, `unpin`, `suggest-labels`
  - `labels list|create|update|delete`
  - `milestones list`
- `prs`
  - `list`, `view`, `patch`, `update`
- `reactions`
  - `list`, `add`, `remove`
- `reviews`
  - `address`, `comment`, `comments`, `review-comments`, `review`
- `checks`
  - `pr`
- `actions`
  - `list`, `inspect`
- `stars`
  - `list`, `add`, `remove`
- `lists`
  - `list`, `items`, `create`, `delete`, `assign`, `unassign`
- `releases`
  - `plan`, `notes`, `create`
- `publish`
  - `context`, `open`, `create`, `draft`, `ready`, `merge`, `close`,
    `reopen`, `checkout`
- `request`
  - `get`

## Scope rules

- This skill must not perform organization-level management or settings actions.
- Work on non-current repositories only when the user explicitly provides
  `owner/repo`, unless the selected `ghops` command resolves the current repo
  from the local checkout.
- Authenticated-user star and star-list helpers may run outside a git checkout.
- For repo-targeted star or list membership operations, require explicit
  `owner/repo` targets.
- `request get` is the only raw escape hatch in phase 1. Keep it read-only.

## JSON and output

- Use `--json` only at the `ghops` level:
  - `scripts/ghops --json <noun> <verb> ...`
- `--json` returns a CLI envelope, not raw provider payloads:
  - success: `{"ok": true, "version": "...", "command": [...], "data": ...}`
  - error: `{"ok": false, "version": "...", "command": [...], "error": {...}}`
- `doctor --json` must remain machine-readable even when `gh` is missing or
  auth is missing.
- `actions inspect --json` is summary-only and rejects mixed-output modes such
  as `--job-id` or `--artifact-name`.
- `request get` rejects raw mutating `gh api` flag forms, including compact and
  `--flag=value` variants.
- Never print full tokens, cookies, or raw `gh auth status` dumps in JSON.

## References navigation

- Start at `references/script-summary.md` for the public `ghops` entrypoint and
  the command-map index behind it.
- Open `references/workflows.md` when you need the full domain runbook before
  executing the task.
- When issue routing is the core problem, open
  `references/triage/issue-workflows.md` first.
- When authentication, CLI setup, or retry behavior is uncertain, open
  `references/core/installation.md` or `references/core/failure-retries.md`.

## Learn

- If repeated runtime GitHub work suggests a better `ghops` route, command
  contract, or reference update, treat that as a runtime learning signal; see
  `references/core/github_skill_learn.md`.
- Prefer improving an existing `ghops` command or the `projects/ghops/`
  implementation before proposing a new runtime command.
- Keep user-facing guidance in `references/` aligned with the shipped
  `scripts/ghops` runtime behavior.

## CLI Maintenance

- Keep normal execution on the shipped `ghops` artifact: `scripts/ghops` from
  the owning checkout, or `<skill-root>/scripts/ghops` when operating from a
  different repository.
- Treat `projects/ghops/` as the maintained Python project behind the shipped
  artifact at `scripts/ghops`.
- Treat `projects/ghops/pyproject.toml` as the CLI semver source of truth, and
  use `scripts/ghops --version` to verify the shipped runtime version.
- Open `projects/ghops/` when fixing bugs, improving performance, rebuilding,
  or extending the `ghops` contract.
- Keep runtime logic in `projects/ghops/src/ghops/`; do not add new runtime
  behavior anywhere else.
- Do not add compatibility aliases or runtime shims for the older public
  per-domain script surface.
- Keep normal skill users on `scripts/ghops`; do not direct them to run Python
  directly from `projects/ghops/`.
- Treat any future build outputs outside `scripts/ghops` as intermediates, not
  supported runtime entrypoints.
- Follow semver for shipped CLI changes:
  - major for breaking CLI contract changes
  - minor for backward-compatible new features or meaningful capability
    additions
  - patch for backward-compatible bug fixes and corrections
- After maintenance changes, re-verify through the shipped artifact with:
  - `scripts/ghops --help`
  - `scripts/ghops --version`
  - `scripts/ghops --json doctor`

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
