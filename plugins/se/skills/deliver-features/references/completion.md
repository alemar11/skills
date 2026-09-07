# Completion and Issue Linkage

Read before publication, after material review or topology changes, and before
final reconciliation. [task-delivery.md](task-delivery.md) owns unit coverage;
Spec's [specification contract](../../spec/references/specification.md)
owns the promised outcomes and task checks.

## Outcome evidence

For each task, verify all completion checks across its contributing units and
repositories, or exact evidence that the result is already incorporated. Then
verify every Feature criterion against the complete assembled result. Passing
all task checks does not substitute for feature-level integration verification.

Bind assembled evidence to the spec revision/content and the full repository,
base, and candidate HEAD vector. A change invalidates affected evidence; rerun
the relevant integration and outcome checks. Do not use a stale combination of
otherwise individually passing PRs.

Delivery completion means all selected outcomes are verified, every remaining
unit has a current ready PR with admissible candidate review, hosted acceptance,
and required CI, and the claim release is verified. It does not mean those PRs
are merged or issues closed. If the spec requires merged/deployed behavior to
prove an outcome and that evidence is unavailable, defer for that action rather
than claiming completion. An already-incorporated unit needs current outcome
evidence in the intended integration base, not a new empty PR.

## Exact closing references

Before every G Send handoff, derive the exact `closing_issue_refs` from verified
task/parent identities and scope evidence. This input is owned by Delivery;
G must not infer it from branch names, nearby issues, or the parent spec.

- A task issue qualifies only when the PR fully satisfies its completion
  checks, including prerequisite and multi-repository contributions already
  incorporated in their intended bases. A partial contribution gets an ordinary
  task reference and an explanation of what remains, not a closing keyword.
- The main spec issue qualifies only when every criterion is satisfied and
  this PR's merge, together with already-incorporated contributions, completes
  the entire outcome. Passing unit checks or merely listing every task is
  insufficient. Do not close the parent from an early task PR.
- If several unmerged PRs jointly deliver a task or spec and no one PR can
  establish complete closure safely, omit its closing keyword and report the
  exact remaining post-merge closure action. Do not fabricate a final PR or
  close issues directly to satisfy a template promise.
- A Markdown-only spec has no hosted closing identity. Use portable spec/task
  references and report an empty closing set unless independently verified
  associated issues were explicitly supplied.

Distinguish task readiness, PR delivery, and provider issue lifecycle. Verify
closing references against the actual PR base and planned landing sequence;
stacked PR linkage alone is not proof of automatic issue closure. Report
deferred closure honestly when topology or provider behavior leaves it pending.

Pass the verified set to G and read back every resulting closing reference and
ordinary contribution link. G may preserve existing closing lines on update:
inspect the entire resulting set, not just newly added lines. A stale or
over-broad line must be corrected through G before delivery can complete;
never silently retain it as unrelated body content. Missing exact identity or
uncertain scope blocks that write until reconciled.

Read [hosted-content safety](../../../references/hosted-content-safety.md)
before each hosted body write or correction. Do not include local absolute
spec paths, worker transcripts, or claim tokens in the PR.

## Final reconciliation

Reread the authoritative spec and task contracts. Verify all task and feature
outcomes, the exact combined validation vector, and each unit's actual PR HEAD,
ready state, base, body contribution/closing references, topology, candidate
receipt, hosted acceptance, and required CI. Report `provider-clean` separately
from `adjudicated-clean`. Keep these results in task history, not repository
claims or planning progress fields.

Only after this evidence is current may the orchestrator quiesce all actors
and follow the existing whole-group release protocol. The final report names
spec/task-to-PR mappings, integrated validation, closing references and remaining
closure actions, plus review, CI, and release evidence.
