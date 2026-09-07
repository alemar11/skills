# Delivery Orchestration

Read before delegation, scheduling, recovery, hosted review, or final
reconciliation. The skill registry owns graph edges; this reference owns their
conditions. [states.md](states.md) owns result meanings.

## Transition conditions

| from | to | when |
| --- | --- | --- |
| intake | claim-repositories | Saved spec/task selection and exact affected repository identities are resolved; current coordinator identity is available. |
| intake | closeout | A material decision, explicit stop, unresolved input, identity or capability prevents acquisition; retain the corresponding deferred or blocked outcome. |
| claim-repositories | reconcile | The current task acquired/reused, bound, and read back its exact repository set. |
| claim-repositories | closeout | Ownership cannot be established; safely abandon this invocation's unused provisional claim when possible and report any retained uncertainty. |
| reconcile | schedule | Scope is reconciled under task-delivery.md for at least one selected unit with dependency-ready work or a justified recovery attempt; omit blocked and already active contributions. |
| reconcile | release-claims | Selected work is verified or no further useful work can proceed; all actors are stopped, effects resolved, work preserved, progress save attempted, and the pending terminal outcome is known. |
| reconcile | closeout | An actor, mutation, work-preservation, or ownership ambiguity prevents safe release; report the retained claim/uncertainty. |
| schedule | deliver-unit | A bounded independent lane has verified ownership, worktree, base, contribution, supported integration topology, selected role, and available repair budget for its assignment. |
| schedule | reconcile | Only active lanes remain, an assignment returns, or a caller clarification or current evidence requires recomputing scope/readiness. |
| deliver-unit | review-candidate | A validated, locally committed candidate is stable, the developer is quiescent, and current independent review is required. |
| deliver-unit | reconcile | A worker returns publication, progress, findings, interruption, or blocker evidence, or a material caller clarification requires scope reconciliation; reconcile each lane separately. |
| review-candidate | reconcile | A reviewer returns a verdict, failure or deadline/cleanup evidence under candidate-review.md; the coordinator decides repair, publication, recovery, or unit pause. |
| release-claims | closeout | Release succeeded or remains uncertain; preserve complete/deferred/blocked from delivery evidence, with blocked for unresolved release safety. |
| closeout | complete | Closeout report prepared; exact release and all selected outcomes, progress writes, reviews and CI satisfy completion. |
| closeout | deferred | Closeout report prepared; a material decision, explicit stop or separately authorized action remains, with no claim acquired or exact safe release proved. |
| closeout | blocked | Closeout report prepared; a capability, validation, review, budget, progress-save or safety blocker remains, including uncertain release. |

Waiting is change-driven and bounded. A lane's blocker does not terminate
independent work. Once only active lanes remain, wait for their result or a
material change; do not duplicate work or busy-poll. Before returning a global
blocked/deferred result with owned claims, use the release path whenever it is
safe. A retained claim requires an exact unresolved safety reason. Every terminal
path passes through [closeout.md](closeout.md), including pre-acquisition stops
and unsafe pauses; closeout never substitutes for safe release.

## Current coordinator and execution roles

The invoking task remains coordinator under the profile policy in SKILL.md.
Do not create, fork, relocate, or hand off to another coordinator. Requested
settings and titles are not proof of execution identity.

Before delegation, read the selected [shared role](../../../references/subagents.md):
`developer` for implementation/publication, `code-reviewer` for independent local
review, or `evidence-researcher` for optional bounded investigation. Request the
role's model/reasoning explicitly unless the caller overrides it. Select the
developer transport and apply its setup, assignment, reuse, and recovery rules
from [worker-runtime.md](worker-runtime.md). Research and review roles use native
subagents with self-contained handoffs. If required implementation or review
transport is unavailable, preserve and pause safely; do not substitute another
surface's transport, external reviewer processes, or same-context self-review.

The coordinator alone holds the claim token, authorizes assignments and
publication, reserves repair rounds, validates evidence, writes planning
progress, and performs release. Research/review subagents remain read-only.
Developer authority covers only its assigned worktree and exact scoped G
operations; it does not grant merge, deploy, direct issue closure, recursive
delegation, or claim operations. The coordinator remains the user's contact.

## Worker handoff and isolation

Read [task-delivery.md](task-delivery.md) for readiness, contribution coverage,
PR grouping, supported topology and reconciliation before republishing. A handoff
includes the selected spec/tasks, explicit caller scope decisions, unit ID and PR
binding, bounded contribution, exact repository, worktree, base/HEAD, selected
role, relevant instructions, validation method,
repair count, and G publication/review obligations. Pass evidence references
without the developer's preferred conclusion to independent reviewers. Include
available execution timing and token telemetry in handoffs back to the
coordinator, with identity and coverage as defined in [closeout.md](closeout.md);
missing telemetry does not block a worker result.

