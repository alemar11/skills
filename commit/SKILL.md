---
name: commit
description: Create a well-formed git commit from current changes using session history for rationale and summary; prefer explicit pathspec staging and, in monorepos, default to one subproject per commit unless the user asks for a cross-cutting commit. Use when asked to commit, prepare a commit message, or finalize staged work.
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

## Monorepo Default

If repo docs or the top-level layout show multiple subprojects, packages, apps,
or services, default to one subproject per commit unless the user explicitly
wants a cross-cutting commit.

Typical signals:

- repo guidance explicitly says to split commits by subproject
- multiple top-level folders such as `project-a/`, `project-b/`, `shared/`,
  `infra/`, or `tools/`
- the worktree contains changes across unrelated subproject roots

In these repos:

- prefer separate commits over a single mixed commit
- use explicit pathspec staging per subproject
- if one change truly spans subprojects, confirm that bundling is intentional
  or split the work into sequential commits

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
- Example fast path:
  - one or two already-validated files changed
  - run `git status --short --branch`
  - inspect the relevant `git diff -- <path>`
  - stage only those paths with `git add -- <path>`
  - commit with a short, well-formed message
  - verify sequentially with `git status --short --branch` and `git log -1`

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
   In monorepos, stage by subproject root by default and avoid mixing
   unrelated roots in one commit unless the user asked for that.
   Do not run staging and staged-diff verification in parallel. Finish
   `git add`, then inspect `git diff --staged` or `git diff --staged --stat`
   sequentially so the verification reflects the actual index state.
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
10. Wrap body lines at 72 characters.
11. Create the commit message with a here-doc or temp file and use
    `git commit -F <file>` so newlines are literal (avoid `-m` with `\n`).
12. Commit only when the message matches the staged changes: if the staged diff
    includes unrelated files or the message describes work that isn't staged,
    fix the index or revise the message before committing.
13. After `git commit` succeeds, verify the result sequentially, not in
    parallel with the commit itself. Run `git status --short --branch` and
    `git log -1` to confirm the worktree is clean and `HEAD` matches the new
    commit.

## Speed Guidance

- Prefer the fast path for obvious docs-only or similarly low-risk commits.
- Prefer the safe path whenever there is any chance the commit scope is mixed
  or the resulting behavior needs validation.
- In monorepos, spend a few extra seconds on pathspec staging if it keeps
  subproject boundaries clean; that is usually worth more than shaving one
  command off the workflow.
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
```
