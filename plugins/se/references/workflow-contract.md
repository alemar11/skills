# SE Workflow Contract

This reference is the canonical owner of the hosted shape for the SE Idea
workflow. The G-owned GitHub issue workflow owns provider transport,
pagination, mutation safety, and read-after-write verification. The Idea skill
owns when this contract is read or applied; it must not edit the contract during
a run.

The shared workflow graph vocabulary is owned by workflow-graph.md. This
reference remains limited to the Idea hosted shape and must not duplicate
graph-node or terminal-state definitions.

## Hosted shape

A durable SE Idea is:

- an open issue titled `Idea: <Name>`;
- free of native Issue Type metadata;
- rendered with the canonical seven-section Idea body.

The `Idea:` title prefix and the canonical seven-section body are the complete
semantic hosted shape. Open questions are body content, not a request to apply
a separate state.

## Ownership

| Workflow | Applies | Reads | Does not own |
| --- | --- | --- | --- |
| `idea` | Idea hosted shape | Idea title, body, state, and native Issue Type | Feature specs, implementation units, planning transitions |

A runtime flow must stop when the hosted shape is missing, contradictory, or
cannot be reconciled with the target repository.
