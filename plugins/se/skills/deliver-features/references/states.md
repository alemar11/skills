# Delivery Features States

Delivery Features owns a small transient workflow graph. It has no persisted run
status, assignment status, checkpoint, effect journal, or delivery-state
machine. On resume, the orchestrator re-enters the graph through `intake`,
re-establishes ownership at `claim-repositories`, and derives the continuation
at `reconcile` from externally owned evidence.

## Workflow nodes

| Node | Kind | Meaning |
| --- | --- | --- |
| `intake` | action | Resolve the exact selected specs, their task contracts and prerequisites, repositories, and visible home. |
| `claim-repositories` | action | Atomically acquire or reuse repository ownership and bind one correlated visible orchestrator. |
| `reconcile` | validation | Reconstruct current truth from Feature, Git, candidate-review, pull-request, hosted-review/CI, and task owners before another effect. |
| `schedule` | decision | Compute the ready frontier and choose serial or bounded concurrent work. |
| `deliver-unit` | action | Run one verified worker lane through implementation, validation, and a stable local commit; after clean candidate review, resume the same lane for standalone or stacked pull-request publication, ready transition, and exact-HEAD hosted review and CI convergence. Several ready lanes may occupy this node concurrently. |
| `review-candidate` | validation | Run a fresh independent read-only adversarial review of one complete locally committed delivery-unit delta with the required fixed profile. Several independently scheduled candidates may occupy this node concurrently. |
| `release-claims` | action | After successful delivery or authorized handoff/abandonment, prove all other actors quiescent, make exact whole-group release the orchestrator's final external effect, and read back every repository as unclaimed. |
| `complete` | terminal | Exact whole-group release is verified and retained evidence proves either successful delivery of every selected Feature or completion of the requested handoff/abandonment. |
| `deferred` | terminal | A material semantic decision or additional user authority is required. |
| `blocked` | terminal | No safe transition remains because required capability, identity, ownership, evidence, or reconciliation is unavailable. |

Workflow position is transient. None of these node IDs is stored in the
repository registry, task metadata, branch names, or pull requests.

## Transient selected-spec disposition

| Disposition | Meaning |
| --- | --- |
| `delivery-required` | At least one task contribution or feature-level outcome still needs implementation or current delivery evidence across the selected spec's units. |
| `already-incorporated` | Current exact evidence proves every task completion check and Feature criterion in the intended repository integration bases. |

An unmet prerequisite never removes a task or spec from completion. Account
for all task contributions, units, and assembled feature-level verification.
If an outcome has no new delta but lacks incorporation evidence, defer rather
than creating an empty PR or excluding it. A unit may be already incorporated
while the rest of its spec still requires delivery.

Unit IDs and task contribution mappings are transient task-history evidence
owned by [task-delivery.md](task-delivery.md). They are not persisted planning
fields or registry state. Issue open/closed status is provider-owned and never
substitutes for completion checks or full feature criteria.

## Transient candidate-review dispositions

| `candidate_review_disposition` | Meaning |
| --- | --- |
| `clean` | The independent reviewer found no material issue blocking publication of the exact reviewed spec/task contract, unit contribution, base, and candidate HEAD. |
| `findings` | One or more material findings require repair or an evidence-backed rebuttal accepted by a fresh review. |
| `indeterminate` | Exact target, reviewer execution, or evidence was insufficient for a trustworthy verdict. |

These values are transient reviewer results, not workflow nodes or persisted
claim state. Their meanings are canonical here; the operational review contract
only produces and consumes them. Any content, ancestry, base, or full-HEAD
change invalidates them.

## Transient candidate-review execution dispositions

| `candidate_review_execution_disposition` | Meaning |
| --- | --- |
| `completed` | The independently identified reviewer execution ended and returned an admissible result for its exact snapshot. |
| `not-executed` | Authoritative evidence proves the reviewer never began; one retry of the identical snapshot is permitted after cleanup. |
| `interrupted` | The reviewer began but did not return an admissible result; block unless that exact attempt can be recovered. |
| `ambiguous` | Available evidence cannot establish whether or how the reviewer executed; never launch a replacement blindly. |

