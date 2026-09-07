---
node_id: blocked
kind: terminal
purpose: report-the-exact-planning-or-save-blocker
entry_conditions:
  - no-responsible-transition-remains
inputs:
  - current_spec_evidence
  - unresolved_decisions
  - save_evidence
outputs:
  - blocker_report
transitions: []
stop_if:
  - another-safe-transition-remains
side_effects:
  - none
terminal_states:
  - blocked
---

# Blocked

Report the exact missing source, unresolved material decision, inconsistent
spec/task contract, unavailable destination capability, or ambiguous save or
requested handoff. Preserve verified file/issue identities and name the
smallest recovery input. A partial artifact is not the complete result.

Do not turn an ordinary answer wait, unknown nonessential baseline, optional
metadata/native-edge warning, or unavailable planner self-attestation into a
terminal blocker. Do not change the requested destination to manufacture success.
