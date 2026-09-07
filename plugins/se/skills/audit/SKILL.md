---
name: audit
description: "Monitor a frozen cohort of active SE tasks read-only when explicitly invoked as $se:audit."
---

# Audit SE Sessions

Follow the shared [execution scope](../../references/execution-scope.md) for
standalone and composed invocation.

## Scope

Use this skill only after an explicit `$se:audit` invocation. Observe the
initial cohort of active application sessions that can be attributed directly
to Learn, Idea, Spec, Delivery Features, or another non-monitoring skill owned by the
current SE plugin. Monitor that frozen cohort until every selected session
becomes terminal or the user stops the audit.

## Persistent monitoring objective

At `intake`, establish the following persistent objective for the audit run:

> Monitor the frozen attributed cohort until every selected session reaches a
> terminal state, no session is attributable, or the user explicitly stops the
> audit.

Keep this objective active across bounded waits, temporary no-progress periods,
incomplete reads, and ordinary turn boundaries. Do not end the audit with a
terminal report while any selected session remains `active`, `inProgress`,
stalled, or waiting for input. A progress update is not a terminal report. The
objective ends only at the stopping conditions above.

Keep the audit read-only and return its report in the invoking session. Do not
persist transcripts, findings, checkpoints, or audit state. The runtime
monitoring objective is the sole persistence mechanism allowed by this skill;
it does not authorize model, worker, task, delegation, repository, or hosted
state changes.

Read the shared
[workflow-graph.md](../../references/workflow-graph.md) before evaluating any
SE graph. For each selected session, read the exact active contract for every
confirmed SE skill before assessing it.

Read [states.md](references/states.md) for the human-readable meaning of every
Audit node and for the separate report, evidence, finding, and observed-runtime
state registries. That reference also defines the runtime-checkpoint boundary.

## Workflow graph

The registry is the structural source of truth. Mermaid is its maintained
projection.

| node_id | kind | purpose | entry_conditions | inputs | outputs | transitions | stop_if | side_effects | terminal_states |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| intake | action | Resolve explicit scope, stopping policy, and persistent monitoring objective. | explicit `$se:audit` invocation | user request | frozen audit scope, stop policy, and persistent monitoring objective | capability-check, blocked | invocation is not explicit or targets mutation | none | none |
| capability-check | validation | Establish a reliable live inventory and authoritative-read boundary. | audit scope is frozen | live application capabilities | capability and coverage record | discover, blocked | inventory and authoritative reads are both unavailable | read | none |
| discover | action | Freeze the initial active-session cohort and coverage boundary. | minimum live capabilities are available | active-session inventory | frozen cohort and coverage boundary | attribute, reported, blocked | no reliable cohort boundary can be established | read, transient | none |
| attribute | validation | Retain only sessions with direct SE-use evidence. | initial cohort is frozen | candidate sessions and task-visible evidence | attributed cohort and exclusions | observe, reported | none | read, transient | none |
| observe | action | Read selected sessions and advance their evidence frontiers. | at least one session is attributable | attributed cohort and prior frontiers | fresh session observations and evidence gaps | assess, blocked | all selected evidence is unavailable or unusable | read, transient | none |
| assess | validation | Reconstruct graph conformance and classify evidence-backed findings. | fresh session evidence and skill contracts are available | observations, graph registries, and contract baselines | conformance map, feedback, and finding registry | monitor-decision, blocked | every required baseline or evidence frontier is unusable | read, transient | none |
| monitor-decision | decision | Continue monitoring or return the current terminal report. | selected-session states and evidence gaps are known | assessed cohort and user-stop state | refresh decision or terminal report | refresh, reported, blocked | none | none | none |
| refresh | action | Perform a bounded authoritative wait or read refresh. | at least one selected session remains active | active cohort and evidence frontiers | refreshed states or bounded no-change evidence | observe | user stops during the wait | read, transient | none |
| reported | terminal | Return a complete or explicitly partial read-only report. | no attributable sessions, terminal cohort, or user stop | report artifacts and coverage record | final Markdown report | none | terminal | none | reported |
| blocked | terminal | Report why no responsible audit result can be established. | minimum inventory, contract, or evidence boundary is unavailable | retained evidence and exact blocker | blocker report and smallest recovery input | none | terminal | none | blocked |

## Transition conditions

The `transitions` column lists target IDs only. This matrix is the canonical
condition map for the Audit registry; Mermaid remains its projection.

