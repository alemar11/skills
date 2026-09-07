# Existing Specs and Exports

Read when revising or exporting a saved spec. The content contract remains [specification.md](specification.md).

## Revision

Load the authoritative spec and every affected task before drafting. Preserve
their exact logical and saved identities, retired IDs, unrelated
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
authority. Render the complete current spec/task contract for either destination.

For an export to GitHub, record the snapshot source on the parent and link its
task issues back to that exported parent; apply the same safety and readback
gates as any hosted save. Export requires explicit authority for the destination
write. Editing an exported snapshot requires an explicit decision to transfer
authority or revise the original. If both destinations are requested without a
clear authority, resolve that choice before saving. Do not implement automatic
bidirectional synchronization.
