---
node_id: clarification
kind: action
purpose: resolve-material-decisions-through-grilling
entry_conditions:
  - material-decision-remains
inputs:
  - clarification_brief
  - planning_evidence
outputs:
  - clarified_decisions
  - accepted_assumptions
transitions:
  - to: analysis
    when: decision-resolved-or-safely-assumed
  - to: blocked
    when: required-decision-unavailable
stop_if:
  - material-decision-would-be-invented
side_effects:
  - read
  - transient
terminal_states: []
---

# Clarification

Compose [Grilling](../../grilling/SKILL.md) inside this planner with the admitted
evidence, accepted decisions, constraints, and material uncertainty. Ask one
focused question at a time; wait nonterminally for an answer. Do not introduce
another planner or Study controller.

Return a refined handoff, or the best-supported user-stopped handoff with
unconfirmed items labeled, to Analysis. Continue only if each material decision
is resolved or safely assumed; a declined indispensable decision blocks.
A complete brief does not need this node or a fresh confirmation interview.
