---
name: deliver-features
description: "Deliver saved SE specs or selected tasks through independently reviewed, ready pull requests."
---

# Deliver Features

Follow the shared [execution scope](../../references/execution-scope.md) for
standalone and composed invocation.

## Scope and authority

Deliver authoritative saved GitHub or Markdown specs. Select the whole spec by
default or exact tasks explicitly named by the caller. Read
[task-delivery.md](references/task-delivery.md) during Intake and on material
caller clarifications for scope reconciliation, prerequisites, coverage,
PR grouping and integration. Unfinished prerequisites
outside selection need permission before implementation; keep independent
selected work moving.

The intended coordinator is Astra (`gpt-6-astra`) in the current task, with
the caller's configured reasoning. This skill does not change task settings or
create a replacement coordinator; explicit caller profile choices take precedence.
Rename it to `🚚 Deliver · <scope>` when supported, without gating work on its title.
Use native subagents and isolated implementation worktrees; never create a
separate visible coordinator or worker task. Before delegation read the selected
[shared role](../../references/subagents.md): `developer`, `code-reviewer`, or
`evidence-researcher`.

Own scope, integration choices, evidence acceptance and recovery. Delegate bounded
execution, consume concise results, and read branch-specific procedures only
when needed. Choose routine sequencing without extra approval; escalate material
scope or authority decisions. Do not replay completed work to restate its proof.

Invocation authorizes selected implementation, worktrees, branches, commits,
pushes, PR publication/readiness, explicit hosted review requests and scoped
finding replies, progress updates, and safe claim release. It does not authorize
merge, deployment, releases, direct issue closure, destructive recovery, or
unselected work. Preserve inspected dirty work and unrelated content.

## Required routing

Read [orchestration.md](references/orchestration.md) before scheduling, task
operations, recovery, or hosted review; [repository-claims.md](references/repository-claims.md)
before claiming/releasing; [candidate review](references/candidate-review.md)
before local review and the [repair budget](../../references/review-repair-budget.md)
before assigning repairs or reconstructing counts;
[completion.md](references/completion.md) before publication, closing-reference projection or completion; and
[progress.md](references/progress.md) before saved status updates or resume.
Read [closeout.md](references/closeout.md) at Intake to capture available run
measurements, and before every final report for delivery results and a mandatory
workflow retrospective.

Before every hosted handoff apply the shared
[G preflight](../../references/codex-dependency-preflight.md) and, immediately
before each hosted write, [hosted-content safety](../../references/hosted-content-safety.md).
Carry those obligations into every developer handoff that permits hosted work.
Read [states.md](references/states.md) and the shared
[workflow graph](../../references/workflow-graph.md) before interpreting states.

## Workflow graph

The registry owns structural edges; orchestration.md owns their conditions.
Several independent lanes may occupy implementation or review, but every result
returns to reconciliation. A blocked PR does not stop independent selected work.

