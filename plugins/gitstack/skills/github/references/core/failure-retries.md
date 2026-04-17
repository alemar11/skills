# GitHub failure retry matrix

Use this reference when a `gh` command or `ghops` command fails and you want the
next retry command without re-deriving the fallback path.

- Runtime path errors (`ghops`: no such file or directory):
  - Retry command:
    rerun the same command through the installed plugin path,
    `ghops ...`, instead of assuming the current checkout
    owns the `gitstack` plugin files.
- Auth/session errors (`gh auth status` fails, 401/403 auth):
  - Retry command:
    `gh auth login && ghops --json doctor`
- Repository context errors (not a git repo, cannot resolve repo):
  - Retry command: `gh repo view --json nameWithOwner` in the target repo
    directory, or `gh repo view owner/repo --json nameWithOwner` from
    elsewhere.
- Repository mismatch errors (current checkout does not match the target
  repository):
  - Retry command:
    rerun the same `ghops ... --repo owner/repo` command from the
    correct repo root, or use `ghops issues copy` /
    `ghops issues move` with explicit repo arguments for cross-repo
    transfers.
- Invalid JSON field errors (for example `Unknown JSON field: "projects"`):
  - Retry command: replace with supported fields, e.g.
    `gh issue view <n> --json number,title,state,projectItems,projectCards`.
- PR edit scope errors (`gh pr edit` fails with
  `missing required scopes [read:project]`):
  - Retry command:
    `ghops prs update --pr <n> [--title ...] [--body ...] [--base ...] [--repo owner/repo]`
    from the target repo root; `ghops` retries via `gh api` for
    title/body/base-only updates when needed.
- Transient API/network failures (502/503/timeouts):
  - Retry command: re-run the same `gh ...` command after a short delay; keep
    scope unchanged.
