---
node_id: decompose
kind: action
purpose: derive-an-actionable-ordered-task-plan
entry_conditions:
  - coherent-main-spec-draft-exists
inputs:
  - spec_draft
  - existing_spec_evidence
  - review_findings
outputs:
  - complete_spec_draft
  - task_plan
  - clarification_brief
transitions:
  - to: review
    when: complete-verifiable-task-plan-exists
  - to: clarification
    when: decomposition-exposes-material-decision
  - to: blocked
    when: feasible-task-contract-unavailable
stop_if:
  - tasks-require-unaccepted-scope-or-incompatible-prerequisites
side_effects:
  - read
  - transient
terminal_states: []
---

# Decompose

Read [task-decomposition.md](../references/task-decomposition.md). Apply the task
field contract in [specification.md](../references/specification.md) and use
[task.md](../templates/task.md) for each detailed task.

Produce a stable ordered index with task identity, title, repositories,
acceptance references, blockers and required evidence, and a detail/issue link.
Recommended order must respect hard prerequisites but must not manufacture
edges between independent tasks. Every task has its own completion checks and
validation; every F-AC has task coverage and feature-level verification.

Prefer vertical slices; justify bounded preparatory work, expand-contract
stages, and assembled-validation exceptions. Preserve independent fan-in and
state integration constraints without choosing branches or forcing PR stacks.
A fresh session must understand a task from that task and the main spec.

Resolve routine granularity from evidence. A newly exposed material outcome,
rollout, or integration decision returns to Clarification. Return the complete
spec and task plan to Review, not an isolated changed task fragment.
