---
name: github-repository-triage
description: "Summarize issue and pull-request queues, blockers, and next actions read-only."
---

# GitHub Repository Triage

Before any shell command that may contact GitHub or a package registry, read
and follow [Network execution](../../references/network-execution.md).

## Transport

Use authenticated `gh` for provider reads. Use the read-only portfolio scanner
for multiple explicit repositories and direct `gh` for one-repository detail.
This skill never performs GitHub writes; route every write-shaped request to
its owning skill.

Before the first provider-facing direct `gh` or shared CLI operation, load
[`../../references/gh-dependency-preflight.md`](../../references/gh-dependency-preflight.md)
and require its host and authentication checks.

## Role

Return a concise, URL-first queue assessment. Use `g:github-issues` for
classification, `g:github-investigation` for disposition analysis, and
`g:github-issues` for decided mutations. Triage itself is read-only.

## Multi-Repository Script

Resolve `<plugin-root>` as two directories above the directory containing this
`SKILL.md`, then invoke the helper from the installed plugin root. Do not
assume the current checkout contains the G source tree.

```bash
<plugin-root>/scripts/g portfolio scan --help
<plugin-root>/scripts/g --version
<plugin-root>/scripts/g --json doctor
```

The script accepts repeated explicit `owner/repo` inputs or a user-supplied
repo file, emits stable JSON success/error envelopes in JSON mode, preserves
per-repository failures, and writes no implicit config.

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
3. For multiple repositories, run
   `<plugin-root>/scripts/g portfolio scan` and summarize queue size,
   blocking CI, release gaps, and next actions per repository. Preserve
   per-repository failures instead of hiding the rest of the scan.
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
- `references/script-summary.md`: `g portfolio scan` command contract.
- `../../references/options.md`: canonical G invocation fields for routed handoffs.
