---
name: git-commit
description: "Create local Git commits or push them when requested. Use $g:send for pull-request publication."
---

# Git Commit

Before any shell command that may contact GitHub or a package registry, read
and follow [Network execution](../../references/network-execution.md).

## Core Rule

Use direct `git` commands. The only bundled helper is the target-aware editor
adapter for noninteractive amend-fixup messages; it never stages, commits,
rebases, or pushes.

Resolve the user request to
`commit_operation=commit-only|commit-and-push|push-only`, then use the workflow below.

Escalate to broader diff review or split commits only when the worktree is
mixed, generated files are involved, or the staged scope is still unclear.

For a commit-producing operation, resolve
`commit_kind=regular|fixup|amend-fixup`. Default to `regular`. Select a fixup
kind only when the user explicitly requests it or target-repository
instructions require it; review feedback by itself never selects a fixup.
Require an exact `target_commit`, resolve it to one ancestor commit, and verify
that the staged refinement maps cleanly to that target. Because Git's generated
fixup matcher uses the target subject, require that subject to be unique in all
history reachable from `HEAD`. Stop when the target is missing, ambiguous,
outside the current history, subject-ambiguous, or does not own the change.
Never amend the target in place and never autosquash fixup commits.

If the user asks for a PR, draft PR, branch publication, or "send", use
`$g:send` instead. `commit_operation=push-only` never creates a commit;
`commit_operation=commit-and-push` does both operations. When the user
explicitly authorizes direct-to-main issue closure, use issue-closing commit
trailers such as `Closes #123` only after staging the intended paths and
verifying the diff and only with `commit_kind=regular`; never add trailers to
Git-generated fixup messages. Route GitHub issue comments, labels, type changes,
follow-up issue creation, or manual closure to `$g:github-issues`.

## Workflow

1. Inspect the worktree with `git status --short --branch`, then inspect and
   record the pre-existing index with `git diff --staged --name-status` before
   running any `git add` command.
2. If unrelated changes are already staged, stop by default without resetting
   or rewriting the user's index. Continue only after the unrelated staged work
   is committed separately, or isolate fully reviewed intended path contents
   with the path-limited workflow in `references/workflows.md` when that scope
   is explicit. Do not use path-limited commit isolation for partial-hunk work.
3. For small cohesive work, inspect only the intended files first. Expand to
   `git diff --stat` or broader review only when the scope is mixed or unclear.
4. For `commit_kind=fixup|amend-fixup`, resolve `target_commit` to a full SHA,
   prove it is an ancestor of `HEAD`, inspect its subject and diff, and confirm
   that the intended changes belong to that one logical commit.
5. Stage only intended paths with explicit pathspecs such as
   `git add -- <path>`.
6. Re-check `git diff --staged` before committing, and compare its path set with
   the recorded pre-existing staged set and the intended commit scope.
7. For `commit_kind=regular`, write a concise imperative subject and a body with
   summary, rationale, and validation. For `fixup`, let Git generate the
   `fixup!` message. For `amend-fixup`, provide the complete replacement subject
   and body while preserving Git's target-derived `amend!` matcher; use the
   bundled editor adapter when execution is noninteractive.
8. Run the command for the selected kind from `references/workflows.md`.
9. Verify with `git status --short --branch` and
   `git log -1 --pretty=fuller`.
10. For `commit_operation=commit-and-push`, use `git push` or
   `git push -u origin HEAD`; for `push-only`, verify the existing commit range
   and push without staging or committing.

## References

- `references/workflows.md`: commit, split-commit, and push-only workflows.
- `../../references/options.md`: shared canonical G options.
- `scripts/replace-amend-fixup-message`: noninteractive editor adapter that
  preserves Git's target-derived amend-fixup matcher.
- `scripts/validate-fixup-target`: resolve one ancestor target and reject a
  subject that could make a later autosquash ambiguous.
