# Delivery Features Orchestration

Load this reference for graph scheduling, multi-repository topology, resume,
worker concurrency, pull-request stacks, claim conflicts, or workflow
transitions. `SKILL.md` owns the workflow node registry; this reference owns
the condition for every declared edge.

## Workflow transition conditions

| from | to | when |
| --- | --- | --- |
| intake | claim-repositories | Every exact selected saved spec, its authoritative task contracts and dependencies, repository identities, and visible home are resolved without a material user choice. |
| intake | deferred | A material semantic choice remains that the caller can resolve. |
| intake | blocked | The selection is invalid, cyclic, unreadable, or cannot be mapped to authoritative repositories. |
| claim-repositories | claim-repositories | One orchestrator-creation attempt is authoritatively proved not applied; retry task creation once under the same provisional claim. |
| claim-repositories | reconcile | The complete claim is independently acquired or reused, correlated to one stable orchestrator identity, bound, and read back. |
| claim-repositories | blocked | Claim overlap, provisional task effects, binding, or orchestrator identity cannot be reconciled safely. |
| reconcile | schedule | At least one selected Feature remains unfinished and current authoritative evidence supports another scheduling decision. |
| reconcile | release-claims | Final delivery evidence is admissible, or handoff/abandonment is explicitly authorized; every worker and reviewer is stopped, no mutation remains outstanding, and the bound orchestrator is ready to make exact whole-group release its final external effect. |
| reconcile | deferred | Safe continuation requires a material semantic decision or additional user authority. |
| reconcile | blocked | Required capability, identity, ownership, receipt, cleanup, review, or effect evidence remains unavailable or ambiguous, or another review-driven repair or rebuttal is required after ordinal `2`. |
| schedule | deliver-unit | One or more dependency-ready delivery units are not already assigned to an independently observed active lane and have verified bases, topology, trustworthy worker targets, and reconciled candidate-review evidence indicating implementation, repair, review preparation, or publication work. |
| schedule | reconcile | No new assignment should start because only active lanes remain or until a bounded authoritative refresh observes a material Git, pull-request, review, CI, task, or Feature change. |
| schedule | deferred | The only responsible continuation requires a material user decision or authority. |
| schedule | blocked | Unfinished work has no responsible ready, refresh, or user-decision path. |
| deliver-unit | review-candidate | A worker returns a stable locally committed unit candidate at an exact base and full HEAD with all required validation passing and no clean current candidate review. |
| deliver-unit | reconcile | A worker returns exact published completion, partial progress that is not ready for candidate review, correction, or blocker evidence; concurrent returns reconcile independently. |
| review-candidate | reconcile | Candidate Review returns one admissible receipt or exact execution, cleanup, identity, or budget failure evidence. `reconcile` alone chooses the next edge. |
| release-claims | complete | Exact whole-group release and subsequent unclaimed readback are verified while admissible final delivery or authorized handoff/abandonment evidence is retained. |
| release-claims | blocked | Release cannot be proved exact and safe. |

`schedule -> reconcile` is a change-driven wait loop, not a busy poll. Terminal
nodes have no outgoing transitions. A resumed invocation starts at `intake` and
reconstructs its continuation through `claim-repositories -> reconcile`; task
history or a claim row never acts as a persisted current-node pointer.

## Orchestrator placement

The orchestrator is the visible owner of one caller-selected spec or
explicit batch. Use the single involved saved project as its home. For a graph
spanning several projects, prefer the current associated project when it visibly groups
the whole run; otherwise use the caller-selected coordination project. Ask
only when several plausible homes remain. The workers still run in their
repository projects and isolated worktrees. A projectless orchestrator is only
a warned fallback; use `projectless` as its visible-home claim key. It does not
change repository ownership.

Reuse the invoking visible task as the orchestrator when its stable identity
and intended home can be independently observed and correlated to this exact
Feature selection. Otherwise create one separate visible orchestrator. In both
cases, complete the acquisition and binding protocol in
[repository-claims.md](repository-claims.md) before any worker or G-owned
effect. A title, current directory, or self-report never establishes the
required identity or correlation.

Freeze all repository identities before acquisition. Version 1 does not expand
a live claim because independent multi-repository expansion can deadlock and
can make the intended visible home ambiguous.

## Task metadata and worker targets

Set display titles when tasks are created:

- orchestrator: `🤖 Orchestrator · <spec or batch name>`;
- worker: `🛠 <repository> · <current delivery unit>`.

