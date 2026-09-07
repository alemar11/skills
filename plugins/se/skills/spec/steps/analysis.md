---
node_id: analysis
kind: action
purpose: establish-outcome-decisions-and-verification
entry_conditions:
  - sources-and-repositories-resolved
inputs:
  - admitted_sources
  - repository_scope
  - existing_spec_evidence
  - clarified_decisions
outputs:
  - planning_evidence
  - material_unknowns
  - clarification_brief
transitions:
  - to: clarification
    when: material-decision-remains
  - to: plan
    when: evidence-and-decisions-sufficient
  - to: blocked
    when: essential-evidence-unavailable
stop_if:
  - evidence-cannot-support-a-coherent-outcome
side_effects:
  - read
terminal_states: []
---

# Analysis

Inspect current behavior, accepted constraints, existing verification boundaries,
and cross-repository contracts. Distinguish facts, accepted decisions, optional
suggestions, and assumptions under [specification.md](../references/specification.md).

Resolve only decisions material to outcome, scope, compatibility, safety,
ownership, migration, integration, or validation adequacy. The planner may make
explicitly delegated choices and safe assumptions. It preserves accepted
technical decisions without prescribing incidental implementation details.

When a material decision remains, pass the evidence, candidate interpretation,
and exact uncertainty to Clarification. Otherwise continue directly to Plan.
On re-entry, update only the analysis affected by the answer. Do not restart
launch, unrelated discovery, or an already completed interview.
