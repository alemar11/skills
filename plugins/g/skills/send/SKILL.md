---
name: send
description: "Commit and push scoped changes, then create or update one PR while preserving existing draft state."
---

# Send

Before any shell command that may contact GitHub or a package registry, read
and follow [Network execution](../../references/network-execution.md).

## Role

Publish one branch and PR. Compose `g:git-commit` for commit authoring; Send owns
the push, base selection, PR body, and publication readback. Reuse an existing
suitable commit and matching PR.

Use `<plugin-root>/scripts/g publish preflight` and `publish open` for a new PR;
use file-backed `gh api --input` for existing title/body changes. Keep provider
text out of shell strings and argv. Before a provider operation, read
[gh preflight](../../references/gh-dependency-preflight.md).
The plugin root is two directories above the directory containing this file.

For issue-only work or no publishable changes, use the relevant G owner instead
of running publication. Single-PR publication does not imply stack management.

## Base Selection And Existing PR Reuse

Resolve the PR base branch before committing or pushing. Use the explicit base
branch supplied by the caller for a new PR; otherwise use the repository default
branch. A non-default explicit base is valid and is not evidence of a stack.
Never treat the worker or feature head branch as the PR base merely because it
is named `target_branch_name`.

When the current branch already has exactly one matching open PR, that PR is the
publication target. Without an explicit base, preserve its read-back
`baseRefName`; with an explicit base, require it to equal that existing base.
Stop on a missing or ambiguous base instead of retargeting the PR or silently
falling back to the default branch. Preserve its current `isDraft` value.

Send does not infer, verify, link, or manage a stack. A caller that needs a
parent/child relationship invokes `$g:github-stack` separately after Send's
publication receipt. Do not use `stack submit` as a Send fallback.

## Issue Linkage Contract

Accept `closing_issue_refs` as caller-owned factual input: the exact GitHub
issues whose accepted scope is fully satisfied by this PR. Validate every
candidate against its exact GitHub repository and issue before PR mutation.
Send must not derive an issue from a bare number, branch name, commit subject,
nearby issue, parent Feature Spec, dependency, or partial implementation.

When `closing_issue_refs` is nonempty:

- include one canonical `Closes` line per deduplicated issue under `## Issues`
  in the PR description, using `Closes #<number>` for the PR repository and
  `Closes <owner>/<repository>#<number>` for another repository;
- preserve and union valid closing references already present when updating a
  PR, without replacing unrelated template or author content;
- stop on conflicting, ambiguous, missing, or only partially satisfied issue
  evidence rather than adding a closing keyword that could close the wrong
  issue.

The selected PR base does not change this validation. Send carries the exact
caller-provided issue set to the PR body and verifies the resulting body and
provider references; it does not decide whether the current delivery topology
will make GitHub close those issues or mutate an issue directly. A composing
workflow such as Implement owns the standalone/stacked interpretation and any
separate post-publication delivery verification.

When no issue is confirmed, omit `## Issues` rather than inventing a placeholder
or asking merely to fill the section. Report the empty linkage result in the
closeout. See `references/workflows.md` for body construction and verification.

## Workflow

1. Run the complete publish preflight before any push: require a named branch,
   reject the repository default branch, verify `gh` authentication, verify the
   `origin` repository and any configured upstream match the current branch,
   and look up an existing open PR for that branch. The shared network execution
   contract applies to the complete GitHub-dependent preflight from the outset.
2. Resolve the intended base using **Base Selection And Existing PR Reuse**.
   Capture the existing PR's exact base when reusing it; stop on explicit-base
   drift and repeat the base read-back after the commit/preflight boundary.
3. Inspect worktree state and confirm the intended scope when it is mixed.
4. Receive and validate the caller's exact `closing_issue_refs`. Read an
   existing PR body when present, preserve its valid closing references, and
   prepare the complete template-aware PR body. Do not impose a default-base
   requirement in Send.
5. Reuse the current commit when it already represents the intended scope.
   Otherwise create one through `$g:git-commit` with
   `commit_operation=commit-only`; Send retains ownership of push. Do not
   override Git Commit's `commit_kind` selection: it defaults to `regular` and
   may select a targeted fixup only from the explicit request or
   target-repository instructions with an exact target.
6. Rerun the complete publish preflight immediately before pushing and repeat
   the existing-PR/base read-back. The selected base must still agree with the
   explicit target or preserved existing PR; otherwise stop and reconcile the
   changed remote state. Use a normal push to the verified upstream, or `git push
   -u origin HEAD` only when no upstream exists. Never infer permission to
   force-push.
7. Re-check for an existing PR after push. Open a draft PR only when none
   exists; otherwise update the existing PR without changing its `isDraft`
   value. In particular, a ready PR must remain ready; never call a draft
   conversion or the draft-only creation path for an existing PR. After an
   ambiguous create failure, look up the PR again before retrying so a
   successful first request cannot create a duplicate. Read back the PR body
   and require the exact canonical `Closes` line for every resolved
   `closing_issue_ref`. Preserve the existing PR's base and draft state; never
   retarget it implicitly.
8. Stop after publication and its read-backs. Send must not request or wait for
   an automated Codex review. If a composing workflow needs one, it must invoke
   `$g:github-review-threads` as a separate operation using the exact repository,
   PR, and full published head SHA from Send's publication evidence. The ready
   transition and any automatic provider review remain outside Send.
9. Return branch, PR URL, commit hash, PR base, canonical
   `closing_issue_refs`, issue-linkage verification, exact published head,
   draft-state read-back, and verification performed. If post-publication
   verification fails after the push or PR mutation succeeded, preserve and
   report the successful publish evidence separately; do not repeat the push or
   PR creation blindly.

## References

- `references/workflows.md`: publish, existing-PR, and retry workflows.
- `../../references/options.md`: shared canonical G options.
