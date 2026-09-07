# Delivery Orchestration

Read before delegation, scheduling, recovery, hosted review, or final
reconciliation. The skill registry owns graph edges; this reference owns their
conditions. [states.md](states.md) owns result meanings.

## Transition conditions

| from | to | when |
| --- | --- | --- |
| intake | claim-repositories | Saved spec/task selection and exact affected repository identities are resolved; current coordinator identity is available. |
| intake | deferred | A material selection or authority decision prevents responsible work before acquisition. |
| intake | blocked | Input, identity, or required capability cannot be established before acquisition. |
| claim-repositories | reconcile | The current task acquired/reused, bound, and read back its exact repository set. |
| claim-repositories | blocked | Ownership cannot be established; safely abandon this invocation's unused provisional claim when possible and report any retained uncertainty. |
| reconcile | schedule | At least one selected unit has useful dependency-ready work or a justified recovery attempt; omit blocked and already active contributions. |
| reconcile | release-claims | Selected work is verified or no further useful work can proceed; all actors are stopped, effects resolved, work preserved, progress save attempted, and the pending terminal outcome is known. |
| reconcile | blocked | An actor, mutation, work-preservation, or ownership ambiguity prevents safe release; report the retained claim/uncertainty. |
| schedule | deliver-unit | A bounded independent lane has verified ownership, worktree, base, contribution, selected role, and available repair budget for its assignment. |
| schedule | reconcile | Only active lanes remain, an assignment returns, or current evidence requires recomputing readiness. |
| deliver-unit | review-candidate | A validated, locally committed candidate is stable, the developer is quiescent, and current independent review is required. |
| deliver-unit | reconcile | A worker returns publication, progress, findings, interruption, or blocker evidence; reconcile each lane separately. |
| review-candidate | reconcile | A reviewer returns a verdict, failed attempt, or cleanup evidence; the coordinator decides repair, publication, recovery, or unit pause. |
| release-claims | complete | Exact release is proved and all selected outcomes, progress writes, reviews, and CI satisfy completion. |
| release-claims | deferred | Exact release is proved and preserved work awaits a material user decision, explicit stop, merge, or deployment authority. |
| release-claims | blocked | Exact release is proved but a capability, validation, review, budget, or progress-save blocker remains; or release itself remains uncertain. |

Waiting is change-driven and bounded. A lane's blocker does not terminate
independent work. Once only active lanes remain, wait for their result or a
material change; do not duplicate work or busy-poll. Before returning a global
blocked/deferred result with owned claims, use the release path whenever it is
safe. A retained claim requires an exact unresolved safety reason.

## Current coordinator and native subagents

The invoking task remains the coordinator and keeps its model/reasoning. When
supported, request `🚚 Deliver · <spec or selected scope>` as its title. Renaming
is best effort; titles never establish identity or gate work. Do not create,
fork, relocate, or hand off to another visible coordinator or worker task.

Before delegation, read the selected [shared role](../../../references/subagents.md):
`developer` for implementation/publication, `code-reviewer` for independent local
review, or `evidence-researcher` for optional bounded investigation. Request the
role's model/reasoning explicitly unless the caller overrides it. Use native
subagents with self-contained handoffs. If required implementation or review
transport is unavailable, preserve and pause safely; do not substitute visible
tasks, external reviewer processes, or same-context self-review.

The coordinator alone holds the claim token, authorizes assignments and
publication, reserves repair rounds, validates evidence, writes planning
progress, and performs release. Research/review subagents remain read-only.
Developer authority covers only its assigned worktree and exact scoped G
operations; it does not grant merge, deploy, direct issue closure, recursive
delegation, or claim operations. The coordinator remains the user's contact.

## Worker handoff and isolation