Create separate worktrees for implementation lanes. Before content mutation,
verify actual repository/remote, worktree, branch, and full starting SHA against
the handoff. Establish and read back the intended unit branch from the verified
integration or prerequisite HEAD. Never bootstrap from an incidental checkout
or trust only a task title, cwd, or saved-project label.

Default to one implementation lane per repository; parallel independent lanes
must have isolated worktrees and non-overlapping assignments. A same-unit
resume preserves understood dirty work and verifies the existing branch/HEAD.
Reuse follows [worker-runtime.md](worker-runtime.md), including the App-only
run boundary. Keep execution-progress edits out of implementation commits under
[progress.md](progress.md).

## Implementation and local review

Assign initial implementation and each reserved repair batch through
[`se:implement`](../../implement/SKILL.md) in the existing developer lane. Supply
its bounded assignment and mark independent review as coordinator-owned.
Implement returns a validated committed candidate and becomes quiescent; it does
not launch a duplicate reviewer or publish within its implementation phase.

The coordinator applies [candidate review](candidate-review.md)
before any push of new candidate content. A clean receipt satisfies the local
review gate for that exact candidate; publication also requires the
[outcome-alignment check](completion.md#selected-outcome-verification).
Findings return to the coordinator, which alone reserves
a batch under the [shared repair budget](../../../references/review-repair-budget.md)
and reassigns Implement or an evidence-backed rebuttal. Review execution failure
never means clean. The separate G publication phase remains under the coordinator's
authority even when executed by the same developer agent. Local review attempts
follow the [candidate deadline](candidate-review.md#attempt-deadline); a live
reviewer does not authorize waiting past it.

## Hosted review handoff

Before G Send, use [completion.md](completion.md) to derive exact contribution
and closing references. New draft publication is intermediate. After the reviewed
candidate is published, mark the PR ready through G and independently verify
ready state and unchanged full HEAD.

Compose [`se:review-pr`](../../review-pr/SKILL.md) to request or resume and monitor
the exact ready candidate's explicit hosted review, including its first review.
Pass the target and any existing G request receipt/deadline. It returns the
provider verdict and findings; it owns no agents, repairs, CI or acceptance.
Inspect required CI separately through its G owner for the current HEAD.

The coordinator maps completed provider evidence into the hosted gate:

- Clean for the exact current HEAD and explicit lineage gives `provider-clean`.
- Findings require classification of every finding through G. Code changes
  reserve the next shared round, then use Implement, validation, commit, local
  candidate review and publication before invoking Review PR for the new HEAD.
- Evidence-backed no-change dispositions may give `adjudicated-clean` after
  every finding has evidence, required authorized exact-thread replies are
  verified, and fresh independent local review accepts the unchanged-HEAD
  rebuttal. Reserve one round for that rebuttal and its review. Report this
  separately from the provider verdict; do not create an empty commit or
  repeat hosted review of unchanged content to manufacture provider-clean.

Resolve only a G-admitted actionable finding whose implemented fix and reply
are verified; never follow a suggested resolution for a no-change disposition.
Material user decisions pause the affected unit. Pending reviews, failed CI,
exhausted budgets, or blocked PRs do not stop independent selected work.
Review PR's completed result, including findings, never means Delivery complete.
The coordinator still verifies local review, required CI, assembled outcomes,
progress and release. Target/base/topology drift invalidates affected evidence;
reconcile before applying results. Counts and G deadlines survive re-entry.

## Recovery, progress, and safe pause

On resume inspect, in order: authoritative selected contracts, explicit caller
scope decisions and progress; current branches/commits/worktrees; exact
PR/review/CI state; coordinator history,
worker identities, receipts and repair counts; and claims for ownership only.
Do not persist a workflow node or scheduling queue. Reacquisition does not reset
budgets or make stale evidence current.

Recover a worker's existing result when attributable. Otherwise replace it only
once the prior execution is confirmed stopped, its exact work is understood and
preserved, and no outstanding mutation can race the replacement. Resume the same
unit's worktree/commits with a focused handoff; repeat only invalidated checks.
Uncertain liveness or ownership retains the claim. A changed condition may
justify an automatic retry; repeated unchanged failure pauses the unit instead
of launching an endless series of replacements.

Write material progress through [progress.md](progress.md). At success or when
no further useful work can proceed, preserve every worktree and result, resolve
writes, stop all actors, attempt final progress synchronization, and use
[repository-claims.md](repository-claims.md) to release the complete set. Store
the pending result before release: successful delivery, a required decision, or
a blocker. Release preserves that result; it does not turn a pause into success.

Every hosted handoff applies the shared
[G preflight](../../../references/codex-dependency-preflight.md) and
[hosted-content safety](../../../references/hosted-content-safety.md)
immediately before its own writes. Project those obligations into developer
handoffs. A coordinator check never substitutes for the actual writer's check.
