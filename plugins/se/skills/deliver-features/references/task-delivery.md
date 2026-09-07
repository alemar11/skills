# Task Delivery and PR Topology

Read before assigning implementation, choosing PR boundaries, or verifying
task coverage. Spec owns the saved
[specification contract](../../spec/references/specification.md); Delivery
owns how its tasks become reviewed changes.

## Selection and delivery units

Load each explicitly selected saved spec and all its task details. Accept an
authoritative GitHub bundle or Markdown file; an exported snapshot or older
unmigrated shape is not authoritative delivery input. A selection contains the
whole spec and its tasks. Explicit local implementation of a single task may
instead use Implement; never silently treat a partial selection as delivery of
the full spec. Read external prerequisites without adding them to the selection.

Freeze all affected implementation repositories before claiming them. A tracker
owner alone does not imply product-code changes in that repository. Map every
declared repository to an exact Git identity and local project before writing.

Choose the smallest useful set of delivery units. Each unit owns one spec,
one repository, one branch, and one PR, and records the task outcomes or
per-repository contributions it supplies. A unit can cover several related
tasks. A multi-repository task requires units in each contributing repository;
no single unit claims the whole task without all its completion evidence.

Assign a stable lower-kebab `delivery_unit_id` within the spec and retain its
exact coverage and identity in the handoff and task history. This is transient
execution evidence, never a new plan field or claim-registry column. Do not
reassign an ID to a different delta. Repartitioning work invalidates affected
review evidence and never resets the spec-wide revision budget.

Before assignment, account for every task and criterion across units or exact
already-incorporated evidence. Do not schedule overlapping contributions twice.
One PR per task or per spec is not mandatory. Every unit delta remains bounded
and reviewable, and its contribution is explicit in the PR body.

## Ready frontier

Use recommended task order to choose among ready work. Readiness requires the
actual `blocked_by` and external prerequisite outcomes, with their declared
evidence. A list position, closed issue, native edge, or completed agent turn
alone is insufficient. Native GitHub edges are diagnostic projections of the
spec's semantic graph.

A prerequisite may be available in the verified integration base or in a
current validated candidate that the dependent can actually consume. For a
cross-repository candidate, require its current published PR, exact HEAD, and
the contract/integration evidence needed by the dependent. Respect an explicit
merged or deployed prerequisite; delivery does not authorize those effects.
Missing external prerequisites block the dependent without expanding scope.

Applicable confirmed check failures block readiness unless G diagnosis proves
they are exclusively infrastructure or flaky and unrelated to correctness.
Pending checks do not by themselves unblock an otherwise unproved prerequisite.
Final delivery still requires every required validation and CI result.

Several tasks may execute sequentially inside one unit. Do not require a
separate PR for an internal prerequisite: verify its outcome before starting
the dependent contribution, and validate the final combined unit. A unit cannot
wait on a result it can only produce after that dependent work; resolve such
grouping cycles by regrouping before assignment.

Exclude already active unit contributions from the ready frontier. Prefer one
active lane per repository, reusing clean lanes for serial work. Additional
lanes require independent work and isolated worktrees. If only active lanes
remain, take the change-driven reconcile path rather than duplicating workers.

## Integration strategy

Planning edges never force a Git stack. Before a dependent mutation, choose
and verify how every prerequisite will be available:

- use the repository integration base when it already contains the required
  changes;
- combine tightly coupled tasks in one unit and validate the sequence;
- use a stack when one verified immediate parent contains all same-repository
  prerequisite HEADs and a separate PR remains useful;
- for independent fan-in, combine contributions in one unit before publication,
  or use an explicit integration arrangement with non-overlapping PR deltas and
  a verified final landing path. If existing published units cannot be combined
  safely, defer for the required integration or merge decision.

Choose routine local grouping autonomously within scope. Do not introduce a
semantic dependency between independent tasks, omit a prerequisite, duplicate
their changes in competing PRs, or perform an unauthorized merge to force
progress. Record any required human merge/rollout action before starting work
that depends on it. A spec permitting only assembled validation must have a
concrete validation target; provisional unit evidence is not final delivery.

Cross-repository dependencies never supply a Git base. For a stack, verify the
actual immediate parent branch and full HEAD through G. When prerequisite
changes are already in the integration base, start a new root rather than
targeting a merged or deleted branch. Parent or integration drift invalidates
affected ancestry, candidate receipts, and validation; restack or regroup and
revalidate the affected units before publication.
