# Delivery workers

Read before worker creation or assignment; use Recovery only when interrupted,
resuming, or replacing a worker. The shared
[runtime surface](../../../references/codex-runtime-surface.md) owns classification.

## Transport and setup

On the App, use a visible task in the exact matching saved repository project
and an isolated worktree. On CLI, use a native subagent with an isolated worktree.
Creating a subagent does not establish filesystem isolation: prepare and assign
its worktree explicitly, and require the same checkout verification as on App.
An unresolved surface or unavailable required transport/target blocks affected
work. Do not substitute the other surface, an external process, or implementation
in the orchestrator. Apply the entrypoint's authorization boundary before worker
creation. Never create a replacement coordinator.

Workers default to `gpt-5.6-luna` with `max` reasoning; explicit user overrides
win. Request those settings, but do not gate editing on effective-model telemetry
or claim that requested settings were independently observed. Use the worker
title `🤖 <assignment>` when supported, naming its bounded work. Include the
repository name only when needed to distinguish otherwise ambiguous tasks.
Do not use the orchestrator's 🚚 prefix. Titles are metadata, not target identity.

Create with the complete initial assignment, not a bootstrap followed by a second
permission message. Pending worktree setup must finish before mutation; the
worker verifies the actual repository/remote, worktree, branch, base and full
starting HEAD against its assignment. Never overwrite dirty content or reuse
an incidental checkout to make the target fit. Resolve a mismatch before editing.
A creation receipt establishes a known creation effect, not a verified checkout.

## Assignment and result

Include the selected outcome and constraints, exact repository and intended
worktree/branch/base, prerequisite commits, relevant source contracts with spec
identity/revision when applicable, validation,
publication authority and the task-to-PR closing references required by
[Task issue closure](../SKILL.md#task-issue-closure). After checkout verification,
the worker's first progress report to the orchestrator includes its permanent
worker/task identity when available and the resolved worktree path. A pending
creation handle or title is not that identity. This report is informational:
editing does not wait for acknowledgment or unavailable identity metadata.
Give only needed context, not the full orchestration conversation.
Carry the entrypoint's G preflight and
[hosted-content safety](../../../references/hosted-content-safety.md) obligations.

The worker owns implementation, self-inspection, tests, PR publication/readiness
and required CI for its branch within that assignment. It loads Implement, then
the applicable G workflows; it does not inherit Deliver Features' developer role,
independent-review gate, phase handoffs or claims. CI fixes remain within the
original outcome and are revalidated and published by the same worker.

When the orchestrator selects a shared integration PR, contribution assignments
end with validated commits made available to the designated integration worker.
They use Implement and return the result below; separate contribution PRs are
needed only when the selected topology requires them. The integration assignment
uses the same worker profile, transport and result contract under
[integration.md](integration.md#integration-assignment). A contribution handoff
completes that assignment, not the selected feature's delivery.

Workers may delegate only Implement's
[optional UI designer](../../implement/SKILL.md#optional-ui-design); other agent
creation is prohibited. Workers cannot broaden scope, mutate another worker's
branch/PR, land PRs, deploy or perform production actions. An integration assignment
may combine assigned commits into its own delivery branch. Honor direct user stops
and corrections; relay material scope/target changes to the orchestrator and
reconcile affected dependencies before conflicting work continues. The
orchestrator is the normal coordination point, not a barrier to user authority.

Return selected source references and, for a spec, its identity and revision;
verified outcomes and outstanding scope; PR URLs when applicable and exact HEAD/base;
task-closing references and their body/provider verification, including any pending
stack activation; checks and
required CI state; worker/worktree/branch identities, preserved dirty content,
blockers and the next bounded action when work remains. Finish mutation before
returning completion. The orchestrator verifies current facts without asking for
another ritual receipt or a replay of the worker's investigation.
Keep each result bound to its repository, branch/PR and full commits even after
the worker's checkout moves to another assignment.

## Serial reuse and concurrent work

Prefer the same worker and worktree for compatible serial assignments in the
same repository. On every reassignment, update the existing worker's title to
the current bounded assignment using the title format above, including repair
and integration work. Verify the rename when supported; unavailable title
updates do not block execution or justify a replacement worker.

Before switching branches, finish the previous assignment,
preserve its commits and PR reference, and stop its branch-dependent processes.
Resolve dirty content without discarding it or carrying it into another
assignment; if safe reuse is unavailable, use another isolated worker/worktree.
Reconcile any existing writer or checkout of the target branch before switching;
never force a switch around conflicting ownership. The worker verifies the
assigned branch, base and full HEAD before editing. Reuse changes the branch,
not the task's worktree binding.

For a serial stack, create each child branch from the exact validated parent
commit under [integration.md](integration.md). Earlier branches and PRs remain
available when the worker moves to a child. Returning to an earlier PR for a fix
is another serial assignment; preserve the current work first and reconcile
affected descendants after the parent changes.

Concurrent assignments require distinct workers and worktrees with one writer
per branch/PR. A reused worker never handles two active assignments at once.
Leave completed App tasks visible and unarchived.

## Recovery

Wait for results or meaningful changes, not repeated generic status updates.
If setup or publication has an uncertain effect, inspect the existing task or
PR/branch evidence before retrying. Never infer failure from a missing reply or
create a duplicate worker/PR while the earlier effect remains unresolved.

Before replacement, confirm the old worker stopped and cannot race the new one;
preserve commits and dirty content, reconcile outstanding writes, and verify
the replacement's exact target. Unknown liveness blocks replacement. Preserve
worktrees by default; do not clean, reset or delete user work to simplify recovery.

On interruption, preserve the assignment/result context above and identify pending
submissions, uncertain effects and active/stopped/unknown worker liveness. Resume
from that handoff plus current Git/PR state.
Reuse an attributable stopped worker/result when safe; never repeat completed
work solely to reconstruct narrative or renew authority.
