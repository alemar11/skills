# Review PR States

Default request-and-wait and explicit inspect-only scope are caller instructions,
not persisted configuration. The skill has no saved workflow position: resume
reconstructs the exact PR/HEAD, G request receipt, original deadline, and observed
provider evidence. It owns no agents, implementation, or repair state.

| `review_pr_result` | Meaning |
| --- | --- |
| `completed` | G established a terminal clean or findings verdict for the selected explicit request and expected current HEAD. |
| `inspected` | Read-only inspection returned available review evidence and gaps without requesting or waiting. |
| `pending` | The selected review remains unanswered at the original deadline or caller stop; retain the receipt and deadline. |
| `deferred` | A draft PR or unresolved target selection requires caller action before requesting/waiting. |
| `blocked` | Required capability, request correlation, target stability, or provider evidence prevents responsible monitoring. |

A completed review is not an accepted implementation. Findings are returned to
the caller, not converted to repair-required or an adjudicated verdict here.
Provider verdicts, finding identities, request receipts and deadlines remain
G-owned evidence; retain them unchanged in the caller handoff.

Inspect-only ends with inspected, even when no review exists. Default invocation
requests a missing review, resumes a matching pending request, or immediately
returns a verified terminal result. Pending resumes against the same deadline;
a later terminal readback can yield completed without extending the wait.
Deferred/blocked resumes only after reconciling its cause. HEAD drift blocks the
bound run; a caller may invoke a new run with the new target. Historical evidence
remains attributable to its original HEAD and never becomes current by re-entry.
