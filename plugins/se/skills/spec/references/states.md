# Feature Specification States

The workflow registry in `SKILL.md` owns nodes and transitions. The content
contract in [specification.md](specification.md) owns durable spec/task
identities. Workflow position and operation results are transient.

## Workflow nodes

| Node | Kind | Meaning |
| --- | --- | --- |
| `intake` | action | Resolve bounded inputs, repository scope, source authority, and destination/operation. |
| `analysis` | action | Establish behavior, decisions, constraints, and credible verification. |
| `clarification` | action | Resolve only material decisions through Grilling; ordinary answer waits are nonterminal. |
| `plan` | action | Draft the coherent main spec and its feature acceptance criteria. |
| `decompose` | action | Produce the complete actionable task plan with stable identities, order, and real prerequisites. |
| `review` | validation | Review the whole spec/task contract, correcting with progress or returning a material question. |
| `save` | action | Render a complete preview or write and verify the selected destination. |
| `complete` | terminal | The complete preview or requested save and explicitly requested downstream handoff are verified. |
| `blocked` | terminal | Essential evidence, a material decision, authority, or save reconciliation is unavailable. |

## Caller choices

| Field | Values | Meaning and default |
| --- | --- | --- |
| `destination` | `github`, `markdown` | GitHub for a new spec unless the caller requests a local file. Existing specs retain their authoritative destination; a change of destination requires explicit export or authority-transfer scope. |
| `operation` | `preview`, `save` | Save by default; an explicit draft, preview, or no-write request renders without durable or hosted writes. |

These are operation choices, not project configuration. The exact file path or
repository target is caller/repository data, not another enum. A preview may
read an explicitly supplied hosted source through G; a local-only source
constraint still forbids hosted reads. No destination or operation grants
additional source access or implementation authority.

## Derived evidence and result values

| Field | Values | Meaning |
| --- | --- | --- |
| `source_route` | `new-source`, `existing-source` | Derived from whether the request creates a spec or revises/exports an existing authoritative artifact. |
| `planning_readiness` | `ready`, `clarification-required`, `blocked` | Whether evidence supports drafting, a material choice remains, or essential evidence is unavailable. |
| `grilling_outcome` | `refined`, `user-stopped`, `blocked` | Composed interview result; a stopped handoff is usable only when remaining assumptions are safe. |
| `review_result` | `clean`, `revision-required`, `clarification-required`, `blocked` | Review disposition under the registered graph. |
| `save_result` | `previewed`, `saved`, `exported`, `blocked` | Complete non-durable rendering, verified authoritative save, verified snapshot export, or incomplete operation. |
| `readback` | `verified`, `no-op`, `ambiguous` | Observed exact saved content; no-op requires the target already matches. Ambiguity blocks a required save. |
| `native_projection_result` | `verified`, `no-op`, `failed`, `unavailable`, `unknown` | GitHub relationship/dependency observation. A recorded native limitation is a warning when the complete semantic body representation is verified. |
| `downstream_handoff_status` | `not-requested`, `verified`, `no-op`, `failed`, `unavailable`, `ambiguous` | Only not-requested, verified, or no-op permits completion when a handoff is in scope. |

A saved spec may contain its semantic revision, explicit assumptions, acceptance
baselines, and a record of retired identities. It does not persist a current
workflow node, worker assignment, delivery status, review receipt, or operation
journal. Task progress and GitHub issue state belong to their execution/provider
owners; Spec preserves them during revision.
