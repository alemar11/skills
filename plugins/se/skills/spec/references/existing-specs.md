# Existing Specs and Exports

Read for a revision, an export, or an older saved Feature artifact. The current
content contract remains [specification.md](specification.md).

## Revision

Load the authoritative spec and every affected task before drafting. Preserve
their exact logical and saved identities, acceptance high-water mark, unrelated
content, and executor-owned status, checkboxes, comments, and progress. Record
the smallest semantic change; increment `spec_revision` once for the accepted
bundle revision. A save retry or unchanged export does not increment it.

Reordering or renaming preserves task identity. New tasks receive unused IDs.
If a task's outcome is replaced rather than refined, retire its old identity
explicitly and allocate another. Keep a compact record of retired task and
criterion IDs so later runs cannot reuse them; use the
[revision note](../templates/maintenance-changelog.md) when useful. Do not silently remove already
implemented obligations or reshape active work; surface material conflicts
with observed execution for user direction.

Update the parent index and affected task details together, preserving
unaffected fields. Verify that no task, criterion, or dependency is orphaned.
Retiring a hosted task removes it from the active index with an explicit
historical reference; closing or deleting that issue requires separate scope.
Retirement invalidates any prior delivery evidence relying on it.

## Authority and exports

An existing artifact keeps its authoritative destination by default. An
explicit export preserves `spec_id`, `spec_revision`, task IDs, order,
dependencies, decisions, and criteria. The exported artifact identifies its
authoritative source and revision and is a snapshot, not another writable
authority. Render the complete content for either destination.

For an export to GitHub, record the snapshot source on the parent and link its
task issues back to that exported parent; apply the same safety and readback
gates as any hosted save. Export requires explicit authority for the destination
write. Editing an exported snapshot requires an explicit decision to transfer
authority or revise the original. If both destinations are requested without a
clear authority, resolve that choice before saving. Do not implement automatic
bidirectional synchronization.

## Older Feature artifacts

Older saved artifacts may use a Feature Plan Set registry and Macro Task fields.
Those are migration inputs, not aliases accepted by the current contract.
Do not silently reinterpret them during delivery. Spec may migrate them
under an explicit revision/migration request after reading every affected body.

Preserve each old parent issue as one spec and each corresponding child issue
as one task. Carry stable Feature and Macro identity values into `spec_id` and
`task_id` when canonical and unambiguous; preserve F-AC identities and allocation
history. Record an explicit old-to-new mapping for any noncanonical identity
that must change. Do not merge sibling parents or move tracker ownership merely
because the new format supports multi-repository specs.

Replace planning-only task summaries with evidence-backed actionable outcomes,
scope, completion checks, and validation. Map real old dependencies to explicit
prerequisite outcomes; an old stack-intent edge does not automatically prescribe
Git topology. Cross-spec prerequisites retain exact references and required
evidence. Missing task meaning or a changed accepted obligation requires
clarification, not fabricated content. Preserve execution progress and foreign
relations, then save and verify the same artifacts in the current shape.