| from | to | when |
| --- | --- | --- |
| intake | capability-check | scope is valid |
| intake | blocked | invocation or scope is invalid |
| capability-check | discover | a reliable subset is observable |
| capability-check | blocked | no responsible observation is possible |
| discover | attribute | candidates exist |
| discover | reported | no candidates exist |
| discover | blocked | inventory evidence is unusable |
| attribute | observe | attributable sessions exist |
| attribute | reported | no sessions qualify |
| observe | assess | responsible evidence exists |
| observe | blocked | no selected session can be assessed |
| assess | monitor-decision | assessment is responsible |
| assess | blocked | no contract or evidence boundary supports assessment |
| monitor-decision | refresh | a selected session remains active and the user has not stopped |
| monitor-decision | reported | the cohort is terminal, empty, or user-stopped |
| monitor-decision | blocked | no responsible report remains possible |
| refresh | observe | after each bounded refresh |

~~~mermaid
flowchart TD
    intake --> capability-check
    intake --> blocked
    capability-check --> discover
    capability-check --> blocked
    discover --> attribute
    discover --> reported
    discover --> blocked
    attribute --> observe
    attribute --> reported
    observe --> assess
    observe --> blocked
    assess --> monitor-decision
    assess --> blocked
    monitor-decision --> refresh
    monitor-decision --> reported
    monitor-decision --> blocked
    refresh --> observe
~~~

The `refresh` loop represents ongoing monitoring. Terminal nodes have no
outgoing transitions.

## Cohort discovery and attribution

At `capability-check`, inspect current live application capabilities. Require a
way to inventory recent sessions across available projects and hosts, read a
selected session authoritatively, and refresh its state. If full active-session
coverage cannot be established but a reliable subset is available, continue
with `coverage: partial`; do not claim complete coverage.

Treat every bounded page, recent-task window, host partition, or project
partition as incomplete until the runtime's authoritative continuation or
partition boundary is exhausted. For `coverage: complete`, traverse every
available continuation and every relevant host/project partition, deduplicate
by stable session identity, and establish one stable discovery boundary before
freezing the cohort. If inventory changes while a complete pass is assembled,
repeat the bounded pass or downgrade coverage rather than combining an unstable
cohort. A single capped result set—even when it returns the requested maximum—
is never complete-inventory evidence.

When exhaustive traversal is unavailable, freeze only the reliably observed
subset and record `coverage: partial` with the observed cap/window, partitions
visited, unavailable continuation boundary, and the classes of sessions that
may have been omitted. Equivalent complete-inventory mechanisms are acceptable
only when they authoritatively cover the same full active-session population;
repeated overlapping recent-window reads are not pagination.

At `discover`, freeze the deduplicated initial cohort of sessions that are
active at the stable observation boundary. Newly started sessions are outside
the run and require a new or explicitly broadened audit. Exclude:

- the current audit session and other audit or monitor sessions;
- inactive sessions at the discovery boundary;
- unrelated chats and sessions that expose only a skill catalog;
- sessions whose only SE signal is a title, description, project path,
  repository proximity, cache entry, or behavior resemblance.

At `attribute`, confirm SE use only from task-visible evidence such as an
explicit canonical `$se:<skill>` invocation, a direct SE skill source link,
or a verified SE-owned handoff/profile reference and role. G-owned activity
alone is not SE use. Record exact session identity, host, project and
repository when exposed, current state, confirmed skills, comparison-contract
source, and evidence frontier.

If the session's loaded SE version or source revision cannot be established,
record `contract-baseline-unverified`. Compare cautiously with the auditor's
current contract, but keep every contract-derived skill bug, graph violation,
and regression `provisional` or `indeterminate`. Only baseline-independent
runtime, repository, dependency, or user-condition findings may be confirmed.

## Observation and stopping

Read each selected session without sending messages or changing its lifecycle.
Treat timeout, truncation, missing history, or failed reads as evidence gaps.
One unreadable session does not block the cohort when other responsible results
remain possible.

Refresh a selected session after a material state transition, an incomplete or
truncated read, a monitoring gap, and immediately before final judgment. Use
bounded waits for batches supported by the live runtime; otherwise use bounded
authoritative reads and report reduced coverage.

Continue until:

- every selected session is terminal;
- no session was attributable; or
- the user stops the monitor.

A user stop returns `reported` with the evidence collected so far, explicit
partial coverage, and every unfinished session identified. Use `blocked` only
when inventory, contract, or evidence loss prevents any responsible report.
A stalled or input-waiting selected session remains active: no-progress alone
does not invent a terminal state or an overall audit timeout. Keep each wait or
read bounded, then continue the monitor until the session becomes terminal or
the user stops it.

## Graph-conformance reconstruction

For each confirmed skill, use its registry as the structural authority and its
Mermaid only as a projection. Record positively evidenced node entries,
artifacts, authority decisions, side effects, transitions, and terminal state.
Classify each relevant relation as:

