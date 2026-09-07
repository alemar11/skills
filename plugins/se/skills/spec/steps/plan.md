---
node_id: plan
kind: action
purpose: draft-the-main-feature-specification
entry_conditions:
  - planning-evidence-and-decisions-sufficient
inputs:
  - planning_evidence
  - clarified_decisions
  - existing_spec_evidence
  - review_findings
outputs:
  - spec_draft
  - acceptance_criteria
  - decision_evidence
transitions:
  - to: decompose
    when: coherent-main-spec-draft-exists
  - to: blocked
    when: spec-contract-cannot-be-completed
stop_if:
  - unsupported-scope-or-decisions-required
side_effects:
  - transient
terminal_states: []
---

# Plan

Draft one coherent spec using [spec.md](../templates/spec.md) and the canonical
[specification contract](../references/specification.md). Multiple repositories
can contribute to its outcome. Use separate specs only for genuinely independent
outcomes; an explicit batch needs no artificial parent or set registry.

Record behavior, scope/non-goals, failure cases, compatibility, accepted
technical decisions and their authority, assumptions, risks, and observable
F-ACs. Separate binding decisions from implementation suggestions. Record each
criterion's verified baseline or an honest unknown, plus its verification
method; do not demand a false falsifier or fabricate a failing baseline.

Preserve exact identities and allocation history during revision. Correct
review findings coherently, then pass the whole draft to Decompose so task
coverage and dependencies are reconsidered with the changed spec.
