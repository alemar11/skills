---
name: deliver
description: "Orchestrate isolated workers to deliver specs, issues, or bounded requests through ready PRs."
---

# Deliver

Use the current task as delivery lead and orchestrator, designed for
`gpt-6-astra` with caller-configured reasoning. Honor explicit profile overrides;
do not change task settings or create a replacement coordinator.
Once scope is known, rename that task to `🚚 Deliver · <scope>` when supported.
Reserve 🚚 for the orchestrator; worker titles follow their own contract.
Titles are metadata and never gate execution.
Even a single bounded change uses a worker. Follow shared
[execution scope](../../references/execution-scope.md); this skill's worker
contract is local, not the shared developer role used by Deliver Features.
Deliver selected scope and return its result to the caller. Backlog discovery,
recurring monitoring and queue persistence belong to the caller.

## Select and assign

Accept a saved SE spec, selected issues/tasks, or directly described bounded work.
Resolve the intended outcome, repository identities, acceptance checks and caller
constraints. A saved spec selects the whole spec unless the caller names a subset;
read all task contracts and accepted decisions without rewriting requirements.
Do not implement unselected prerequisites. Ask only for material unresolved
scope or authority; keep independent selected work moving.

Choose useful repository-bound PR units, not one worker or PR per checklist item.
Default to one active worker per repository; add isolated workers for independent
concurrent assignments. Prefer worker/worktree reuse for compatible serial work
under [workers.md](references/workers.md). Choose PR topology before dispatch;
read [integration.md](references/integration.md) when combining contributions,
handling dependencies, stacks, cross-repository outcomes or topology changes.
Parallel execution alone does not require a stack or an extra integration PR.
Assign one writer per branch, PR and shared artifact, including
any requested source-progress edits. Worktrees do not isolate ports, databases
or external services; separate those resources or serialize their use.

Read the shared [runtime surface](../../references/codex-runtime-surface.md), then
[workers.md](references/workers.md) before creating, assigning or recovering workers.
Supply a complete assignment through publication and required CI, or through a
validated commit handoff when a designated worker will integrate the contribution.
Ordinary phase transitions need no coordinator approval round trip.

## Authority and worker work

Delivery authorizes scoped worktrees, branches, implementation, commits, pushes,
PR creation/readiness and CI corrections within the selected scope. Worker
creation must also satisfy the active runtime's authorization rules; skill
invocation cannot replace an explicit task-creation request where the runtime
requires one. Reuse established authority across assignments and continuations;
ask only for missing required authority. Explicit user restrictions win: no-push
work ends with a local handoff and PR delivery explicitly incomplete. Never ask
to override that restriction. Integrating assigned commits into an owned delivery
branch is authorized under the integration contract. Landing PRs, deployment,
releases, production actions, direct issue closure, destructive recovery and
scope expansion are not authorized.

The worker composes [Implement](../implement/SKILL.md) for local implementation,
self-inspection and relevant validation. Assignments that publish a PR then use
G publication and CI workflows. Implement's responsibility still ends at the committed
local candidate; this delivery assignment authorizes the subsequent G phase.
No independent review is required by this skill. Repository/user-required checks
and reviews still apply; optional reviews run only when explicitly requested.
A separately requested managed review workflow retains its own contract and
budget; ordinary implementation and CI correction use no review-round ledger.

Before hosted access, the actual actor applies [G preflight](../../references/codex-dependency-preflight.md)
for the workflows it needs; immediately before every hosted write it applies
[hosted-content safety](../../references/hosted-content-safety.md). Carry these
routes in worker assignments. Do not install, reload or substitute dependencies.

For publication use G Send; it creates drafts and preserves existing draft state.
Deliver owns the subsequent ready transition: the assigned worker applies G's
[network execution](../../../g/references/network-execution.md) and
[gh preflight](../../../g/references/gh-dependency-preflight.md), marks only its
exact validated PR ready using the supported GitHub CLI operation, then reads
back non-draft state and unchanged full HEAD. This is a distinct authorized
transition, not Send behavior or a request for automated review. Use G GitHub
Actions for current checks and CI fixes. Missing readiness capability blocks
completion; do not report a draft as delivered.

The orchestrator supplies exact justified closing references, or an empty set.
A PR may close an issue only if its merge completes that issue's entire outcome
with prerequisites already incorporated. Several unmerged contributions get
ordinary references, not premature closing keywords. Preserve foreign content
and verify actual PR references after publication. Source spec/issue progress
is report-only unless the user requests a separate progress update.

## Coordinate and finish

Wait for worker results, attention requests or meaningful external changes;
do not busy-poll or send generic continuation messages. Workers correct scoped
failures while evidence shows progress. Repeated unchanged failures, unavailable
authority or unresolved decisions yield a precise blocker, not endless retries.
Continue independent units while another is blocked.

Consume each result under the [worker result contract](references/workers.md#assignment-and-result).
Verify current PR/CI facts and selected outcomes. When contributions need combining,
assign a worker to integrate and validate them under the integration contract;
the orchestrator accepts the assembled outcome. Reuse valid evidence
instead of repeating every worker test. Changed scope, base or HEAD invalidates
affected evidence. A worker's completed turn alone is not delivery proof.

Finish when every PR required for the selected scope is non-draft, required CI
passes, and selected outcomes and any explicitly required reviews are verified.
No required CI must be established from current evidence, not missing results.
Already-incorporated work needs current outcome proof, not a duplicate PR.
Draft, pending, partial and blocked results are not successful delivery. Ready
PRs remain unmerged; merge/deployment prerequisites needing further authority
remain blockers rather than being silently weakened.

Return a concise result for the selected scope using the worker result contract;
combine contributions without claiming unselected outcomes. On interruption or
partial results include a resume handoff under the worker recovery rules.
Preserve worktrees and leave App workers visible by default.
No mandatory retrospective, token accounting, claims, lock replacement, scheduling
graph or durable ledger. Separate runs have no automatic ownership exclusion;
known competing work must still be reconciled before a conflicting write.

## Skill Dependencies

Bundled [Implement](../implement/SKILL.md) owns local work without delegation or
publication. Installed `g@alemar11` owns Git/GitHub publication, required CI and
optional stacks; load only the workflows needed for the selected operation.
The orchestrator owns assignments, integration and acceptance.
