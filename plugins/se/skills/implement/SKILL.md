---
name: implement
description: "Implement and validate selected local work or a bounded workflow assignment, without PR publication."
---

# Implement

Follow the shared [execution scope](../../references/execution-scope.md) for
standalone and composed invocation.

Implement exactly the selected spec, ticket, directly described work, or
caller-assigned repair batch. Read the main spec and detailed task contract when
provided; a spec is not required for a direct implementation or review fix.
Use `se:deliver-features` for explicitly requested reviewed delivery of saved
specs. Discussion of implementation does not itself select work.

## Assignment and execution

Standalone work uses the current repository and branch. A composed assignment
supplies the bounded contribution or selected findings, accepted requirements,
exact repository/worktree/branch/base and starting HEAD, relevant instructions,
and validation requirements. Verify the actual target before mutation; report
an unresolved mismatch to the owner. Preserve unrelated work and never add
unselected prerequisites or change requirements to make checks pass.

The executing task or developer subagent retains the caller-selected profile.
Implement never creates tasks or subagents and never operates claims, whether
standalone or composed. For review-driven work, read the
[shared repair budget](../../references/review-repair-budget.md), require the
owner's reserved batch, and preserve its identity/count; this skill cannot
reserve or reset a round. Standalone implementation outside a managed SE review
loop does not acquire a review budget merely because it fixes a bug.

Use test-driven development where practical, especially at pre-agreed seams.
Run checks covering the changed behavior and repository-required gates. Broaden
validation only for unresolved risks or failures.

## Review and handoff

Return the validated candidate to the caller. Independent review is a separate
workflow owned by the user or orchestrator; it is never launched by Implement.
Local checks and self-inspection do not satisfy a caller-required independent
review gate. This boundary is the same for standalone and composed work.

Commit only files required for the selected work to the verified target branch.
Return the committed HEAD and base, changed scope, validation evidence, worktree
state, any reserved batch identity/count, and blockers. Become quiescent before
handoff so the owner can review a stable candidate. Preserve unrelated dirty
work and disclose it; a composed caller may require a clean isolated lane.

This skill ends at local implementation. A separately authorized push,
publication, hosted review, merge, deployment, or issue action belongs to its
owning workflow after this handoff; authorization for that later phase does not
bypass the caller's review gate.
