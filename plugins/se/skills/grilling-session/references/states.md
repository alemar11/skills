# Grilling Session State Reference

This reference is the canonical inventory of state used by `$se:grilling-session`.
All state is transient in the invoking conversation. Grilling Session has no persisted
checkpoint, run ledger, write preference, or repository-owned state.

## Workflow nodes

| Node | Kind | Plain description |
| --- | --- | --- |
| `context-read` | Action | Use Learn to inspect applicable repository context without writing. |
| `frame` | Decision | Infer the subject and identify the highest-value ambiguity. |
| `question` | Action | Ask exactly one focused question with a concrete recommended answer and incorporate the user's response. |
| `confirm` | Decision | Present the compact interpretation as one final confirmation question. |
| `complete` | Terminal | Return the user-confirmed refined handoff. |
| `reported` | Terminal | Return the best-supported handoff after the user ends questioning. |
| `blocked` | Terminal | Report why responsible questioning or synthesis cannot continue. |

## Result state

| Field | Allowed values | Meaning |
| --- | --- | --- |
| `grilling_outcome` | `refined`, `user-stopped`, `blocked` | Reports whether the user confirmed the brief, ended questioning early, or the workflow could not continue. |

`grilling_outcome=refined` maps to workflow node `complete`.
`grilling_outcome=user-stopped` maps to `reported` and preserves unconfirmed
items. `grilling_outcome=blocked` maps to `blocked` and names the smallest
recovery input.

The topic, questions, answers, working interpretation, refined handoff,
repository evidence, and durable-knowledge candidates are run data, not state
fields. A durable-knowledge candidate is not evidence that Learn captured it.
