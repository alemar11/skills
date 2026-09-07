# Idea State Reference

This reference is the human-readable inventory of state used by `$se:idea`.
Keep workflow position separate from run mode, graph effect classification,
candidate results, transient handoff fields, and hosted issue state.

Idea has no persisted workflow checkpoint or run-state ledger. Its capture
bundle, current workflow node, and reports are transient. Only an explicitly
published hosted issue is durable, and that issue does not persist the
workflow's current node.

## Workflow nodes

| Node | Kind | Plain description |
| --- | --- | --- |
| `capture` | Action | Collect proposal evidence after an explicit capture or preview request. |
| `normalize` | Action | Convert the evidence into concrete, deduplicated candidate Ideas. |
| `clarify-select` | Decision | Honor the explicitly selected set, including all candidates; ask only for unresolved selection or one material intake gap. |
| `freeze` | Action | Finalize the accepted local candidates, owners, bodies, and intended metadata. |
| `terminal-operation` | Decision | Resolve exactly one terminal branch after the local bundle is frozen. |
| `preview` | Action | Render proposed Ideas locally without loading publication dependencies or hosted state. |
| `publish` | Action | Enter the hosted publication branch for the exact authorized scope. |
| `preflight` | Validation | Verify that the required publication workflow is available before hosted access. |
| `hosted-checks` | Validation | Inspect the target, duplicates, collisions, issue state, and hosted metadata. |
| `mutate` | Action | Perform one normalized hosted issue operation. |
| `reconcile-verify` | Validation | Read hosted state back and distinguish verified success, absence, or failure before any retry. |
| `reported` | Terminal | Return an explicit preview or no-candidate report. |
| `deferred` | Terminal | Stop coherently because candidate selection or clarification is required. |
| `complete` | Terminal | Finish after every requested hosted operation has been verified. |
| `blocked` | Terminal | Stop because required evidence, scope, authority, dependency, or reconciliation is unavailable. |

## Field-qualified and external states

| Owner | Values | Class and lifetime | Meaning |
| --- | --- | --- | --- |
| `run_mode` | `publish`, `preview` | Selectable run field; transient | `publish` is the default and may perform verified hosted writes; `preview` is explicit and local-only. |
| Graph `side effects` | `none`, `transient`, `dependency-read`, `hosted-read`, `hosted-write` | Graph metadata; static | Describes what a workflow node may affect. These values are not lifecycle states. |
| Candidate report outcome | `created`, `reused`, `proposed`, `skipped`, `failed` | Result value; transient report | Describes the disposition of each selected candidate independently of the workflow terminal node. |
| Hosted reconciliation outcome | `created`, `reused`, `missing`, `failed` | Result fact; transient report | Records what readback verified after a hosted operation and determines the safe resume point. It is not hosted issue state. |
| `idea_ref_state` | `proposed-non-durable`, `verified-hosted` | Typed handoff field; transient | Distinguishes a preview-only proposed ref from a hosted identity verified by readback. It does not duplicate the hosted issue's own state. |
| `source_kind` | `idea-source` | Typed handoff discriminator; transient | Identifies the artifact as an Idea Source Handoff. |
| Spec `source_route` | `new-source` | Receiving-workflow field; transient | Tells Spec to treat the handoff as tentative source evidence and derive its own plan fields. |
| Hosted issue `state` | `open` | External persisted domain state | A durable Idea is an open hosted issue. |
| Hosted native `Issue Type` | unset | External persisted domain state | Idea deliberately leaves the provider-native Issue Type unset. |
| Hosted collision observation | exact equivalent, near title match, materially different collision | Derived external fact; transient | Guides reuse or user clarification. These descriptions are not a persisted enum or workflow state. |
| Open Questions sentinel | `None recorded.` | Hosted body content; durable when published | Means no open question was recorded; it is content, not workflow state. |
| `allow_implicit_invocation` | `false` | Persisted skill metadata | Requires an explicit Idea capture or preview request. |

Candidate selection, rendered bodies, publication order, preflight evidence,
and qualified references are run data rather than enum states. The word
“checkpoints” in the publication procedure describes ordered verification
steps; it does not define a checkpoint field.
