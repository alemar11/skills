# Delivery States

Workflow position, lane scheduling, and the pending terminal outcome are
transient. Resume starts at Intake and reconstructs truth from semantic
contracts, Git/PR/review/CI evidence, execution progress, coordinator history,
and ownership. The claim registry never stores workflow or delivery status.

## Workflow nodes

| Node | Meaning |
| --- | --- |
| `intake` | Resolve authoritative specs, exact task selection and repositories, and the current coordinator. |
| `claim-repositories` | Acquire/reuse the frozen set and bind it to the current task. |
| `reconcile` | Reconcile lanes, evidence, per-PR budgets and blockers; continue independent work or prepare safe release. |
| `schedule` | Assign dependency-ready units with supported integration topology, or wait for active lanes without duplicating work. |
| `deliver-unit` | Implement and validate an isolated candidate; after clean local review, publish and converge its explicit hosted review and CI. |
| `review-candidate` | Independently review an immutable committed candidate in a detached read-only snapshot within its recorded attempt deadline. |
| `release-claims` | After preservation/quiescence, release the exact group while retaining the pending success or pause result. |
| `closeout` | Prepare the mandatory delivery report, measurements and generalized workflow audit without changing delivery evidence or ownership. |
| `complete` | All selected outcomes, progress writes, and review/CI gates are verified and this run released ownership. |
| `deferred` | A material user decision, explicit stop, or separately authorized action is needed; any acquired claim was safely released. |
| `blocked` | A capability, validation, review, budget, progress-save, or safety blocker remains; report whether claims were released, retained, or uncertain. |

A pre-acquisition stop has no claim to release. After acquisition, blocked or
deferred work follows `reconcile -> release-claims -> closeout` whenever safe.
Pre-acquisition stops and unsafe pauses also enter closeout with their exact
claim state. All terminal outcomes require a closeout report, including explicit
stops; evidence limits permit a concise best-effort retrospective. A release
failure returns blocked with uncertainty; it does not imply a retained claim
if successful release already has exact evidence. A later foreign acquisition
never becomes this coordinator's ownership.

## Selection and delivery evidence

`selected_task_ids` is caller-derived run scope, qualified by spec identity.
Absent explicit task selection, it contains the whole spec. `delivery_unit_id`
and task coverage are coordinator-owned execution identities, later bound to
an exact repository/PR. They are not semantic plan fields or claim columns.
An unselected dependency can block selected work but cannot enlarge selection.

A selected task may require new delivery or be `already-incorporated`; the latter
requires exact current outcome evidence in intended integration bases. A subset
can complete while the parent spec remains outstanding. `pending_outcome` is the
transient intended `complete`, `deferred`, or `blocked` report preserved across
release and closeout; it is never a persisted workflow position.
[closeout.md](closeout.md) owns report content and measurement coverage. Timing,
usage and retrospective notes are transient execution evidence, not spec fields,
claim columns, or a new saved workflow state. Closeout does not promote a paused
outcome or restart delivery to test its recommendations.

## Persisted progress status

[progress.md](progress.md) owns the original artifact's execution section.
These statuses are evidence summaries and do not schedule or authorize work.

| `delivery_status` | Meaning |
| --- | --- |
| `outstanding` | No current evidence establishes completed delivery for this task. |
| `in-progress` | Implementation or required validation/review is in progress. |
| `blocked` | A named dependency, decision, capability or review/budget gate prevents current completion. |
| `pr-ready` | All task contributions, combined outcome checks, both review gates and required CI qualify; all remaining PRs are ready. |
| `merged` | All task contributions are observed incorporated in intended bases and task outcomes verified there. |

