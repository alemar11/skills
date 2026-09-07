# Review Repair Budget

Each independent unit starts at round `0` before a PR exists. Its exact PR
inherits that count upon publication. Permit two review-driven repair or
rebuttal rounds per PR across local and hosted review combined. Batch all known
actionable findings for that PR into one round and reserve the next round before
assigning repair. A round covers the repair/rebuttal and subsequent reviews;
passing through another gate does not spend a second round. Further findings
requiring another change or rebuttal consume the next round. Infrastructure
retries, interrupted execution recovery, and repeated waits do not spend rounds.

The budget owner serializes reservations for the same PR; independent PRs have
independent counts. At round `2`, a clean result may publish or complete. If a
third round is needed, block that PR and its dependents while other independent
work continues. Never reset counts by changing HEAD, worker, reviewer, task,
unit ID, or PR. When regrouping, carry the highest spent/reserved count from the
contributing work and preserve its history; do not split to evade exhaustion.

On resume, reconstruct counts from the owner's history and attributable repair
and progress evidence. Receipts that fail the current profile/target contract
cannot satisfy a review gate, but their attributable spent counts remain spent. If history cannot
establish a safe count for a PR, pause that PR for reconciliation rather than
assuming zero or blocking unrelated work.

## Ownership and handoff

Read before assigning any review-driven repair or rebuttal, or reconstructing
its count. Delivery and Implement consume this contract. `repair_round` is a
persisted execution fact in attributable owner history and any Delivery progress;
it is not a skill-local counter or semantic spec field.

Delivery is the sole budget owner for its units. It records the reservation and
exact batch before assigning Implement, which preserves that identity/count
without reserving another round. Re-entry for the same batch carries its result
evidence. Review PR only monitors provider review; it neither consumes this
contract nor reserves, reconstructs, or resets a repair count. A missing budget
history blocks repairs, not request/monitoring work.

A handoff preserves the owner identity, exact unit/PR binding, spent/reserved
round, batch identity and scope, and evidence of its result. Do not persist a
new scheduling ledger or put review state in repository claims. A local review
and its hosted follow-up belong to the same batch; only newly required repair
or rebuttal advances the count. Explicitly selected findings do not authorize
fixing other feedback; report it to the owner before expanding the batch.
