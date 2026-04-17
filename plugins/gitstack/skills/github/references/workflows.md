# GitHub workflows

Use this as the top-level runbook index referenced by `github/SKILL.md`.
Choose the `ghops` runtime path first, then open the matching detailed workflow
document when the domain needs deeper guidance.

## Domain runbooks

- Triage-owned repository, authenticated-user star/list, issue, PR metadata,
  reaction, and issue-link flows:
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

- Stay on `ghops` for runtime execution across triage, reviews,
  checks, generic Actions, releases, and publish or lifecycle work.
- Route only full local-worktree publish to `yeet`.
- Use `references/core/failure-retries.md` when the chosen `ghops` command
  fails and you need the next retry path quickly.
