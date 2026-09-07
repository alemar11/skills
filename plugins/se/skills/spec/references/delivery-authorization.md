# Delivery Authorization

Read after a verified authoritative save and when preserving or changing delivery
metadata. This reference owns the pickup marker; output references own its storage
and provider operations. The marker authorizes delivery of the agreed spec scope
through validated ready PRs. It does not authorize landing PRs, deployment or
scope expansion, create a monitor, or prove that execution has started.
Existing caller restrictions and runtime authorization rules still apply.

## Marker

| Destination | Authorized | Inactive |
| --- | --- | --- |
| Main GitHub spec issue | `ready-for-agent` label | Label absent |
| Markdown spec frontmatter | `delivery: ready-for-agent` | `delivery:` empty, null or absent |

Only the exact marker enables pickup. It applies to the authoritative main spec,
not individual task issues or exported snapshots. Dependencies and the complete
current spec/task contract must still be checked before execution. The marker is
authorization metadata, not an execution state or part of semantic `spec_revision`.

## Post-save decision

After the whole authoritative spec is saved and verified, ask: **Should this spec
be available for automatic delivery to ready PRs?** Reuse an explicit answer or
existing authorization; a request to publish and deliver already grants it.
Publication alone does not. Preview/no-write operations and exports do not prompt
for or enable pickup.

If approved, apply the marker through the selected output reference and verify
it. Approval includes creating the exact missing repository label and applying
it to the main issue, without a second confirmation. Declining leaves a new spec
inactive; no answer is not approval. Do not repeat an answered question when
resuming the same save. A requested marker change remains incomplete until verified,
even when publication itself succeeded.

## Revision and handoff

Preserve the marker and prior decision during ordinary revisions; do not renew
authorization merely because the artifact was saved again. Reconcile material
scope changes with active work and the authority already granted under
[existing-specs.md](existing-specs.md). An unchanged marker does not grant new
authority for work outside that agreement.

Exports remain inactive snapshots even when the source is authorized. Transfer
of authority must reconcile the old and new pickup locations before enabling the
new one; never create two active authoritative copies. Explicit revocation removes
the GitHub marker or empties the Markdown field, preserving other metadata.

Report the saved source and observed pickup authorization separately. Setting the
marker does not invoke Deliver; only an explicitly requested downstream handoff
uses the entrypoint's handoff rules.