| node_id | kind | purpose | entry_conditions | inputs | outputs | transitions | stop_if | side_effects | terminal_states |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| intake | action | Resolve saved specs, exact selected tasks, repositories and current coordinator. | Explicit delivery or resume request. | Saved contracts, caller scope. | Selection, repository set, coordinator identity. | claim-repositories, closeout | Selection or identity cannot be resolved. | read, transient |  |
| claim-repositories | action | Acquire and bind ownership to the current task. | Valid selection and current coordinator identity. | Frozen repository set and fencing context. | Verified bound claim. | reconcile, closeout | Ownership cannot be established. | durable |  |
| reconcile | validation | Reconcile requested outcomes, caller decisions, lanes, reviews, budgets and blockers. | Bound ownership, a lane result or material caller clarification. | Contracts, caller decisions, Git, PR, CI, agent and claim evidence. | Ready work or preserved pending result. | schedule, release-claims, closeout | Unsafe actor, mutation, preservation or ownership ambiguity. | read, transient |  |
| schedule | decision | Assign bounded independent work or await active lanes. | Current evidence supports selected work. | Ready units, supported topology, bases, lanes, role and repair budget. | Scoped assignments. | deliver-unit, reconcile | No new responsible assignment. | read, transient |  |
| deliver-unit | action | Implement and validate; after review and outcome alignment publish and converge one PR. | Verified isolated lane and authorized phase. | Selected task contributions, base, role, review and budget. | Committed candidate, reviewed PR, progress or blocker. | review-candidate, reconcile | Lane or candidate evidence is untrustworthy. | durable, hosted |  |
| review-candidate | validation | Independently review the immutable committed candidate. | Validated candidate and quiescent developer. | Contract, coverage, base, HEAD, snapshot, role, deadline and budget. | Review receipt or execution/cleanup evidence. | reconcile | Independence, target or cleanup is uncertain. | read, transient |  |
| release-claims | action | Release the complete claim after verified quiescence and preservation. | All actors stopped, effects resolved, progress attempted, pending result known. | Exact claim and final delivery or pause evidence. | Verified release plus preserved result. | closeout | Release remains ambiguous or unsafe. | durable |  |
| closeout | action | Prepare delivery results, run measurements and a generalizable workflow retrospective. | Pending outcome known; safe release attempted wherever possible. | Captured run evidence, measurement coverage, release or retained uncertainty. | Final report preserving delivery outcome. | complete, deferred, blocked | Evidence limits require a concise best-effort report. | read, transient |  |
| complete | terminal | Report verified delivery of all selected outcomes. | Exact release and all selected delivery/progress gates verified. | Closeout report, final outcome and release evidence. | Delivery report and remaining unselected work. |  | terminal | none | complete |
| deferred | terminal | Report the decision or separately authorized action needed. | Before acquisition or after verified safe release. | Closeout report, preserved work and exact unresolved choice. | Resume handoff. |  | terminal | none | deferred |
| blocked | terminal | Report unresolved capability, review, budget or safety evidence. | No useful independent work remains or safety prevents continuation. | Closeout report, preserved results, blocker, release or retained-claim evidence. | Resume handoff with exact ownership state. |  | terminal | none | blocked |

~~~mermaid
flowchart TD
    intake --> claim-repositories
    intake --> closeout
    claim-repositories --> reconcile
    claim-repositories --> closeout
    reconcile --> schedule
    reconcile --> release-claims
    reconcile --> closeout
    schedule --> deliver-unit
    schedule --> reconcile
    deliver-unit --> review-candidate
    deliver-unit --> reconcile
    review-candidate --> reconcile
    release-claims --> closeout
    closeout --> complete
    closeout --> deferred
    closeout --> blocked
~~~

## Completion and pause

Complete only when selected task checks and assembled outcomes are verified,
PRs are ready with current local review, explicit-request hosted acceptance and
required CI, progress updates are verified, and exact claim release is proved.
Ready does not mean merged; a task subset does not mean the whole spec delivered.

Apply the shared two-round repair budget per PR across both review gates. Pause
exhausted PRs or those awaiting decisions/capabilities while independent work continues. When
no useful work remains, preserve work, stop all actors, save progress, and
release safely before reporting a pause. Retain claims only when safety or
release evidence remains uncertain. Resume through Intake, reacquire ownership,
and revalidate existing evidence without resetting budgets or duplicating review
requests. Workflow nodes and queues are never persisted as progress or claims.

## Result

Every terminal report follows [closeout.md](references/closeout.md): delivery
results with duration and token-usage coverage, followed by a workflow audit of
what worked, what failed, and reusable improvements to this skill or its invoked
skills. The coordinator owns synthesis; optional bounded research does not
change any invoked skill's delegation policy. A paused run reports partial
results and its resume handoff, never a successful delivery claim.

## Skill Dependencies

Bundled [`se:implement`](../implement/SKILL.md) owns bounded implementation and
repairs; [`se:adversarial-review`](../adversarial-review/SKILL.md) supplies local
critique under Delivery's candidate-review contract; [`se:review-pr`](../review-pr/SKILL.md)
requests/monitors hosted review and returns provider evidence. Delivery retains
review acceptance, scheduling, the shared budget, claims, progress and spec verification. Installed `g@alemar11` owns
Git/GitHub transport, publication, review operations, CI and stacks. Delivery
never installs, refreshes, or substitutes dependencies.
