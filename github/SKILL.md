---
name: github
description: Handle repo-scoped GitHub triage, issue lifecycle, reactions, PR metadata, and route specialist GitHub workflows inside the full GitHub skill suite.
---

# GitHub

## Overview

Use this skill as the repo-owned umbrella entrypoint for repository-scoped
GitHub work. It owns repository orientation, issue lifecycle work, reactions,
PR patch inspection, and PR metadata edits. It also routes specialized review,
CI, release/tag, and PR publish requests to the matching companion skills.

Breaking change: the GitHub split is intentional. Standalone `github` installs
are no longer the supported path for review, CI, release/tag, or PR
publish/lifecycle work. Install the full GitHub suite (`github`,
`github-reviews`, `github-ci`, `github-releases`, and `github-publish`) when
those workflows need to run.

Prefer the maintained helper scripts first. Drop to raw `gh` or `gh api` only
when the helper layer does not already cover the job.

Keep commit authoring and staging discipline with the separate `commit` skill.

## Ownership

| Request type | Owner |
| --- | --- |
| Repository orientation, issue/PR summaries, PR patch inspection | `github` |
| Issue lifecycle, label suggestion, reactions, PR metadata edits | `github` |
| Review follow-up and review submission | `github-reviews` |
| PR checks and GitHub Actions investigation | `github-ci` |
| Release-backed tags and tag-only flows | `github-releases` |
| PR opening and PR lifecycle mutations | `github-publish` |

## Trigger rules

- Use for repository-scoped GitHub work in the current repository or an
  explicitly provided `owner/repo`.
- Use directly for repository orientation, issue or PR summaries, patch
  inspection, issue lifecycle mutations, reactions, and PR metadata edits.
- Route review follow-up to `github-reviews`, CI debugging to `github-ci`,
  release/tag work to `github-releases`, and PR publish/lifecycle work to
  `github-publish`.
- If a routed specialist skill is unavailable, name the missing companion
  skill, note that the split is intentionally breaking for standalone
  `github`, and stop instead of stretching the umbrella into that workflow.
- Reject or reroute organization-level or enterprise-level mutation requests.

## Quick workflow

1. Determine project scope first.
2. Enforce repository-only scope.
3. Classify the request by owner.
4. If the task is umbrella-owned, choose the narrowest local helper.
5. If the task belongs to a companion skill, route immediately instead of
   carrying specialist procedure detail here.
6. Use the read-only fast path when it is enough.
7. Run `scripts/preflight_gh.sh` before mutating `gh` actions.
8. Restate the resolved target repository, PR, issue, or reaction target
   before mutating anything.

## Scope rules

- This skill must not perform organization-level management or settings actions.
- Work on non-current repositories only when the user explicitly provides
  `owner/repo`.
  - Use each command's supported repo-targeting form or the matching helper's
    `--repo owner/repo` option.

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

## Speed defaults

- Use `scripts/repos_view.sh`, `scripts/issues_view.sh --summary`, and
  `scripts/prs_view.sh --summary` for routine triage and orientation.
- Use `scripts/prs_patch_inspect.sh` for changed-file inspection.
- Use `scripts/reactions_manage.sh` for reaction work, including PR review
  comment reactions.
- Use `scripts/prs_update.sh` for PR metadata edits.
- Use `references/script-summary.md` as the first helper picker; open
  `references/workflows.md` only when the umbrella-owned workflow needs a
  fuller runbook.

## Reference map

- `references/script-summary.md`: authoritative helper catalog and documented
  script flags.
- `references/workflows.md`: reusable umbrella-owned workflows for PR metadata,
  issues, reactions, patch inspection, and commit-close wording.
- `references/issue-workflows.md`: issue close/update/transfer standards and
  issue-view JSON field pitfalls.
- `references/github_workflow_behaviors.md`: decision policy for issue label
  suggestion and commit issue-link workflows.
- `references/installation.md`: GitHub CLI installation, auth, and preflight
  setup.
- `references/failure-retries.md`: retry commands for umbrella-owned auth,
  repo, and PR metadata failure modes.

## Output Expectations

- Restate the resolved target repository, PR, issue, or reaction target before
  mutating anything.
- For repository, issue, or PR triage, prefer concise normalized summaries over
  raw JSON or raw command output.
- For reaction mutations, report the exact selected targets and whether the run
  was a preview (`--dry-run`) or a real write.
- For read-only requests, return the relevant facts and next useful command or
  action, not raw command noise.
- For failed commands, report the concrete error and the retry command from
  `references/failure-retries.md` when one applies.

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
- "Close issue 77 with the implementation evidence from this commit."
- "Add a thumbs-up reaction to this PR review comment."
- "Update the PR title and body without changing any review state."
