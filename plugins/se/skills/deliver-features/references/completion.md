# Completion and Issue Linkage

Read before publication, closing-reference projection, progress completion, and
final reconciliation. [task-delivery.md](task-delivery.md) owns selection and
unit coverage; [progress.md](progress.md) owns saved execution status.

## Selected-outcome verification

Verify every selected task's completion checks across all contributing units
and repositories, or exact current evidence of incorporation in the intended
bases. Then verify the selected work's assembled behavior and relevant feature
criteria/preservation obligations. For whole-spec selection, verify every
criterion. For a subset, identify what it proves and explicitly retain criteria
that require unselected work as outstanding; never claim the entire feature is
complete. Passing individual task checks does not replace integration evidence.

Bind evidence to the semantic spec/task identity and the exact repository,
base, and candidate HEAD vector. Rerun only evidence invalidated by changes.
Never combine stale, individually passing PRs into a claimed integrated result.
A merged/deployed prerequisite or acceptance requirement still needs observed
evidence; pause for that separately authorized action when unavailable.

Delivery completes when all selected outcomes are verified, each remaining
unit has a ready PR with admissible independent local review, explicit-request
hosted acceptance and required CI, progress updates were verified, and claim
release was proved. Already-incorporated contributions need current outcome
proof rather than a new PR. A required draft-only output pauses this delivery
contract; publication alone is not delivery.

Ready PRs may remain unmerged. Report pending merge/rollout actions without
retaining claims just to await them. Merge, deploy, releases, and direct issue
closure require separate authorization. A safely paused run reports its verified
partial results and blocker, not successful delivery of the selected bundle.

## Exact closing references

Before each G Send, derive caller-owned `closing_issue_refs` from exact issue
identities and coverage. Never infer closure from a branch name or nearby issue.

- A task issue qualifies only when this PR's merge completes all its task checks,
  including prerequisite and cross-repository contributions already incorporated
  in their intended bases. Partial contributions get ordinary task references.
- A main spec issue qualifies only when this PR's merge plus already-incorporated
  work completes all tasks and feature criteria. A selected subset cannot close
  the parent while other work remains.
- When several unmerged PRs jointly supply an outcome and none can safely close
  it alone, omit the closing keyword and report the exact post-merge action.
  Do not invent a final PR or close issues directly.
- A Markdown-only spec has no GitHub closing identity. Use portable spec/task
  references and an empty closing set unless exact associated issues were
  explicitly supplied and verified.

Check actual PR bases and landing order; a stacked link does not guarantee
provider automatic closure. Pass the exact justified set to G, then read back
all closing lines and contribution references, including preserved existing
lines. Correct any over-broad or stale closing line through G before completing.
Uncertain identity or coverage blocks that write. Updating an execution status
to `pr-ready` never closes the corresponding issue.

Apply [hosted-content safety](../../../references/hosted-content-safety.md)
immediately before every hosted write or body correction. Do not publish local
absolute spec paths, agent transcripts, or claim tokens.

## Final reconciliation

Reread the authoritative semantic contracts, selected task outcomes, exact
combined validation vector, PR heads/bases/deltas, ready or incorporated state,
local receipts, explicit hosted-review lineage, required CI, and issue linkage.
Distinguish `provider-clean` from `adjudicated-clean`. Update progress and retain
the spec/task-to-PR mapping, spent repair counts, remaining tasks, and pending
merge/closure actions in the coordinator's handoff.

Then quiesce every actor and perform the final release protocol. Require the
exact successful release evidence and absence of the old binding; subsequent
foreign ownership is not this run retaining its claim. A failed progress write
or unresolved gate produces a safely released pause when possible. Unsafe
quiescence, preservation, or release leaves a blocked report with exact retained
ownership or uncertainty. Every outcome then runs [closeout.md](closeout.md)
for the final delivery report and workflow retrospective. Do not hold claims
for that analysis or treat missing metrics as a failed delivery gate.