PR publication alone permits neither `pr-ready` nor `merged`. A task becomes
in-progress from outstanding/blocked when responsible work resumes, and becomes
pr-ready only after current gates pass. Merge observations plus incorporated
outcome proof permit merged. Invalidated evidence returns it to in-progress or
blocked with a reason; preserve historical links and merged PR facts. The parent
uses the same meanings across all its tasks; partial delivery never upgrades it.
Provider open/closed and draft/ready/merged remain external facts, not aliases.
Per-PR repair counts recorded with progress preserve evidence on resume; they
never grant a new round or replace reconciliation with authoritative history.

## Candidate review

| `candidate_review_disposition` | Meaning |
| --- | --- |
| `clean` | Independent review finds no material issue blocking this exact unit candidate. |
| `findings` | Actionable corrections or an evidence-backed rebuttal remain. |
| `indeterminate` | Target, execution, profile, or evidence does not support a trustworthy verdict. |

| `execution_disposition` | Meaning |
| --- | --- |
| `completed` | Independent execution ended and returned an attributable result. |
| `not-executed` | Authoritative evidence proves work never began. |
| `interrupted` | Work began but no complete admissible result was returned. |
| `ambiguous` | Execution or effect cannot yet be established. |

| `checkout_cleanup_disposition` | Meaning |
| --- | --- |
| `not-created` | Authoritative evidence proves no checkout/registration was created. |
| `removed` | Exact temporary checkout and registration removal were verified. |
| `cleanup-failed` | Known checkout/registration remains; preserve and report its path. |
| `unknown` | Current target identity or cleanup result cannot be proved. |

Execution interruption may recover or be replaced only after confirmed stop,
understood preserved work, and safe cleanup. Ambiguous liveness never permits
another concurrent execution. The current candidate-review contract owns
receipt admissibility and retry decisions; missing result never means clean.

[candidate-review.md](candidate-review.md#attempt-deadline) owns local review
timing. Start and deadline are execution facts retained in coordinator history,
not claim columns or a separate timeout state. Expiry without an on-time completed
result gives `indeterminate`; confirmed stop gives `interrupted`, and unconfirmed
stop gives `ambiguous`. Cleanup uses its own disposition above. A timeout does
not spend a repair round or renew itself on resume.

[task-delivery.md](task-delivery.md#reconcile-before-republishing) owns topology
and rebase publication boundaries. Changed targets invalidate affected review
evidence before publication; topology observations are not persisted workflow
positions or new claim fields.

The [shared repair budget](../../../references/review-repair-budget.md) owns
round transitions and reservations. Review PR's [monitoring results](../../review-pr/references/states.md)
report provider completion only; this coordinator owns acceptance below.

## Hosted acceptance

| `hosted_review_acceptance` | Meaning |
| --- | --- |
| `provider-clean` | G returned terminal clean for the exact current HEAD and this workflow's explicit request lineage. |
| `adjudicated-clean` | G returned findings; every finding has an evidenced disposition, required replies are verified, and fresh independent local review accepted the unchanged-HEAD rebuttal with no remaining code change or user decision. |

Report adjudicated acceptance separately from the provider verdict. No-change
findings remain unresolved when G prohibits resolving them. Ready-triggered or
automatic review, missing comments, pending deadline, stale results, ambiguous
correlation, and provider failure cannot satisfy the explicit hosted gate.

## Repository ownership

| Persisted fact | Meaning |
| --- | --- |
| `provisional` | Rows have null `orchestrator_task_id`; the current coordinator has reserved the set but not completed binding. |
| `bound` | Rows name the current coordinator's stable task identity. |
| unclaimed | No row exists; absence is not stored state. |

All rows in a token group share home/binding. The CLI retains its schema names
for compatibility; no new coordinator task is implied. Command dispositions
remain `acquired`, `reuse-bound`, `reconcile-provisional`, `bound`, `already-bound`,
and `released`. They are operation results, not scheduling or delivery state.
`doctor` status `absent`/`ok` and inspect `database_state=absent` are read-only
observations. Exact whole-group release evidence proves this run released its
claim even if another owner acquired afterward; an ambiguous release is not
proved merely by observing current absence or foreign ownership.
