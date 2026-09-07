# Task Selection and PR Grouping

Read during Intake, on material caller clarifications, and before assigning or
regrouping work. Spec owns the
[specification contract](../../spec/references/specification.md); Delivery owns
selection, execution units, integration, and PR grouping.

## Selected outcomes

Accept an authoritative saved GitHub spec bundle or Markdown spec. Read the
main spec and its task contracts; reject exported snapshots and unmigrated
legacy formats. Select all tasks by default. An explicit subset selects exact
task IDs within their qualified spec identities; an explicit batch may select
several specs. Read the surrounding spec to preserve constraints, not to expand
implementation scope.

At Intake, before substantial implementation, and when a caller clarification
changes scope, environment, ordering or authority, reconcile the requested
outcome with the saved task contracts. Identify what the proposed work delivers
and what remains excluded or blocked. Apply clear caller instructions without
reconfirmation. If a material conflict with a saved prerequisite or preservation
constraint remains unresolved, explain its effect on the deliverable and resolve
only that decision before affected work proceeds. Quiesce affected assignments
while reconciling; continue unaffected selected work. Do not silently narrow
selection or replace the requested outcome.

Carry explicit caller decisions alongside the saved contract in coordinator
history and handoffs, including on resume. They do not authorize incidental
rewrites of saved semantics: Spec owns those changes, and delivery progress is
not a contract amendment. Changed semantics or coverage invalidate affected
evidence under [candidate-review.md](candidate-review.md#recovery-and-invalidation).

Read prerequisites outside the selection and verify their declared evidence.
An unfinished prerequisite requires the caller's decision before adding it.
Keep its dependent blocked while independent selected work proceeds. Never
silently implement the prerequisite or claim that delivering a subset completes
the whole spec. Expansion into another repository requires safe release and
reacquisition of the newly frozen complete claim set before mutation.

Map selected tasks to exact repositories and local checkouts. Claim selected
implementation repositories plus any repository whose authoritative Markdown
progress file will be written. A GitHub tracker owner alone does not imply a
code repository claim. Do not claim every repository in an otherwise unselected
part of the spec. Branch/worktree and source-file identities must be resolved
before writing; display titles never establish them.

## Delivery units

Choose the smallest coherent set of reviewable PRs. A delivery unit owns one
spec, one repository, one branch, and one PR; it may supply one or several
selected tasks or their per-repository contributions. Group tightly coupled
schema/API work when useful; split independent outcomes or an unwieldy delta.
Explicit caller grouping wins when feasible. Multi-repository work needs a PR
in each repository that has a new delta. Already-incorporated work needs exact
current evidence, not an empty PR.

Assign a stable lower-kebab `delivery_unit_id` within the qualified spec and
bind its exact task coverage before assignment. Bind it to the exact repository
and PR number when published. Keep unit identity, coverage, branch/base, and
repair count in the coordinator's history and handoffs. Never reuse an identity
for unrelated work or assign overlapping contributions twice. Repartitioning
invalidates affected evidence and preserves the repair history under
[review-repair-budget.md](../../../references/review-repair-budget.md).

Account for every selected task across units or already-incorporated evidence.
A partial contribution does not complete a multi-repository task. Relevant
feature criteria and preservation constraints apply even to a subset; distinguish
criteria fully verified by this selection from those awaiting other tasks.

## Readiness and concurrency

Recommended order chooses among ready work; actual prerequisites determine
readiness for the proposed action. Identify whether each prerequisite gates code
preparation, publication, merge, data application, deployment or cleanup from
the contract and explicit caller decisions. Do not infer that boundary from a
task title or assume operational prerequisites apply only at deployment.
Resolve material ambiguity under the selected-outcome policy above.

Preparation may proceed only where that boundary permits it. Before preparation
becomes the remaining deliverable, verify that it still materially advances the
current request and resolve any material substitution with the caller. Local
references prove only their observed scope; preparation does not satisfy the
gated operational outcome.

Verify declared prerequisite outcomes, not merely a closed issue, list position,
native edge, or finished agent turn. A code prerequisite must be available in
the integration base or a validated candidate the dependent can consume.
Cross-repository candidates require a published PR, exact HEAD, and the needed
contract/integration evidence. Respect explicit merged/deployed prerequisites;
Delivery does not authorize those effects.

Several tasks may execute sequentially within one unit. Verify an internal
prerequisite before its dependent contribution without demanding another PR.
Regroup before assignment if grouping creates a cycle. Native GitHub edges
remain diagnostic projections of the spec's semantic dependencies.

Default to one active implementation lane per repository. Add concurrent lanes
only for independent work in separate worktrees. Exclude active contributions
from scheduling. Block only affected units when a prerequisite, repair budget,
or review is unavailable; continue independent selected work. When no useful
work remains, preserve progress and follow the safe-pause protocol.

## Integration strategy

For stacks or another managed PR topology, establish during grouping and before
dependent implementation that G's read-only contract and current state support
the arrangement. Standalone PRs do not require the stack workflow.
Check branching/sibling relationships as well as each immediate
parent. Correct Git ancestry alone does not prove that the stack manager can
represent the arrangement. Do not create branches or PRs just to probe support.

If support is unavailable or uncertain, choose a supported grouping within the
selected scope, or defer affected work before implementation. An explicit
grouping constraint that cannot be honored needs a caller decision. Do not
silently drop requested stack relationships or serialize siblings by inventing
a dependency. Reuse this evidence until topology or relevant capabilities change.

Before dependent mutation, verify how all prerequisites will be available:

- use the intended integration base when it already includes them;
- group coupled tasks into one unit and verify the sequence;
- use a stack when one actual immediate parent contains all same-repository
  prerequisite HEADs and separate review is useful;
- combine independent fan-in before publication, or use an explicit integration
  arrangement with non-overlapping deltas and a verified landing path.

Choose routine grouping autonomously. Defer affected work when existing PRs
cannot be combined safely without a merge or integration decision. Never add
fictional semantic edges, duplicate competing PR changes, or merge without
permission. Cross-repository dependencies never supply a Git base.

A repository-qualified caller base wins; otherwise use the provider's default
branch. Through G, refresh the intended upstream and resolve its full tip before
bootstrap. Recheck it before starting another root. For a stack, verify the
actual immediate parent and full HEAD; use a fresh root once prerequisite
changes are incorporated. Base, ancestry, or contract drift invalidates affected
reviews and verification. Apply the reconciliation boundary below before
publishing any resulting candidate.

## Reconcile before republishing

When an upstream or stack change affects existing lanes, first quiesce the
affected writers and identify every branch the operation could change. Work
outside selected ownership requires separate authority. Use G operations whose
effects keep changed candidates local: fetch and reconcile/rebase, validate the
resulting exact bases and HEADs, independently review each invalidated candidate,
then publish only those that pass. Reconcile dependents against the reviewed
parent HEADs; preserve existing repair counts and refresh hosted evidence after
publication. A pure rebase is not itself a review-driven repair round.

Do not use compound synchronization or submission that can rewrite and push
candidates before that review. In particular, G stack sync may rebase and push
several branches. Use it only if its verified effect scope cannot publish an
unreviewed candidate; otherwise use the separated operations above. If G cannot
express that separation, pause affected units rather than bypassing local review
or switching to raw provider operations. Unexpected effects require readback
and reconciliation before another mutation.