Best-effort rename a reused worker for its current unit. Titles and project
grouping are diagnostics, never identity, correctness evidence, or a reason to
retry or replace a task.

Use the configured model and reasoning defaults for the orchestrator and
implementation workers unless the caller explicitly requests another profile.
The independent candidate reviewer instead uses its fixed profile from
[candidate-review.md](candidate-review.md). If a caller makes any other profile
acceptance-critical, verify it or report that it cannot be established;
otherwise profile metadata does not gate delivery.

Resolve one integration branch per repository before scheduling. A
repository-qualified caller override wins; otherwise use the authoritative
provider default. Reject a missing, ambiguous, inaccessible, or
wrong-repository selection without fallback. Through the applicable G-owned
branch transport, refresh that upstream branch and read its full remote tip.
Freeze the branch and SHA for the current bootstrap wave, reread them before
each standalone or stack-root bootstrap, and recompute unstarted work if the tip
changes. Never infer a base from the current checkout, a stale tracking ref,
project metadata, or a branch name alone.

Before any fresh worker mutation, independently observe its actual stable
repository identity, remote, isolated worktree, current branch, and full
starting SHA. Require an exact match with its handoff. A fresh worker then
establishes the intended unit head branch from that verified integration
base or prerequisite HEAD and reads back the branch and initial HEAD before
content writes. Missing or mismatched evidence stops that lane.

Before reassigning a clean worker, first verify the prior unit's expected
head branch and current HEAD and prove its worktree clean and unambiguous. Then
switch through G-owned branch transport to the next unit's independently
verified integration base or prerequisite HEAD, read back that starting branch
and SHA, create the new unit head, and read back its initial HEAD before
content writes. A same-unit resume instead remains on its expected head
branch, verifies current HEAD, and preserves inspected dirty work. Saved-project
placement, task title, and prior dialogue never substitute for these facts.

## Task scheduling

Read [task-delivery.md](task-delivery.md) before decomposing the selected specs
into delivery units, computing readiness, or assigning a worker. It owns task
coverage, unit identities, prerequisite evidence, and integration strategy.

A worker handoff includes the current spec and assigned task details, unit
identity, exact repository and base, required contribution and validation,
review budget, and G obligations. Reassign a clean worker only after its prior
unit's branch and HEAD are verified. Same-unit resume preserves inspected dirty
work; changing units uses the independently verified starting-point protocol.

## Candidate review

After implementation and required validation, the worker locally commits the
stable candidate and becomes quiescent with a clean worktree. It returns its
exact base and full HEAD. Enter `review-candidate` under
[candidate-review.md](candidate-review.md) before the first push. Admit only
its complete current receipt. A clean result returns the same worker for
publication; findings return it for repair or rebuttal; execution, cleanup,
identity, and budget failures follow that reference's closed recovery rules.
Candidate Review never satisfies the later hosted gate.

## Pull-request topology

Apply [task-delivery.md](task-delivery.md) before choosing or changing a unit's
base and PR boundary. Return the actual topology and exact task contribution
mapping with every unit result. Semantic task dependencies do not determine
standalone versus stacked publication.

## Hosted review convergence

Apply [completion.md](completion.md) to derive and verify the unit contribution
and exact closing references before every G Send handoff.

Treat the draft returned by a fresh G Send publication as intermediate
evidence. When the candidate's full HEAD, body, base, and stack topology are
stable, the assigned worker must:

1. make the PR ready through the focused G owner and independently verify the
   draft-to-ready transition against the unchanged full HEAD;
2. retain the typed transition evidence and use the G-owned ready-wait workflow
   for the automatic initial Codex review without posting an explicit request;
3. return to `reconcile` with the exact normalized review and CI evidence.

Use one total 30-minute G-owned wait for each ready or explicit-request
lineage. If no valid initial ready lineage can be reconstructed, use G-owned
read-only reconciliation; block when it cannot recover the exact lineage.
Never substitute an explicit request or toggle the PR back to draft. Resume the
same receipt and deadline after interruption.

Project the terminal result into one Delivery Features-owned
`hosted_review_acceptance`:

