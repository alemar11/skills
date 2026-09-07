---
name: deliver-features
description: "Deliver selected saved SE specs and their tasks through independently reviewed pull requests."
---

# Delivery Features

## Scope and authority

Use `se:deliver-features` only for explicitly selected saved SE specifications
and their complete task plans. Read the canonical
[specification contract](../spec/references/specification.md) and
[task-delivery.md](references/task-delivery.md) during Intake. A verified GitHub
bundle or authoritative Markdown spec is valid input. Do not expand selection
merely because another spec or prerequisite is discoverable.

Invocation authorizes the visible Codex tasks, isolated worktrees, branches,
commits, pushes, pull requests, and review interactions required for those
specs. It does not authorize merge, deploy, release, direct issue closure,
destructive recovery, or unrelated cleanup.

Git branches, commits, pull requests, and provider state are durable outputs.
The local registry coordinates repository ownership only. Reconstruct workflow
position and delivery truth from their authoritative owners; never store
Features, workers, Git, pull-request, review, CI, or current-node state in the
registry.

## Required routing

Load [orchestration.md](references/orchestration.md) before task placement,
worker selection, scheduling, branch or pull-request topology, graph
transitions, hosted review, or final reconciliation. Load
[candidate-review.md](references/candidate-review.md) before
`review-candidate`. Load
[repository-claims.md](references/repository-claims.md) before orchestrator
reuse or any claim operation. Read
[completion.md](references/completion.md) before publication, closure-link
projection, or final reconciliation.

Before every G handoff, run the shared
[G dependency preflight](../../references/codex-dependency-preflight.md).
Before every hosted write, apply the shared
[hosted-content safety contract](../../references/hosted-content-safety.md).
Project both obligations into worker handoffs that permit G-owned work.

Read the shared [workflow-graph contract](../../references/workflow-graph.md)
before interpreting the registry and [states.md](references/states.md) before
interpreting any Delivery Features-owned state or disposition.

## Workflow graph

This table is the structural source of truth. Follow its edges; Mermaid is only
its maintained projection. `schedule` may authorize several concurrent
`deliver-unit` or `review-candidate` occupants, but every result re-enters
`reconcile`.

| node_id | kind | purpose | entry_conditions | inputs | outputs | transitions | stop_if | side_effects | terminal_states |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| intake | action | Resolve selected specs and task contracts, repository identities, and visible home. | Explicit implementation or resume request with exact saved spec references. | Caller request and saved spec and task contracts. | Validated selection, dependency graph, immutable repository set, and visible home. | claim-repositories, deferred, blocked | Selection is ambiguous, cyclic, incomplete, or requires a material user choice. | read, transient |  |
| claim-repositories | action | Acquire or reuse the complete claim and establish one correlated orchestrator. | Intake produced a valid immutable repository set and visible home. | Repository keys, home key, selection, and optional existing claim. | Bound orchestrator identity and fenced repository ownership. | claim-repositories, reconcile, blocked | Ownership, provisional effects, or orchestrator identity cannot be reconciled safely. | durable |  |
| reconcile | validation | Reconstruct current execution truth and resolve ambiguous effects once. | A bound orchestrator exists or material state requires refresh. | Feature, task, Git, pull-request, review, CI, and claim evidence. | Current delivery evidence, trustworthy lanes, and unresolved blockers or choices. | schedule, release-claims, deferred, blocked | An effect remains ambiguous, evidence is unavailable, or continuation needs user authority. | read, transient |  |
| schedule | decision | Compute the ready frontier and choose serial or bounded concurrent lanes. | Reconciled evidence shows unfinished selected Features. | Task prerequisites, unit coverage, delivery evidence, bases, lanes, and review budget. | Bounded unit assignments or a reason to reconcile or stop. | deliver-unit, reconcile, deferred, blocked | No responsible scheduling decision remains. | read, transient |  |
| deliver-unit | action | Implement, validate, and commit one candidate; after review, publish and converge its pull request. | Schedule selected a ready delivery unit and verified its lane and required phase. | Spec/task contracts, unit identity and coverage, worker target, base, candidate-review evidence, budget, and G obligations. | Stable candidate or exact delivery, correction, and blocker evidence. | review-candidate, reconcile | The worker cannot return trustworthy candidate or delivery evidence. | durable, hosted |  |
| review-candidate | validation | Run an independent read-only adversarial review of one immutable candidate. | A stable locally committed candidate passed required validation and lacks admissible current review evidence. | Spec/task content identity, unit identity and coverage, repository, base, HEAD, delta, validation, and budget. | One admissible candidate-review receipt or exact failure evidence. | reconcile | Independence, target, profile, result, cleanup, or budget cannot be established. | read, transient |  |
| release-claims | action | Release the exact complete repository claim as the final external effect. | Reconcile proved successful delivery or authorized handoff/abandonment, all other actors quiescent, and no outstanding mutation. | Bound claim, fencing token, quiescence proof, and final outcome evidence. | Verified whole-group release and retained final outcome evidence. | complete, blocked | Release authority, actor state, ownership, or exact readback is uncertain. | durable |  |
| complete | terminal | Return verified delivery or release outcomes after ownership is removed. | Release-claims verified the whole group unclaimed and retained admissible final outcome evidence. | Final delivery or handoff/abandonment evidence plus release proof. | Plain-language delivery or release report. |  | terminal | none | complete |
| deferred | terminal | Return the material user decision required for safe continuation. | A semantic choice or additional authority cannot be resolved safely. | Reconciled evidence and the smallest concrete question. | Deferred report retaining the claim. |  | terminal | none | deferred |
| blocked | terminal | Return the exact capability, identity, evidence, ownership, review-budget, or reconciliation blocker. | No responsible graph edge remains. | Retained evidence and blocker. | Blocked report preserving any claim not proved released and describing ownership uncertainty. |  | terminal | none | blocked |

