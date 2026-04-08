---
name: yeet
description: Orchestrate the full publish flow from a local checkout by choosing branch strategy, using `git-commit` for intentional commits, pushing, and handing off to `github` for draft PR opening or reuse against the right base branch.
---

# Yeet

## Overview

Use this skill when the user explicitly wants the full publish flow from a
local checkout: inspect scope, create a branch if needed, stage intentionally,
commit, push, and open or reuse a draft pull request.

This skill is intentionally composed. It requires the `git-commit` and
`github` companion skills at runtime:

- `git-commit` owns selective staging, commit authoring, and post-commit
  verification.
- `github` owns current-branch publish context inspection plus PR opening or
  reuse after the branch is ready or pushed.

Keep v1 intentionally narrow:

- same-repo publish only
- no fork-head or cross-repo PR semantics
- no organization-level GitHub actions
- no silent staging of unrelated changes

## Trigger rules

- Use when the user says `yeet` or asks to publish the current worktree from a
  local checkout.
- Use when the request is "commit, push, and open a PR", "publish my current
  branch", or "turn these local changes into a draft PR".
- Keep the current branch only when it is already a non-default, non-long-lived
  local branch.
- Create a new short-lived branch when starting from the repository default
  branch, detached `HEAD`, or a long-lived integration branch such as
  `stable`, `release/*`, `develop`, or `main`.
- Use the active repo or runtime branch-prefix convention for the new branch
  instead of hardcoding `topic/`; if no repo-specific rule exists, use the
  runtime default prefix.
- Route directly to `github` when commit and push are already done, or when
  the request is PR-only lifecycle work.
- If `git-commit` or `github` is unavailable, name the missing
  companion skill and stop instead of re-expanding `yeet` into a standalone
  helper surface.

## Workflow

1. Confirm scope before mutating anything.
   - Start with `git status -sb`.
   - Resolve the current branch, detached-HEAD state, and whether you are still
     on the repository default branch.
   - When useful, run `github/scripts/publish/publish_context.sh --json` from
     the target repo root to confirm whether the current branch is long-lived
     and what PR base should be carried forward.
2. Pick branch strategy.
   - If on the repo default branch or detached `HEAD`, create a new short-lived
     branch before staging and treat the repo default branch as the PR base.
   - If on a long-lived non-default branch, create a new short-lived branch
     from it before staging and remember that original long-lived branch as the
     PR base.
   - If already on a non-default, non-long-lived local branch, keep that branch
     and keep all current changes there.
3. Stage intentionally.
   - Hand off to `git-commit` for selective staging when the worktree is mixed.
   - Use `git add -A` only when the whole worktree is confirmed in scope.
4. Commit with a well-formed message.
   - Hand off to `git-commit` for commit message structure and sequential
     post-commit verification.
5. Push the branch.
   - If there is no upstream, use `git push -u origin <branch>`.
   - Otherwise use `git push origin <branch>`.
6. Open or reuse the draft PR.
   - Hand off to `github` for its `publish` domain helpers:
     `scripts/publish/publish_context.sh` and
     `scripts/publish/prs_open_current_branch.sh --draft`.
   - Execute those helpers from the target repo root even when the helper path
     itself is absolute or lives in another checkout.
   - If step 2 captured an explicit PR base, pass it with `--base <branch>`
     instead of letting the helper fall back to the repository default branch.
   - Let `github` reuse an existing open PR for the current branch
     instead of creating a duplicate.

## Guardrails

- Never stage unrelated user changes silently.
- Never switch a non-default feature branch to a different local branch by
  default.
- Never publish directly from a long-lived branch such as `stable` or
  `release/*`; branch off it and keep that branch as the PR base.
- Never push without confirming scope when the worktree is mixed.
- Default to a draft PR unless the user explicitly asks for a ready PR.
- Stop if the repo is not connected to an accessible same-repo GitHub remote.
- Do not vendor or duplicate the `git-commit` or `github` helper
  layers here.

## Fast paths

- Use `git-commit` directly when the job is "make a good commit" without the
  surrounding publish flow.
- Use `github` directly when the branch is already pushed and the only
  remaining step is PR opening or reuse.
- Use `references/workflows.md` for the full local-checkout publish sequence.

## References navigation

- Read `references/workflows.md` for the complete publish checklist before
  mutating state.
- Open this file’s `Workflow` and `Guardrails` sections first for branching and
  scope decisions.
- If companion-skill availability changes, keep `github` and `git-commit`
  readiness aligned before continuing.

## Reference map

- `references/workflows.md`: composed full publish-from-worktree runbook and
  operator guardrails.

## Examples

- "Yeet this worktree."
- "Publish my current branch as a draft PR."
- "I'm on `main`; branch safely, commit this, and open the PR."
- "Commit, push, and open or reuse the PR for these local changes."
