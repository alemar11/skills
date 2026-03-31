# GitHub failure retry matrix

Use this reference when a `gh` command or GitHub helper fails and you want the
next retry command without re-deriving the fallback path.

- Auth/session errors (`gh auth status` fails, 401/403 auth):
  - Retry command: `gh auth login && scripts/preflight_gh.sh --host github.com`
- Repository context errors (not a git repo, cannot resolve repo):
  - Retry command: `gh repo view --json nameWithOwner` in the target repo
    directory, or `gh repo view owner/repo --json nameWithOwner` from
    elsewhere.
- Repository mismatch errors (`--expect-repo` does not match current
  directory):
  - Retry command: `scripts/preflight_gh.sh --host github.com --expect-repo owner/repo`
    from the target repo root, or use `scripts/issues_copy.sh` /
    `scripts/issues_move.sh` with explicit repo arguments for cross-repo
    transfers.
- Invalid JSON field errors (for example `Unknown JSON field: "projects"`):
  - Retry command: replace with supported fields, e.g.
    `gh issue view <n> --json number,title,state,projectItems,projectCards`.
- PR edit scope errors (`gh pr edit` fails with
  `missing required scopes [read:project]`):
  - Retry command: `scripts/prs_update.sh --pr <n> [--title ...] [--body ...] [--base ...] [--repo owner/repo]`
    from the target repo root; this helper retries via `gh api` for
    title/body/base-only updates.
- Transient API/network failures (502/503/timeouts):
  - Retry command: re-run the same `gh ...` command after a short delay; keep
    scope unchanged.