- `confirmed`: direct evidence establishes the node or transition;
- `compatible-unobserved`: visible behavior is compatible but the internal
  transition is not exposed;
- `indeterminate`: available evidence cannot support a judgment;
- `violated`: fresh evidence contradicts the active graph contract.

Confirm `graph-violation` only when evidence proves at least one of:

- a transition absent from the registry;
- entry without a required entry condition;
- a prohibited side effect or authority crossing;
- continuation from a terminal node;
- a terminal claim incompatible with required evidence.

Missing narration or hidden reasoning is never automatically a violation. For
the Delivery Features graph, combine current-coordinator and native-subagent evidence only
through independently established session identities and SE handoffs. Several
Delivery Features workers may occupy `deliver-unit` concurrently after one
`schedule` decision, and their independently reviewed unit candidates may occupy
`review-candidate` concurrently before returning to `reconcile`.

For a Delivery Features `complete` claim, require observed
`reconcile -> release-claims -> complete`, exact whole-group release evidence
and absence of the old binding, plus retained final delivery evidence. A later
foreign claim does not invalidate the old release. For delivery, verify all
selected task contributions and assembled outcome evidence without treating a
subset as the whole spec,
exact PR contribution and closing references, and that actual base and topology
match reviewed intent. Read Delivery
[completion.md](../deliver-features/references/completion.md) for that gate and
distinguish `provider-clean` from explicitly reported `adjudicated-clean` hosted
acceptance from an explicit hosted request for the current HEAD. A safely
paused run follows `release-claims -> deferred` or `release-claims -> blocked`.
Retained claims require a concrete unresolved quiescence, preservation, ownership,
or release-safety reason. Successful release does not turn a pause into completion.

A conforming run may still support `graph-design-improvement` when repeated
loops, ambiguous ownership, weak stopping rules, or unavoidable evidence gaps
show that the declared graph itself causes material friction.

## Findings

Keep explicit feedback separate from defect classification:

- **Feedback**: observed strengths, explicit user or agent feedback, and
  evidence-backed friction.
- **skill-bug**: SE-owned behavior contradicts the active skill contract.
- **graph-violation**: observed execution contradicts the registered graph.
- **graph-design-improvement**: execution may conform, but graph structure or
  semantics cause evidenced friction.
- **runtime-limitation**: the application cannot expose or preserve required
  observations.
- **repository-condition**: repository state, dependencies, or instructions
  constrain the run.
- **user-choice**: an explicit user decision explains the path or stop.

Use run-local IDs in first-seen order (`AUD-001`, `AUD-002`, ...). Keep one
entry per root cause with `provisional`, `confirmed`, `resolved`, or `withdrawn`
status. A regression is an evidence-backed flag on a finding, not a standalone
category; require a prior verified baseline for the same behavior and contract.

Prioritize findings:

- `P0`: data loss, security failure, unauthorized mutation, or complete audit
  failure;
- `P1`: workflow blocker, graph escape, or repeated materially wrong behavior;
- `P2`: meaningful degradation or recurring operator friction;
- `P3`: clarity, instruction cost, documentation, or polish.

Do not classify model behavior, runtime availability, repository state, user
input, or a dependency's failure as an SE bug unless SE owns the missing
guardrail.

## Terminal report

Return compact Markdown in this order:

1. **Monitored sessions** — identity, host, project/repository, terminal state,
   confirmed SE skills, and comparison baseline.
2. **Coverage and performance** — coverage boundary, compliant behavior,
   strengths, and evidence gaps.
3. **Feedback** — explicit strengths and friction with evidence.
4. **Graph conformance** — per skill, observed path, relation classifications,
   violations, and confidence.
5. **Finding registry** — ID, status, priority, category, regression flag,
   affected skill/node, impact, evidence frontier, owner, and smallest remedy.
6. **Graph improvements** — proposal, observed motivation, expected value,
   risk, and priority.
7. **Priority order** — highest-value next actions.
8. **Terminal assessment** — assess each used skill separately and distinguish
   SE defects from runtime, repository, dependency, and user conditions.

## Mutation boundary

Do not create, message, resume, rename, pin, archive, fork, or hand off
application sessions. Do not create unrelated goals, edit repositories, write
report files, run Git mutations, or mutate GitHub. The persistent monitoring
objective defined at `intake` is allowed only to preserve audit continuity and
does not authorize any other mutation. Do not invoke another SE workflow
implicitly. If the user requests a fix, finish the audit report and require an
explicit transition to the owning implementation or maintenance workflow.

No script or persistent ledger belongs to this skill. Live application state
is authoritative and all audit state is transient.
