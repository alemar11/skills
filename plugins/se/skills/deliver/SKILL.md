---
name: deliver
description: "Orchestrate isolated workers to deliver specs, issues, or bounded requests through ready PRs."
---

# Deliver

Keep the current task as orchestrator with its configured model and reasoning.
Even a single bounded change uses a worker. Follow shared
[execution scope](../../references/execution-scope.md); this skill's worker
contract is local, not the shared developer role used by Deliver Features.

## Select and assign

Accept a saved SE spec, selected issues/tasks, or directly described bounded work.
Resolve the intended outcome, repository identities, acceptance checks and caller
constraints. A saved spec selects the whole spec unless the caller names a subset;
read its task contracts and accepted decisions without rewriting requirements.
Do not implement unselected prerequisites. Ask only for material unresolved
scope or authority; keep independent selected work moving.

Choose useful repository-bound PR units, not one worker or PR per checklist item.
Default to one active worker per repository; add isolated workers for independent
assignments. Read [integration.md](references/integration.md) only for dependencies,
stacks, cross-repository outcomes or topology changes. Task order alone does not
require a stack. Assign one writer per branch, PR and shared artifact, including
any requested source-progress edits. Worktrees do not isolate ports, databases
or external services; separate those resources or serialize their use.

Read the shared [runtime surface](../../references/codex-runtime-surface.md), then
[workers.md](references/workers.md) before creating, assigning or recovering workers.
Supply one complete assignment covering implementation through publication and
required CI. Ordinary phase transitions need no coordinator approval round trip.

## Authority and worker work

Invocation, explicit or implicit, authorizes creating visible App worker tasks
or native CLI subagents for the selected scope, along with scoped worktrees,
branches, implementation, commits, pushes, PR creation/readiness and CI corrections.
Do not ask for separate worker-task creation permission or renew that permission
when continuing the same delivery. Explicit user restrictions win: no-push
work ends with a local handoff and PR delivery explicitly incomplete. Never ask
to override that restriction. Merge, deployment, releases, production actions,
direct issue closure, destructive recovery and scope expansion are not authorized.

The worker composes [Implement](../implement/SKILL.md) for local implementation,
self-inspection and relevant validation, then uses G publication and CI workflows
in the same assignment. Implement's responsibility still ends at the committed
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

Consume each result: PR URL, exact HEAD/base, validation, required CI state,
blockers and preserved work. Verify current PR/CI facts and selected outcomes;
check assembled behavior when contributions interact. Reuse valid evidence
instead of repeating every worker test. Changed scope, base or HEAD invalidates
affected evidence. A worker's completed turn alone is not delivery proof.

Finish when every PR required for the selected scope is non-draft, required CI
passes, and selected outcomes and any explicitly required reviews are verified.
No required CI must be established from current evidence, not missing results.
Already-incorporated work needs current outcome proof, not a duplicate PR.
Draft, pending, partial and blocked results are not successful delivery. Ready
PRs remain unmerged; merge/deployment prerequisites needing further authority
remain blockers rather than being silently weakened.

Report ready PRs, verified outcomes/checks and remaining actions concisely. On
interruption or partial results include a resume handoff under the worker
recovery rules. Preserve worktrees and leave App workers visible by default.
No mandatory retrospective, token accounting, claims, lock replacement, scheduling
graph or durable ledger. Separate runs have no automatic ownership exclusion;
known competing work must still be reconciled before a conflicting write.

## Skill Dependencies

Bundled [Implement](../implement/SKILL.md) owns local work without delegation or
publication. Installed `g@alemar11` owns Git/GitHub publication, required CI and
optional stacks; load only the workflows needed for the selected operation.
The orchestrator owns assignments, integration and acceptance.
