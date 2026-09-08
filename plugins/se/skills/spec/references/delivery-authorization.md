# Delivery Authorization

Read after a verified authoritative save and when preserving or changing delivery
metadata. The shared [readiness states](../../../references/states.md) own values,
storage, transitions and canonical GitHub label colors; this reference owns the pickup
decision. The agent-ready marker authorizes delivery of the agreed spec scope
through validated ready PRs. It does not authorize landing PRs, deployment or
scope expansion, create a monitor, or prove that execution has started.
Existing caller restrictions and runtime authorization rules still apply.

## Readiness

Only the shared agent-ready state enables pickup of the authoritative main spec.
Dependencies, current contracts and existing work must still be reconciled.
Human-ready specs remain open for manual handling and are not eligible for pickup.
The metadata does not advance semantic `spec_revision`.

## Post-save decision

For a spec without an established readiness decision, after the whole
authoritative spec is saved and verified, ask: **Should this spec
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

Preserve either readiness state and the prior decision during ordinary revisions;
do not renew authorization merely because the artifact was saved again. Reconcile material
scope changes with active work and the authority already granted under
[existing-specs.md](existing-specs.md). An unchanged marker does not grant new
authority for work outside that agreement.

Exports remain inactive snapshots even when the source is authorized. Transfer
of authority must reconcile the old and new pickup locations before enabling the
new one; never create two active authoritative copies. Explicit revocation clears
readiness under the shared states contract, preserving other metadata. A human-ready spec requires explicit renewed authorization before
agent pickup; saving it again does not requeue it.

Report the saved source and observed pickup authorization separately. Setting the
marker does not invoke Deliver; only an explicitly requested downstream handoff
uses the entrypoint's handoff rules.
