---
node_id: save
kind: action
purpose: render-and-save-the-selected-spec-destination
entry_conditions:
  - review-clean-and-output-target-resolved
inputs:
  - reviewed_spec
  - output_intent
  - existing_spec_evidence
outputs:
  - final_spec
  - save_evidence
  - warnings
  - downstream_handoff_status
transitions:
  - to: complete
    when: preview-complete-or-save-and-requested-handoff-verified
  - to: blocked
    when: required-write-or-handoff-unreconciled
stop_if:
  - destination-would-be-silently-substituted
  - ambiguous-effect-would-be-replayed
side_effects:
  - transient
  - durable
  - hosted
terminal_states: []
---

# Save

Resolve the exact destination and operation before effects. Load only
[github-output.md](../references/github-output.md) or
[markdown-output.md](../references/markdown-output.md). These references own
projection, destination-specific effects, and readback. The `side_effects`
header lists possible branches: preview performs no durable or hosted write.

For preview, return the complete rendered spec and all task details with
proposed references. For save, freeze the candidate, perform the authorized
write, and verify the complete saved representation. Read
[existing-specs.md](../references/existing-specs.md) for revision or export.

Before any hosted operation run the shared
[G dependency preflight](../../../references/codex-dependency-preflight.md).
Before every hosted write apply
[hosted-content-safety.md](../../../references/hosted-content-safety.md).
Local-source Markdown work needs neither hosted transport nor native edges.

An ambiguous write is reconciled against the same intended artifact before a
retry. Retain verified identities on partial success and report exact remaining
work. Never substitute preview or another destination after a failed save.
Perform an explicitly requested downstream handoff only after verified save,
and reconcile its result before completion. Planning does not start Delivery
or close implementation issues implicitly.
