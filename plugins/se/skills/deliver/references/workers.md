# Delivery workers

Read before worker creation or assignment; use Recovery only when interrupted,
resuming, or replacing a worker. The shared
[runtime surface](../../../references/codex-runtime-surface.md) owns classification.

## Transport and setup

On the App, use a visible task in the exact matching saved repository project
and an isolated worktree. On CLI, use a native subagent with an isolated worktree.
An unresolved surface or unavailable required transport/target blocks affected
work. Do not substitute the other surface, an external process, or implementation
in the orchestrator. Apply the entrypoint's invocation authority for worker
creation; implicit invocation needs no separate permission prompt. Higher-priority
runtime restrictions still apply. Never create a replacement coordinator.

Workers default to `gpt-5.6-luna` with `max` reasoning; explicit user overrides
win. Request those settings, but do not gate editing on effective-model telemetry
or claim that requested settings were independently observed. A concise worker
title such as `🚚 <repository> · <scope>` is metadata, not target identity.

Create with the complete initial assignment, not a bootstrap followed by a second
permission message. Pending worktree setup must finish before mutation; the
worker verifies the actual repository/remote, worktree, branch, base and full
starting HEAD against its assignment. Never overwrite dirty content or reuse
an incidental checkout to make the target fit. Resolve a mismatch before editing.
A creation receipt establishes a known creation effect, not a verified checkout.

## Assignment and result

Include the selected outcome and constraints, exact repository and intended
worktree/branch/base, prerequisite commits, relevant source contracts, validation,
publication authority and justified closing references. Where the runtime
allocates the worktree path, the worker reports the resolved path after verifying
the intended project and isolated checkout. Give only needed context, not the
full orchestration conversation. Carry the entrypoint's G preflight and
[hosted-content safety](../../../references/hosted-content-safety.md) obligations.

The worker owns implementation, self-inspection, tests, PR publication/readiness
and required CI for its branch within that assignment. It loads Implement, then
the applicable G workflows; it does not inherit Deliver Features' developer role,
independent-review gate, phase handoffs or claims. CI fixes remain within the
original outcome and are revalidated and published by the same worker.

Workers cannot create further agents, broaden scope, mutate another worker's
branch/PR, merge, deploy or perform production actions. Honor direct user stops
and corrections; relay material scope/target changes to the orchestrator and
reconcile affected dependencies before conflicting work continues. The
orchestrator is the normal coordination point, not a barrier to user authority.

Return the PR URL and exact HEAD/base, checks performed, required CI state,
remaining blockers and preserved dirty changes/worktree. Finish mutation before
returning completion. The orchestrator verifies current facts without asking for
another ritual receipt or a replay of the worker's investigation.

Reuse a worker for compatible sequential assignments only after the previous
assignment has ended and its work is understood and preserved. Verify the next
branch/base before mutation. Leave completed App tasks visible and unarchived.

## Recovery

Wait for results or meaningful changes, not repeated generic status updates.
If setup or publication has an uncertain effect, inspect the existing task or
PR/branch evidence before retrying. Never infer failure from a missing reply or
create a duplicate worker/PR while the earlier effect remains unresolved.

Before replacement, confirm the old worker stopped and cannot race the new one;
preserve commits and dirty content, reconcile outstanding writes, and verify
the replacement's exact target. Unknown liveness blocks replacement. Preserve
worktrees by default; do not clean, reset or delete user work to simplify recovery.

On interruption, report selected outcomes, worker/worktree/branch identities,
exact HEAD/base and PRs, validation/CI evidence, pending submissions, blockers
and the next bounded action. Resume from that handoff plus current Git/PR state.
Reuse an attributable stopped worker/result when safe; never repeat completed
work solely to reconstruct narrative or renew authority.
