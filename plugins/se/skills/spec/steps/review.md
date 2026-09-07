---
node_id: review
kind: validation
purpose: review-the-complete-spec-and-task-contract
entry_conditions:
  - spec-and-complete-task-plan-exist
inputs:
  - complete_spec_draft
  - planning_evidence
  - existing_spec_evidence
  - prior_review_findings
outputs:
  - review_result
  - review_findings
  - reviewed_spec
  - clarification_brief
transitions:
  - to: plan
    when: correctable-findings-and-material-progress
  - to: clarification
    when: new-material-decision
  - to: save
    when: complete-contract-is-clean
  - to: blocked
    when: repeated-unresolved-findings-or-missing-essential-evidence
stop_if:
  - clean-would-ignore-a-required-contract
side_effects:
  - read
terminal_states: []
---

# Review

Perform a distinct review of the whole spec, tasks, evidence, and requested
output. Use the shared
[`spec-reviewer`](../../../references/subagents.md#spec-reviewer) when useful
and available; otherwise use a separate serial review lens. Supply the complete
draft, evidence, and criteria below. A self-declared clean draft without this
assessment is not evidence.

Verify the canonical [specification contract](../references/specification.md):

- requested outcome, accepted decisions, scope, and non-goals are preserved;
- identities and allocation history are stable, with exact task membership;
- every criterion has a credible verification method and honest baseline;
- task completion checks, ownership, and collective F-AC coverage are complete;
- task order and real prerequisites are distinct, acyclic, and feasible;
- fan-in, migrations, and assembled validation have adequate integration intent;
- tasks introduce no extra scope and are usable with a fresh context;
- both spec-level and task-level outcomes can be verified;
- the selected output preserves all reviewed content and exact existing
  identities/progress, including export authority when applicable.

Correctable findings return through Plan and Decompose while revisions make
material progress. New product decisions return through Clarification. Repeated
unresolved findings block. A clean result passes the complete draft to Save;
review does not itself authorize any additional destination or hosted effect.
