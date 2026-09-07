# Feature Specification Operations and Results

The `spec` namespace describes transient caller choices and operation results,
not a workflow graph. The saved identity and revision contract belongs to
[specification.md](specification.md). A request resolves to preview or save;
review findings return to drafting or clarification. A verified artifact completes
the save; [delivery authorization](delivery-authorization.md) owns the subsequent
pickup decision. An unresolved required effect remains blocked.

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
| `review_result` | `clean`, `revision-required`, `clarification-required`, `blocked` | Assessment of the complete spec and task contract. |
| `save_result` | `previewed`, `saved`, `exported`, `blocked` | Complete non-durable rendering, verified authoritative save, verified snapshot export, or incomplete operation. |
| `readback` | `verified`, `no-op`, `ambiguous` | Observed exact saved content; no-op requires the target already matches. Ambiguity blocks a required save. |
| `native_projection_result` | `verified`, `no-op`, `failed`, `unavailable`, `unknown` | GitHub relationship/dependency observation. A recorded native limitation is a warning when the complete semantic body representation is verified. |
| `downstream_handoff_status` | `not-requested`, `verified`, `no-op`, `failed`, `unavailable`, `ambiguous` | Only not-requested, verified, or no-op permits completion when a handoff is in scope. |

A saved spec may contain its semantic revision, explicit assumptions, acceptance
baselines, and a record of retired identities. It does not persist a current
workflow node, worker assignment, execution status, review receipt, or operation
journal. The delivery marker is permitted authorization metadata, with its values
owned by the linked authorization contract. Task progress and GitHub issue state
belong to their execution/provider owners; Spec preserves them during revision.

Keep save and authorization results separate. A saved spec with an unanswered
pickup question is awaiting the user's decision, not authorized. A declined
request leaves a new spec inactive. A requested marker operation must be verified
or already correct before reporting that effect complete; failure does not change
a verified `save_result=saved` into a claim that publication failed. No result
proves that a monitor or worker has started.
