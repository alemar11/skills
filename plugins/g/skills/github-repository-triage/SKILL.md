---
name: github-repository-triage
description: "Summarize issue and pull-request queues, blockers, and next actions read-only."
---

# GitHub Repository Triage

Before any shell command that may contact GitHub or a package registry, read
and follow [Network execution](../../references/network-execution.md).

## Transport

Use authenticated `gh` directly for explicitly selected repositories. Before
provider reads, complete the
[gh preflight](../../references/gh-dependency-preflight.md).
This skill never performs GitHub writes; route every write-shaped request to
its owning skill.

## Role

Return a concise, URL-first queue assessment. Use `g:github-issues` for
classification, `g:github-investigation` for disposition analysis, and
`g:github-issues` for decided mutations. Triage itself is read-only.

## Workflow

1. Resolve the repository scope:
   - When the user identifies no repository, use the current repository.
   - When the user identifies one repository, use the detailed queue path.
   - When the user identifies multiple repositories or supplies a repo file,
     require explicit `owner/repo` identities and use the comparative scan.
2. For one repository, confirm context with
   `gh repo view --json nameWithOwner,url`. Gather open issues and PRs, inspect
   only the items needed for the
   queue question, and group them by blocker, stale item, ready-for-review,
   CI/review need, or follow-up owner.
3. Read [workflows.md](references/workflows.md) for direct queue reads and
   multi-repository comparison. Report coverage and per-repository failures;
   do not present sampled inventories as complete counts.
4. When queue work identifies one exact issue that needs content-based label or
   type selection, route it to `$g:github-issues`; do not choose metadata from a
   queue summary.
   When the user instead requests a taxonomy proposal, route the exact
   repository and corpus context to that skill; do not invent new labels from
   the triage summary alone.
5. Do not edit labels, milestones, assignees, titles, comments, releases, or
   workflows from this skill; route predetermined authorized GitHub issue
   lifecycle mutations to `$g:github-issues` only after normalizing the handoff to
   `mutation_mode=apply`, the exact repository and issue target, and one
   canonical `issue_operation`. Route an explicit mutation preview with
   `mutation_mode=dry-run` and the same exact target and operation. Pure queue
   reads omit both fields.
6. Route evidence-backed issue disposition questions, including whether an
   issue should close or partial work satisfies its acceptance criteria, to
   `$g:github-investigation`. Route any authorized resulting lifecycle
   mutation to `$g:github-issues`.

## References

- `references/workflows.md`: single- and multi-repository triage workflows.
- `../../references/options.md`: canonical G invocation fields for routed handoffs.
