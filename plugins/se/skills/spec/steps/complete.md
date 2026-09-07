---
node_id: complete
kind: terminal
purpose: report-the-complete-preview-or-verified-save
entry_conditions:
  - preview-complete-or-save-and-requested-handoff-verified
inputs:
  - final_spec
  - save_evidence
  - review_result
  - warnings
  - downstream_handoff_status
outputs:
  - feature_report
transitions: []
stop_if:
  - required-content-or-save-evidence-missing
side_effects:
  - none
terminal_states:
  - complete
---

# Complete

Return the spec identity/revision and saved reference, or the complete preview.
Summarize the ordered task plan, material decisions/assumptions, review result,
readback, destination warnings, and any requested handoff. For a Markdown save,
link the single complete file; for GitHub, link the parent and associated tasks.

Do not put operation receipts or planner-runtime metadata into the spec.
Planning completion proves the requested artifact was produced; it does not
claim code implementation, delivered PRs, merge, or issue closure. The planner
remains available for an explicit follow-up or revision.
