# Dependencies and PR integration

Read when contributions need combining, units have prerequisites, a stack or
cross-repository integration, or parent/base changes affect existing work.
The orchestrator owns topology and acceptance; workers perform integration and
validation in their assigned branches.

## Grouping and prerequisites

Group coupled steps into useful PRs; independent contributions can run in parallel.
Choose separate PRs for independent outcomes, stacks for actual branch dependencies,
or contribution branches feeding one integration PR for a coupled outcome.
Sequential landing alone does not imply stacked PRs. Name the integration target
and assigned writer before dispatching contributions that need combining.
Verify prerequisite behavior in the intended base or an exact validated candidate
before dependent work consumes it. A closed issue, completed task or planning
order is not prerequisite proof. Unselected missing prerequisites block affected
work without authorizing implementation. Explicit merged/deployed requirements
still require observed evidence and separately authorized actions.

For cross-repository work, identify the consumed contract and exact commit
combination, make prerequisite artifacts available, and validate combined behavior.
A branch in another repository cannot supply a Git base. Individual passing tests
do not prove an assembled outcome; task subsets never imply a whole spec completed.

## Integration assignment

Assign integration to a regular worker; it is an assignment, not a separate
permanent role. Reuse a finished worker/worktree when safe under
[workers.md](workers.md#serial-reuse-and-concurrent-work). Supply the target
repository, delivery branch/base, pinned validated contribution commits, source
contracts, combined acceptance checks and intended PR. Make those exact commits
available in the integration checkout before combining them.

The assigned worker integrates the pinned commits into its owned delivery branch,
resolves conflicts without dropping either contribution's requirements, and runs
the affected tests and assembled-outcome checks on the combined result. A clean
Git merge or separate green worker tests do not establish combined correctness.
Material requirement conflicts return to the orchestrator for resolution.

The worker publishes or updates the intended integration PR and completes required
CI and readiness under Deliver. Return source-to-result commit evidence with the
normal worker result; the orchestrator verifies contribution coverage and accepts
the combined outcome. Changed inputs invalidate affected integration evidence.

Do not mutate contribution branches owned by other workers, land PRs, or write
the repository's default/release branches as part of integration. If the target
is an existing PR branch, reconcile its writer before reassignment. Preserve
contribution branches and worktrees; integration does not authorize their cleanup.

## Task closure through integration and stacks

Apply the entrypoint's [task issue closure](../SKILL.md#task-issue-closure) rule
to the chosen landing path. An integration PR carries the closing references
for every task it completes, including tasks supplied as commit-only contributions.

Each stacked PR keeps its own task-closing lines even when its base is another
feature branch. A visible issue link is not proof that merging into that branch
will close the issue. Record the default-branch landing step: if PRs land
individually, recheck each child's closing references after retargeting; if one
PR lands the combined result, that PR must carry all completed task references.
Include this requirement in the merge handoff without performing an unauthorized
merge or changing topology solely to activate issue links. Pending default-branch
activation does not block an otherwise verified ready stack; missing closing
lines do.

## Stacks and parent changes

The orchestrator may choose standalone or stacked PRs. For a stack, identify each
actual parent branch and full commit, PR base and landing order. Use G's stack
workflow only after establishing that it supports the intended topology; do not
invent dependencies or create branches to probe capability. Each child has its
own branch and PR and consumes the known parent candidate. Serial children may
reuse their worker's worktree under [workers.md](workers.md#serial-reuse-and-concurrent-work);
concurrently active parent/child assignments require separate workers and worktrees.

Parent changes invalidate affected child validation. Stop affected writers before
operations that rewrite their branches; assign one actor the bounded operation,
then update descendants in dependency order and rerun invalidated checks. Verify
actual ancestry, PR bases and current HEADs after publication. Do not allow a
compound stack operation to push another worker's unvalidated changes.

When changes interact, verify the selected assembled outcome at the current
commit combination before reporting delivery. No mandatory independent review is
introduced by stacking. Partial/draft/pending contributions remain incomplete;
ready stacked PRs do not mean their parents have merged.