- G terminal `clean` for the exact HEAD produces `provider-clean`.
- For G terminal `findings`, classify every finding through G. An `actionable`
  code change returns the same worker for one budgeted repair, required
  validation, a new commit, and Candidate Review before push. An `actionable`
  evidence response follows the unchanged-HEAD rebuttal path below.
  `needs-user-decision` routes to `deferred`. For evidence-response
  `actionable`, `already-addressed`, `informational`, or `obsolete`, retain G's
  evidence, post G-owned evidence replies to addressable findings authorized by
  this delivery, and retain the disposition for findings without an addressable
  thread. Resolve only a G-admitted actionable finding after its implemented
  fix and verified reply; never resolve a no-change disposition. Then spend one
  review-driven revision on a fresh local Candidate Review of the unchanged
  HEAD that explicitly evaluates the rebuttal. If it is clean and no code
  change or user decision remains, produce `adjudicated-clean` without an empty
  commit or another hosted request.

A changed candidate uses one new full HEAD, invalidates both review gates, and
requires one fresh explicit hosted re-review lineage after Candidate Review and
push. If another repair or rebuttal would exceed revision ordinal `2`, route to
`blocked` without changing the candidate.

`pending-at-deadline`, provider failure, request-correlation failure, or
ambiguous evidence routes to resumable `blocked` with the claim and exact
lineage retained. A stale result returns to `reconcile` to inspect the current
PR and candidate; it never authorizes a duplicate request. `not-requested`,
absence of comments, zero threads, or draft-only evidence is not hosted
acceptance.

Before final delivery proof, independently reread the actual PR HEAD, ready
state, base branch, body identity, and standalone or immediate-parent stack
topology. Require those facts to match the reviewed contract, candidate
receipt, and published intent, plus required validation and CI. Accept only
`provider-clean` or `adjudicated-clean`, and report which one occurred.
Provider-only PR base, body, or topology drift suspends hosted acceptance. If
authoritative readback restores every reviewed value while the contract, base
tip, candidate HEAD, tree, and delta remain unchanged, the prior exact-state
evidence is admissible; otherwise a new supported review lineage is required.

These receipts and observations remain external delivery evidence available
from G, GitHub, and task history. Do not persist them in the repository-claims
registry or add a delivery-state machine.

## Completion and claim release

After [completion.md](completion.md) verifies every selected spec, its tasks,
assembled outcome evidence, PRs, and linkage dispositions, stop and observe
every worker and reviewer. No task except the bound orchestrator may remain able to mutate a repository or
hosted target, and no request, push, reply, resolution, or wait may be
outstanding. The orchestrator then makes exact whole-group claim release its
last external effect, inspects every selected repository as unclaimed, and
enters `complete`. A release or readback failure enters `blocked` and never
claims successful completion.

For handoff or abandonment performed by another invocation, independently
observe the old orchestrator stopped as well as every task it created before
release. `blocked` and `deferred` delivery results retain their claim for a
legitimate resume.

Before every handoff to a G-owned workflow, the orchestrator or worker making
that handoff runs the shared
[codex-dependency-preflight.md](../../../references/codex-dependency-preflight.md).
Before any hosted pull-request, review, or stack write, that same role applies
the shared
[hosted-content-safety.md](../../../references/hosted-content-safety.md)
contract to the final rendered content. Carry both obligations in every worker
handoff that permits G-owned work; an orchestrator check never substitutes for
the worker's own check.

## Resume and replacement

Reconstruct current truth in this order:

1. authoritative saved specs, linked task bodies, and prerequisite declarations;
2. current repository branches, commits, and worktrees;
3. current pull-request, hosted-review, and CI state;
4. visible Codex task history, candidate-review evidence, and worker handoffs;
5. the repository registry only for orchestrator ownership.

The registry does not prove that a worker is running, a branch is clean, a PR
exists, or validation passed. Reconcile those facts from their owners.

Recall the same worker for a repair, rebase, or review fix when its task and
worktree remain trustworthy. Create a replacement lane only when the old lane
is unavailable or unsafe and current Git state is independently understood.
Replacing a worker does not replace the orchestrator or alter the claim.

For an ambiguous task or non-G provider effect, inspect current authoritative
state once. Continue from a proved effect, retry only after proved
non-application, and stop on unresolved ambiguity. For a G-managed review
operation, use its owned journal reconciliation and never create a replacement
mutation when it reports missing, conflicting, ambiguous, or owner-required
recovery. Do not introduce another operation journal.

A worker may replace an invalid or unavailable evidence command with a
platform-correct command when outcome, scope, acceptance criteria,
dependencies, and non-goals remain unchanged. Record the substitution and
continue in the same task and worktree. Material semantic drift requires user
direction; a validation-only correction never requires a new claim,
orchestrator, or worker.
