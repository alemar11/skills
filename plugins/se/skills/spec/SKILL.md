---
name: spec
description: "Create or revise feature specs and task plans on explicit request; save to GitHub or Markdown and offer delivery authorization."
---

# Feature Specification

Produce one coherent spec and an ordered, verifiable task plan from the current
discussion, supplied references, or an existing spec. One
outcome may span repositories. Planning does not implement code, create branches
or PRs, change execution progress, or start Delivery implicitly.

## Current session

Work in the invoking session with its configured model and reasoning. Once the
outcome is clear, update the current task title to `📚 Plan Feature · <outcome>`
when supported. Invocation authorizes this title update; do not create or fork
a planner task. If renaming is unavailable or fails, continue planning and
briefly report the limitation. Titles do not establish spec or repository identity.

Follow the shared [execution scope](../../references/execution-scope.md).
Optional bounded research or draft review may use the corresponding role in
[subagents.md](../../references/subagents.md); read that role before delegation.
Keep ownership of the complete spec here and work serially when helpers are
unavailable or prohibited.

## Draft and review

Read [specification.md](references/specification.md) for the saved content and
identity contract. Inspect relevant code and repository instructions, preserving
source attribution, caller scope, and accepted decisions. For revisions or exports,
read [existing-specs.md](references/existing-specs.md) before changing the draft.

Compose [Grilling Session](../grilling-session/SKILL.md) in this session only for
material unresolved decisions. Preserve prior answers and use safe labeled
assumptions or delegated choices; a complete brief needs no fresh interview.
Ordinary answer waits are not terminal blockers.

Use [spec.md](templates/spec.md) and [task.md](templates/task.md) to draft the
complete artifact. Read [task-decomposition.md](references/task-decomposition.md)
when deriving or changing tasks. Keep the smallest useful task plan.

Review the complete draft against the specification contract before saving:
requested outcomes and accepted decisions are preserved, every acceptance
criterion has task coverage and credible verification, dependencies are real
and feasible, and each task is understandable with the main spec in a fresh
session. Acceptance checks describe feature behavior and prerequisite evidence;
worker, branch and PR topology choices belong to Delivery. Revisions preserve
identities and executor-owned progress.
Correct findings across the whole artifact; ask only about new material
choices. Stop with an exact blocker if essential evidence or a responsible
resolution remains unavailable. Resume from the saved content and current
evidence; do not maintain a planning workflow graph or execution journal.

## Save and report

Invocation authorizes the selected save, subject to caller constraints. New
specs default to GitHub; an explicit local/file request selects Markdown.
Existing specs retain their destination. Draft, preview, or no-write requests
produce a complete preview. An export requires explicit scope and preserves
original authority. Read [states.md](references/states.md) for operation and
result meanings, then only the selected output reference:
[GitHub](references/github-output.md) or [Markdown](references/markdown-output.md).

Before hosted source reads or saves, apply the shared
[G dependency preflight](../../references/codex-dependency-preflight.md).
Before every hosted write, apply
[hosted-content-safety.md](../../references/hosted-content-safety.md).
Local-source Markdown work and previews need no G access.

Verify the complete saved representation. Reconcile uncertain effects against
the same artifact before retrying, retaining identities from partial saves.
Never substitute another destination or preview after a failed save. After a
verified authoritative save, follow [delivery authorization](references/delivery-authorization.md)
to ask whether to enable pickup, reuse established authority and verify any
requested marker change. Publishing alone never enables automatic delivery.
Perform an explicitly requested downstream handoff only after verified save and
any requested marker change; reconcile its result before claiming completion.

Return the saved reference or complete preview, a concise task summary,
material assumptions, review and save results, observed delivery authorization,
and any exact remaining blocker or unanswered authorization question.
Keep operation receipts out of the saved spec. Planning completion proves the
artifact exists, not that its feature has been implemented.

## Skill Dependencies

Material clarification composes bundled `se:grilling-session`, including its
read-only Learn context inspection. Hosted reads and saves require the installed
`g@alemar11` issue workflow. Spec never installs or substitutes dependencies.