~~~mermaid
flowchart TD
    intake --> claim-repositories
    intake --> deferred
    intake --> blocked
    claim-repositories --> claim-repositories
    claim-repositories --> reconcile
    claim-repositories --> blocked
    reconcile --> schedule
    reconcile --> release-claims
    reconcile --> deferred
    reconcile --> blocked
    schedule --> deliver-unit
    schedule --> reconcile
    schedule --> deferred
    schedule --> blocked
    deliver-unit --> review-candidate
    deliver-unit --> reconcile
    review-candidate --> reconcile
    release-claims --> complete
    release-claims --> blocked
~~~

Do not persist a queue, current node, worker assignment, receipt, or retry
record. Resume through `intake -> claim-repositories -> reconcile`, deriving the
continuation from current Feature, task, Git, pull-request, review, CI, and claim
evidence. Reconcile an ambiguous effect once before retrying it.

## Completion gate

Before `reconcile -> release-claims`, apply
[completion.md](references/completion.md) to every selected spec: verify each
task's complete contributions, all feature criteria, assembled validation at
the exact repository HEAD vector, every unit's reviewed PR state, and the exact
issue-linkage disposition. Already-incorporated work requires current outcome
evidence in the intended integration bases. No PR or task count substitutes for
this feature-level verification.

Candidate review is a separate pre-publication gate; hosted Codex review remains
G-owned. Follow their routed contracts for identity, revision budget, finding
disposition, waiting, and recovery. Never claim a provider-clean verdict from
an adjudicated finding.

If the caller requires a PR to remain draft, return `deferred`. A blocked or
deferred delivery retains its claim for legitimate resume. Successful delivery
must make workers and reviewers quiescent, release the whole claim, verify it is
unclaimed, and only then enter `complete`.

## Result

Report each spec's outcome evidence and task-to-unit/PR mapping, repositories,
branches, actual bases and topology, exact HEAD vector, validation, candidate
review, hosted acceptance, CI, closing references, pending closure actions, and
claim release. Also report worker reuse, blockers, and the smallest next action.
Keep transient receipts in task history, not the claim registry.

## Skill Dependencies

This skill requires installed `g@alemar11` workflows for its selected Git,
GitHub, hosted-review, CI, and stack operations. It never installs, refreshes,
or substitutes that dependency.
