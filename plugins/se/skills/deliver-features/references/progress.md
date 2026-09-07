# Delivery Progress

Read before any progress write and when resuming. Delivery owns execution
status and PR links in the original authoritative spec/task artifacts. Spec
continues to own requirements and task meaning. [states.md](states.md) owns the
progress status vocabulary; this file owns placement and write boundaries.

## Content and identity

Record a separate, clearly labeled `Delivery progress` section keyed by qualified
task ID. Include observed status, repository/PR links, exact contribution HEADs,
validation/review evidence, per-PR spent/reserved repair count, blockers, and
what remains. Keep it concise and update only when material evidence changes.
Maintain one record per task/PR identity; repeated writes update that record.
Never store tokens, agent transcripts, local paths in hosted content, or a queue
of future assignments. Progress summarizes execution evidence, not scheduling
instructions or an independent delivery authority.

Progress and provider-owned issue state are excluded from the immutable semantic
spec/task-contract identity and do not increment `spec_revision`. Requirements,
accepted decisions, task membership/ownership, criteria and dependencies remain
inside that identity. Do not ignore arbitrary body changes as progress: exclude
only the explicitly identified execution section and provider status fields.
A prior review still requires its exact Git base and HEAD; this exclusion does
not make code or Git changes invisible.

## Destination

For GitHub, update the linked task issues through G and maintain a concise parent
summary with task/PR links. Keep all semantic sections and foreign content.
Issue open/closed state does not substitute for delivery status; only observed
merges permit `merged`, and parent delivery requires all tasks, not the selected
subset. Apply [hosted-content safety](../../../references/hosted-content-safety.md)
immediately before every hosted write and verify the exact resulting content.

For Markdown, update the single authoritative source file in its original
planning checkout. Keep the progress section separate from spec/task definitions.
Preserve unrelated dirty content, reread before writing to avoid overwriting
concurrent edits, and read back the targeted result. These progress edits remain
local and uncommitted by default; report that explicitly. Do not create a
self-referential commit containing its own reviewed HEAD or push a progress-only
commit into a reviewed candidate. If the source is inside an active candidate
worktree, defer its progress write until that lane is quiescent and it can remain
a local, uncommitted metadata edit; never treat the resulting dirty file as a
clean implementation worktree on resume. Keep that checkout as the authoritative
planning location and create a fresh clean implementation lane from the preserved
candidate commits when needed; do not move or discard the progress diff.

An explicit request to publish Markdown progress is separate from code delivery:
choose and validate an ordinary documentation change without claiming the old
review covers its new commit. Do not silently create another authoritative copy
or an additional PR just to persist progress.

## Update and resume

Write observed progress after meaningful implementation, review, publication,
merge observation, or blocking changes, and before safe release. Never mark
`pr-ready` from publication alone: both review gates, required CI, selected task
checks and integration evidence must be current. Mark a multi-repository task
only after all its contributions qualify. A partial selection leaves other
tasks unchanged and reports their outstanding status.

On resume, reconcile stored progress with current Git, PR, review, CI, and
coordinator history. Preserve spent/reserved rounds from attributable evidence;
stale status never proves readiness, and missing budget evidence never implies
zero. If progress save fails, retain the exact result and work locations in the
coordinator handoff, report incomplete progress synchronization, and release
once quiescence and preservation are proved. That run pauses rather than claiming
fully successful delivery; retry only the missing save after reconciliation.