## Transient candidate-review checkout dispositions

| `candidate_review_checkout_disposition` | Meaning |
| --- | --- |
| `not-created` | Authoritative evidence proves no review checkout or worktree registration was created. |
| `removed` | The exact temporary checkout and its worktree registration were removed and absence was verified. |
| `cleanup-failed` | Cleanup was attempted but the exact checkout or registration remains; report its path and block. |
| `unknown` | Cleanup or current path identity cannot be established safely; preserve the target and block. |

Candidate-review receipts use `review_revision_ordinal` `0`, `1`, or `2`.
These count review-driven repair/rebuttal revisions across all units of one
spec, not task order or spec revision. A new unit uses the current ordinal;
only a repair/rebuttal spends one. A proved non-execution retry keeps its
ordinal. Unaffected earlier receipts remain admissible when their target
identities remain current, even after another unit advances the spec budget.

## Transient hosted-review acceptance

| `hosted_review_acceptance` | Meaning |
| --- | --- |
| `provider-clean` | G returned terminal clean hosted Codex evidence for the exact current HEAD and lineage. |
| `adjudicated-clean` | G returned terminal findings, but every finding has G-owned disposition evidence, required evidence replies are verified, no code change or user decision remains, and a fresh clean local review accepted the rebuttal on the unchanged HEAD. No-change dispositions remain unresolved when G prohibits resolution. |

`adjudicated-clean` is never reported as a clean provider verdict. G-owned
review states and feedback dispositions retain their own names and meanings;
this field is only Delivery Features' completion projection.

## Persisted repository-claim facts

| State | Representation | Meaning |
| --- | --- | --- |
| `provisional` | A claim row whose `orchestrator_task_id` is null. | The immutable repository set is reserved, but task creation has not yet been reconciled and bound. |
| `bound` | A claim row whose `orchestrator_task_id` is present. | One observed orchestrator task owns the complete repository set. |
| unclaimed | No row for the repository. | No Delivery Features orchestrator owns the repository on this host. This is absence, not a stored state. |

Every row in one `claim_token` group has the same `home_project_key` and the
same provisional or bound task value.

## Transient command dispositions

| Disposition | Meaning |
| --- | --- |
| `acquired` | The complete unclaimed repository set was inserted provisionally. |
| `reuse-bound` | The requested repositories already belong to the same bound claim; reuse that orchestrator. |
| `reconcile-provisional` | The requested repositories already belong to the same provisional claim; determine whether task creation happened before retrying. |
| `bound` | The complete provisional claim was attached to the independently observed invoking or separately created orchestrator task. |
| `already-bound` | An idempotent bind observed that the same task already owns the complete claim. |
| `released` | The complete claim group was removed after an authorized bound release or fenced provisional abandonment. |

These dispositions are command results, not persisted states. Errors such as a
foreign claim, mixed ownership, repository-set expansion, binding conflict, or
corrupt registry also are not states.

## Transient diagnostic observations

| Observation | Meaning |
| --- | --- |
| `status=absent` | `doctor` observed no registry file and did not create one. |
| `status=ok` | `doctor` verified the existing registry and its claim count. |
| `database_state=absent` | `inspect` observed no registry file and returned no claims without creating one. |

These observations report the database at command time. They are not persisted
workflow state and do not authorize creation, binding, release, or repair.

## External observations

Task activity, worktree cleanliness, spec/task prerequisites, branches, commits,
candidate-review receipts, pull requests, hosted-review results, CI, and merge
state are observed from their current owners. Candidate review is valid only
for its immutable spec/task contract, unit identity and coverage, repository,
base, candidate, tree, delta, profile,
execution, and cleanup evidence. Final delivery also requires current actual PR
HEAD, ready state, base branch, body identity, and standalone or stack topology.
A draft PR, generic `not-requested`, absence of comments or threads, pending
deadline, stale evidence, provider failure, and ambiguous correlation are not
hosted acceptance. Review receipts and observations must never be projected
into the repository registry.
