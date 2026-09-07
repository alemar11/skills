# Dependencies and PR integration

Read only when units have prerequisites, a stack or cross-repository integration,
or when parent/base changes affect existing work. The orchestrator owns topology;
workers own their assigned branches.

## Grouping and prerequisites

Group coupled steps into useful PRs; independent contributions can run in parallel.
Verify prerequisite behavior in the intended base or an exact validated candidate
before dependent work consumes it. A closed issue, completed task or planning
order is not prerequisite proof. Unselected missing prerequisites block affected
work without authorizing implementation. Explicit merged/deployed requirements
still require observed evidence and separately authorized actions.

For cross-repository work, identify the consumed contract and exact commit
combination, make prerequisite artifacts available, and validate combined behavior.
A branch in another repository cannot supply a Git base. Individual passing tests
do not prove an assembled outcome; task subsets never imply a whole spec completed.

## Stacks and parent changes

The orchestrator may choose standalone or stacked PRs. For a stack, identify each
actual parent branch and full commit, PR base and landing order. Use G's stack
workflow only after establishing that it supports the intended topology; do not
invent dependencies or create branches to probe capability. Each child has its
own worktree and branch, and consumes the known parent candidate.

Parent changes invalidate affected child validation. Stop affected writers before
operations that rewrite their branches; assign one actor the bounded operation,
then update descendants in dependency order and rerun invalidated checks. Verify
actual ancestry, PR bases and current HEADs after publication. Do not allow a
compound stack operation to push another worker's unvalidated changes.

When changes interact, verify the selected assembled outcome at the current
commit combination before reporting delivery. No mandatory independent review is
introduced by stacking. Partial/draft/pending contributions remain incomplete;
ready stacked PRs do not mean their parents have merged.
