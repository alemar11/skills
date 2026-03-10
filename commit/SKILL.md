---
name: commit
description:
  Create a well-formed git commit from current changes using session history for
  rationale and summary; use when asked to commit, prepare a commit message, or
  finalize staged work.
---

# Commit

## Goals

- Produce a commit that reflects the actual code changes and the session
  context.
- Follow common git conventions (type prefix, short subject, wrapped body).
- Include both summary and rationale in the body.

## Inputs

- Codex session history for intent and rationale.
- `git status`, `git diff`, and `git diff --staged` for actual changes.
- Repo-specific commit conventions if documented.

## Execution Modes

Choose one of these modes after the initial worktree inspection.

### Fast Path

Use the fast path when the change is tiny, low-risk, and clearly scoped.
Typical signals:

- 1-3 files changed
- docs-only, comments-only, config-only, or rename-only changes
- a clean staged diff already exists, or explicit pathspec staging is obvious
- no mixed unrelated changes in the worktree
- no validation beyond a brief sanity check is needed

In the fast path, keep the workflow lightweight:

- inspect `git status` and the relevant diff once
- stage explicit paths if needed
- write a shorter but still well-formed commit message
- skip extra ceremony that does not materially reduce risk

### Safe Path

Use the safe path by default, and always use it when any of these apply:

- code changes or behavior changes
- multiple subprojects or mixed concerns
- untracked/generated files that may or may not belong in the commit
- validation or tests should run before commit
- the staged diff does not yet clearly match the intended message

## Steps

1. Read session history to identify scope, intent, and rationale.
2. Inspect the working tree and staged changes (`git status`, `git diff`,
   `git diff --staged`).
3. Choose `Fast Path` or `Safe Path`.
4. Stage only the intended changes after confirming scope. Prefer explicit
   pathspecs (for example, `git add -- <path>`) when the change is narrowly
   scoped; use `git add -A` only when all worktree changes are intended for
   the commit.
5. Sanity-check newly added files; if anything looks random or likely ignored
   (build artifacts, logs, temp files), flag it to the user before committing.
6. If staging is incomplete or includes unrelated files, fix the index or ask
   for confirmation.
7. Choose a conventional type and optional scope that match the change (e.g.,
   `feat(scope): ...`, `fix(scope): ...`, `refactor(scope): ...`).
8. Write a subject line in imperative mood, <= 72 characters, no trailing
   period.
9. Write a body that includes:
   - Summary of key changes (what changed).
   - Rationale and trade-offs (why it changed).
   - Tests or validation run (or explicit note if not run).
10. Append a `Co-authored-by` trailer for Codex using `Codex <codex@openai.com>`
   only if the current agent running this commit workflow is Codex.
   If another agent or user is performing the commit, skip this trailer unless
   explicitly requested.
11. Wrap body lines at 72 characters.
12. Create the commit message with a here-doc or temp file and use
    `git commit -F <file>` so newlines are literal (avoid `-m` with `\n`).
13. Commit only when the message matches the staged changes: if the staged diff
    includes unrelated files or the message describes work that isn't staged,
    fix the index or revise the message before committing.
14. After `git commit` succeeds, verify the result sequentially, not in
    parallel with the commit itself. Run `git status --short --branch` and
    `git log -1` to confirm the worktree is clean and `HEAD` matches the new
    commit.

## Speed Guidance

- Prefer the fast path for obvious docs-only or similarly low-risk commits.
- Prefer the safe path whenever there is any chance the commit scope is mixed
  or the resulting behavior needs validation.
- The actual `git commit` command is rarely the slow part; inspection,
  validation, and selective staging are what add time. Spend that time only
  where it reduces real risk.

## Output

- A single commit created with `git commit` whose message reflects the session.

## Template

Type and scope are examples only; adjust to fit the repo and changes.

```
<type>(<scope>): <short summary>

Summary:
- <what changed>
- <what changed>

Rationale:
- <why>
- <why>

Tests:
- <command or "not run (reason)">

(Optional) If this commit is authored by Codex, add:
Co-authored-by: Codex <codex@openai.com>
```
