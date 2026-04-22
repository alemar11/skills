# GitHub workflows

Use this as the top-level runbook index referenced by the bundled `github` skill.
Choose the direct `gh` or `git` path first, then open the matching detailed
workflow document when the domain needs deeper guidance or one of the remaining
shared `ghflow` helpers is actually justified.

## Domain runbooks

- Triage-owned repository, authenticated-user star or star-list, issue, and PR
  metadata flows:
  `references/triage/workflows.md`
- Review-thread inspection, reply, and review submission:
  `references/reviews/workflows.md`
- PR checks and generic GitHub Actions investigation:
  `references/ci/workflows.md`
- Release-backed tags, tag-only flows, and release publication:
  `references/releases/workflows.md`
- Current-branch PR open or reuse and PR lifecycle mutations:
  `references/publish/workflows.md`

## Routing rules

- Stay on direct `gh` or `git` commands by default, and switch to `ghflow`
  only for focused failing-PR CI inspection, review-thread routing,
  authenticated-user stars or star lists, and current-branch publish helpers.
- Route only full local-worktree publish to `yeet`.
- Use `references/core/failure-retries.md` when the chosen `ghflow` command
  fails and you need the next retry path quickly.