Read [task-delivery.md](task-delivery.md) for readiness, contribution coverage,
PR grouping, and actual integration bases. A handoff includes the selected
spec/tasks, unit ID and PR binding, bounded contribution, exact repository,
worktree, base/HEAD, selected role, relevant instructions, validation method,
repair count, and G publication/review obligations. Pass evidence references
without the developer's preferred conclusion to independent reviewers.

Create separate worktrees for implementation lanes. Before content mutation,
verify actual repository/remote, worktree, branch, and full starting SHA against
the handoff. Establish and read back the intended unit branch from the verified
integration or prerequisite HEAD. Never bootstrap from an incidental checkout
or trust only a task title, cwd, or saved-project label.

Default to one implementation lane per repository; parallel independent lanes
must have isolated worktrees and non-overlapping assignments. A same-unit
resume preserves understood dirty work and verifies the existing branch/HEAD.
Reuse a clean lane for another unit only after proving prior work preserved,
no old worker can write, and the new branch/base correct. Keep execution-progress
edits out of implementation commits under [progress.md](progress.md).

## Implementation and local review

The developer implements the bounded contribution, validates observable
behavior, commits the candidate, and becomes quiescent with a clean worktree.
The coordinator then runs [candidate-review.md](candidate-review.md) before any
push of new candidate content. A clean review authorizes the developer's next
publication phase for that exact candidate. Findings reserve one repair round;
return the same understood work to its developer or a safely reconciled
replacement. Never treat review execution failure as a clean result.

## Explicit hosted review

Before G Send, use [completion.md](completion.md) to derive exact contribution
and closing references. New draft publication is intermediate. Once the exact
published candidate is stable, mark the PR ready through G and independently
verify ready state and unchanged full HEAD. Then use G's explicit Codex review
request to post `@codex review` bound to that commit, including the initial PR
review. Automatic reviews and ready-triggered lineages do not satisfy this
workflow. Do not wait for a ready event to generate review automatically.

Use one request identity per intended review cycle and preserve G's complete
receipt and original deadline. Reconcile an uncertain request through G before
retrying; never post another mention merely because output is missing. Resume
an existing request against its exact PR/HEAD without resetting its deadline.
A changed candidate must pass local review, be pushed, remain ready, and receive
one fresh explicit request for its new full HEAD. A task-progress-only update
does not create another review request for unchanged candidate content.

Pass one total 30-minute duration to the G-owned bounded wait for each explicit
request lineage. Check required CI and current PR evidence through their G
owners. Infrastructure failures and timeouts pause the affected unit, with the
exact request retained. Independent selected units may continue. Generic
`not-requested`, automatic review evidence, stale results, absence of comments,
or zero unresolved threads never substitute for this explicit-request result.

Project G's terminal review result into `hosted_review_acceptance`:

- `clean` for the current exact HEAD and explicit lineage gives `provider-clean`.
- `findings` require classification of every finding through G. Code changes
  reserve the next repair round, then implement, validate, commit, locally
  review, push, and explicitly request review of the new HEAD. A material
  user decision pauses that unit.
- Evidence-backed no-change dispositions may yield `adjudicated-clean` after
  any authorized exact-thread replies and a fresh clean local review that
  evaluates the rebuttal. Reserve one round for the rebuttal; the subsequent
  review belongs to that same round. Do not create an empty commit or request
  another hosted review for unchanged HEAD merely to manufacture provider-clean.
  Report the distinction. Resolve only a G-admitted actionable finding whose
  fix and reply are verified; do not execute a suggested resolution for a
  no-change disposition.

Two rounds apply per PR across both gates under candidate-review.md. Exhaustion
blocks only that PR and its dependents. Provider state/HEAD/base/topology drift
suspends acceptance: restore and verify the exact reviewed state or revalidate
and obtain a supported new explicit lineage when the candidate changed. Never
consume an old result for a new HEAD or bypass required CI.

## Recovery, progress, and safe pause

On resume inspect, in order: authoritative selected contracts and progress;
current branches/commits/worktrees; exact PR/review/CI state; coordinator history,
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
