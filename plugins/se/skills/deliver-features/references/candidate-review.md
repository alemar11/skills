# Independent Candidate Review

Read before local review, review-driven repair, or budget reconstruction.
[states.md](states.md) owns dispositions; the shared
[`code-reviewer`](../../../references/subagents.md#code-reviewer) owns the default
model and role boundaries. Compose
[`se:adversarial-review`](../../adversarial-review/SKILL.md) for its skeptical
review and evidence-backed finding contract. Delivery owns the target,
checkout, acceptance, and per-PR repair budget.

## Immutable target and independent execution

Enter after the developer validates and locally commits a stable candidate,
becomes quiescent, and proves the implementation worktree clean. Bind review
to the qualified spec's semantic contract identity, selected task contributions,
unit identity, exact repository, intended base branch and full SHA, candidate
branch/full HEAD/tree, complete effective delta, repository instructions, and
validation evidence. Execution-progress-only changes do not alter the semantic
spec identity; [progress.md](progress.md) owns that separation.

The coordinator creates a unique detached temporary review checkout at the
candidate HEAD outside the developer's worktree and verifies its clean tree and
exact base. Launch a fresh read-only `code-reviewer` subagent with the selected
role profile and a self-contained brief. The reviewer has no implementation
conversation, candidate-write access, Git mutation authority, or hosted-write
authority. An explicit caller profile override wins and is recorded. A
same-context developer self-review never satisfies this gate.

After every attempt, independently confirm the reviewer stopped, inspect the
snapshot's identities and cleanliness, remove only its exact temporary checkout,
and verify its path and worktree registration gone. A dirty review snapshot
invalidates the result; an uncertain path or active reviewer prevents cleanup
and safe claim release. Do not delete ambiguous or user-owned content.

## Review evidence

Return `candidate-review-receipt-v3` in coordinator history. Its fields are:

| Field | Required evidence |
| --- | --- |
| `receipt_version` | `candidate-review-receipt-v3`. |
| `spec_contract_identity` | Qualified spec/revision plus immutable semantic content identity, excluding execution progress. |
| `delivery_unit_id` | Stable unit ID with its repository/PR binding when published. |
| `task_contributions` | Exact selected outcomes and per-repository coverage. |
| `repository_key` | Canonical claimed repository identity. |
| `base_branch`, `base_sha` | Intended integration or immediate-parent branch and full reviewed base SHA. |
| `candidate_branch`, `candidate_head`, `candidate_tree_identity` | Exact committed candidate. |
| `reviewer_execution_identity` | Observed independent subagent identity, or authoritative `not-created`. |
| `requested_profile` | Role ID, requested model and reasoning, and any explicit override. |
| `observed_profile` | Independently available evidence, or `unavailable`; never self-attestation. |
| `repair_round` | This unit/PR's current spent or reserved round: `0`, `1`, or `2`. |
| `execution_attempt` | Attempt number for this immutable target, independent of repair count. |
| `execution_disposition` | Canonical execution result from states.md. |
| `candidate_review_disposition`, `findings` | Canonical verdict and evidence-backed findings; absent verdict means `indeterminate`. |
| `pre_review_snapshot`, `post_review_snapshot` | Exact base, HEAD, tree, effective delta, cleanliness, and execution-stop evidence. |
| `checkout_cleanup_disposition` | Verified `removed`/`not-created`, or failure/uncertainty with the exact retained path. |

Admit `clean` only for an independent completed execution, matching identities,
clean snapshots, and verified cleanup. Missing profile telemetry alone does not
invalidate an explicitly requested profile; observed mismatch does. Creation
receipts and reviewer self-reports never prove effective settings. An interrupted
or ambiguous attempt is `indeterminate`, even if it returned partial findings.
Keep tokens out of every receipt. Present absence alone never proves non-creation.

## Two repair rounds per PR

Each independent unit starts at round `0` before a PR exists. Its exact PR
inherits that count upon publication. Permit two review-driven repair or
rebuttal rounds per PR across local and hosted review combined. Batch all known
actionable findings for that PR into one round and reserve the next round before
assigning repair. A round covers the repair/rebuttal and subsequent reviews;
passing through another gate does not spend a second round. Further findings
requiring another change or rebuttal consume the next round. Infrastructure
retries, interrupted execution recovery, and repeated waits do not spend rounds.

The coordinator serializes reservations for the same PR; independent PRs have
independent counts. At round `2`, a clean result may publish or complete. If a
third round is needed, block that PR and its dependents while other independent
work continues. Never reset counts by changing HEAD, worker, reviewer, task,
unit ID, or PR. When regrouping, carry the highest spent/reserved count from the
contributing work and preserve its history; do not split to evade exhaustion.

On resume, reconstruct counts from coordinator history and attributable repair
and progress evidence. Old receipts cannot satisfy the new profile/target
contract, but their attributable spent counts remain spent. If history cannot
establish a safe count for a PR, pause that PR for reconciliation rather than
assuming zero or blocking unrelated work.

## Recovery and invalidation

Recover a prior exact result when authoritative evidence permits. Otherwise a
replacement review may run once the old execution is confirmed stopped, the
candidate is understood, and prior review-checkout cleanup is verified. Preserve
its repair count and record the new execution attempt. Retry only when a
concrete recovered capability or changed condition supports progress; repeated
unchanged infrastructure failure pauses the affected PR. Never run competing
review attempts after an ambiguous launch.

A clean result permits publication while all target identities remain current.
Any semantic contract, coverage, candidate, base-tip, ancestry, HEAD, tree, or
delta change invalidates affected evidence. Verify it immediately before push,
ready transition, and final completion. A hosted repair must pass local review
again before push. Another PR's repair count does not invalidate this receipt.
