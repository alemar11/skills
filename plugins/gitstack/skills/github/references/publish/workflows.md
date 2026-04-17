# GitHub publish workflows

Use this reference for current-branch publish context inspection, current-branch
PR opening or reuse, and PR lifecycle mutations.

## publish-context

Purpose: inspect whether the current branch is ready for PR opening and whether
an open PR already exists.

### Preconditions

- `gh` installed and authenticated.
- You are inside a local git checkout of the target repository.

### Operator policy

- Use this command before mutation when the branch, upstream, or open-PR state
  is not already known.
- Prefer it as the post-push handoff point from `yeet`.
- Run it from the target repository root so the local checkout and resolved
  repository stay aligned.
- Use its `current_branch_is_long_lived` and `recommended_pr_base` output to
  carry the right PR base forward when `yeet` branched off a long-lived
  integration branch.

### Preferred command

```bash
ghops --json publish context [--repo <owner/repo>]
```

## pr-open-current-branch

Purpose: open or reuse a PR from the already-pushed current branch without
staging, committing, or pushing.

### Preconditions

- `gh` installed and authenticated.
- Run `ghops --json doctor` first when repo context is uncertain.
- The current branch is pushed to a same-name remote branch.

### Operator policy

- Prefer `ghops publish context` first when the branch, upstream, or
  open-PR state is not already obvious.
- Prefer `ghops publish open` when the request is about the current
  pushed branch.
- Run the command from the target repository root.
- Stop when the branch has no upstream or the upstream branch name differs from
  the local branch name.
- Reuse an existing open PR for the current branch instead of creating a
  duplicate.
- If `yeet` branched from a long-lived branch such as `stable` or `release/*`,
  pass `--base <that-branch>` explicitly instead of letting the command fall
  back to the repository default branch.
- Prefer a structured, feature-level PR body with `Feature`, `Impact`,
  `Validation`, and optional `Follow-ups`.
- Use `--body-from-head` only when the latest commit body is intentionally
  written in that PR-ready format; otherwise pass `--body` explicitly.
- If an open PR already exists for the current branch but targets a different
  base than the requested `--base`, stop and update the PR base explicitly
  instead of silently reusing the wrong target.
- Do not stretch this flow into staging, commit creation, branch creation, or
  pushing.
- If the user wants the full local-checkout publish flow, route to `yeet`
  instead of composing it from this skill.

### Preferred command

```bash
ghops publish open [--title <text>] [--body <text>] [--body-from-head] [--base <branch>] [--draft] [--repo <owner/repo>] [--dry-run]
```

Suggested PR body shape:

```text
Feature:
- <macro summary of the feature, fix, or behavior change>

Impact:
- <user-facing effect, API behavior, or operational effect>

Validation:
- <command or "not run (reason)">

Follow-ups:
- <optional rollout note, TODO, or risk>
```

## pr-lifecycle

Purpose: create a PR from explicit refs or mutate existing PR lifecycle state.

### Operator policy

- Use `ghops publish create` when `head` and `base` are explicit.
- Use `ghops publish draft`, `ghops publish ready`,
  `ghops publish merge`, `ghops publish close`, and
  `ghops publish reopen` for remote lifecycle mutations.
- Use `ghops publish checkout` only when the local checkout side effect
  is acceptable and has been restated to the user.
- Keep PR metadata edits in umbrella `github`.

### Preferred commands

```bash
ghops publish create --title <text> [--body <text>] [--base <branch>] [--head <branch>] [--draft] [--labels <label1,label2>] [--repo <owner/repo>]
ghops publish ready --pr <number> [--repo <owner/repo>]
ghops publish draft --pr <number> [--repo <owner/repo>]
ghops publish merge --pr <number> [--merge|--squash|--rebase] [--delete-branch] [--admin] [--auto] [--repo <owner/repo>]
ghops publish close --pr <number> [--repo <owner/repo>]
ghops publish reopen --pr <number> [--repo <owner/repo>]
ghops publish checkout --pr <number> [--branch <name>] [--detach] [--force] [--recurse-submodules] [--repo <owner/repo>]
```

## Retry notes

- Auth/session errors: `gh auth login && ghops --json doctor`
- Repository mismatch errors: rerun the command from the target repo root or
  pass `--repo owner/repo` explicitly.
- Current branch has no upstream or same-name remote branch: run
  `git push -u origin $(git branch --show-current)` from the target repo root,
  then rerun `ghops publish context` or `ghops publish open`.
- Detached HEAD during current-branch PR opening: switch back to a branch
  first, then rerun `ghops publish open`.
