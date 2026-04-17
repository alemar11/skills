---
name: yeet
description: Orchestrate the full publish flow from a local checkout by choosing branch strategy, using bundled `git-commit` for intentional commits, pushing, and handing off to bundled `github` plus the shared `ghops` CLI for draft PR opening or reuse against the right base branch.
---

# Yeet

## Overview

Use this skill when the user explicitly wants the full publish flow from a
local checkout: inspect scope, create a branch if needed, stage intentionally,
commit, push, and open or reuse a draft pull request.

Inside `gitstack`, this skill is intentionally composed:

- `git-commit` owns selective staging, commit authoring, and post-commit
  verification.
- `github` owns publish-context inspection plus PR opening or reuse after the
  branch is ready or pushed.
- `ghops` is the shared runtime for publish-context and
  publish-open operations.

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
- Route directly to `github` when commit and push are already done, or when
  the request is PR-only lifecycle work.

## Workflow

1. Confirm scope before mutating anything.
   - Start with `git status -sb`.
   - Resolve the current branch, detached-HEAD state, and whether you are still
     on the repository default branch.
   - Run `ghops --json publish context` from the target
     repo root before creating branches, commits, or pushes that are intended
     to end in a PR.
   - Use `ghops --json doctor` only when `gh` install,
     auth, or general runtime readiness is uncertain.
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
   - Hand off to `github` for publish-context inspection plus current-branch PR
     opening or reuse through `ghops publish open`.
   - If step 2 captured an explicit PR base, pass it with `--base <branch>`
     instead of letting the helper fall back to the repository default branch.
   - Let `github` reuse an existing open PR for the current branch
     instead of creating a duplicate.
   - Prefer a PR title that summarizes the full branch-level change, not just
     the latest commit.
   - Prefer a structured, feature-level description with `Feature`, `Impact`,
     `Validation`, and optional `Follow-ups`.
   - Use `--body-from-head` only when the latest commit body already follows
     that PR-ready structure; otherwise pass `--body` explicitly.

## Guardrails

- Never stage unrelated user changes silently.
- Never publish directly from a long-lived branch such as `stable` or
  `release/*`; branch off it and keep that branch as the PR base.
- Never push without confirming scope when the worktree is mixed.
- Never start branch, commit, or push mutations for a PR-intended flow until
  `ghops --json publish context` has passed from the
  target repo root.
- Default to a draft PR unless the user explicitly asks for a ready PR.
- Stop if the repo is not connected to an accessible same-repo GitHub remote.
- Do not vendor or duplicate the bundled `git-commit` or `github` helper
  layers here.

## Fast paths

- Use `git-commit` directly when the job is "make a good commit" without the
  surrounding publish flow.
- Use `github` directly when the branch is already pushed and the only
  remaining step is PR opening or reuse.
- Use `references/workflows.md` for the full local-checkout publish sequence.

## Examples

- "Yeet this worktree."
- "Publish my current branch as a draft PR."
- "I'm on `main`; branch safely, commit this, and open the PR."
- "Commit, push, and open or reuse the PR for these local changes."
