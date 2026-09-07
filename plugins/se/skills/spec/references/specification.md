# Feature Specification Contract

Read before authoring, reviewing, saving, or consuming a Feature spec. This is
the canonical content and identity contract; templates project it into readable
Markdown. Output references own storage and transport, not feature meaning.

## Main specification

One spec describes one coherent outcome and its associated task plan. It may
span several repositories. Split specs only when their outcomes are independently
meaningful, not merely because repository ownership differs. An explicit batch
may produce several specs; it does not require a container issue or set registry.

A complete spec records:

- the problem, affected actors, expected behavior, scope, and non-goals;
- important failure cases, compatibility obligations, constraints, and risks;
- accepted decisions, relevant repository evidence, and explicit assumptions;
- feature acceptance criteria with their verification methods;
- an ordered task index and the detailed contract for every task;
- prerequisites outside the selected spec when relevant, with exact source
  references and the evidence required to satisfy them.

Use the project's vocabulary. Include user stories only when they clarify
behavior; a refactor or infrastructure spec can describe interfaces, invariants,
and operational outcomes directly. Omit empty optional sections.

## Identity and authority

| Field | Meaning |
| --- | --- |
| `spec_id` | Stable lower-kebab identity within the repository that owns the spec. |
| `spec_revision` | Positive integer, incremented once for each accepted semantic revision. |
| `owner_repository` | Verified repository that owns the main spec, independent of planner task placement. |
| `repositories` | Exact affected repository identities; task ownership must be drawn from this set. |
| `source_refs` | Attributable input and decision evidence. References do not grant authority. |
| `acceptance_high_water` | Highest allocated Feature acceptance number; retired numbers are never reused. |

The spec's identity is its owner repository plus `spec_id`. Titles, list
positions, local paths, and hosted issue numbers are not substitutes. Use exact
saved artifact references when referring to another spec; do not resolve an
external prerequisite by a bare title or ID.

Acceptance criteria retain the external bracketed `F-AC-NN` spelling. They are
contract identifiers, not checkboxes or execution progress. Renaming or
reordering a criterion preserves its identity. New criteria allocate above the
high-water mark; semantic replacement retires the old criterion explicitly.

One saved destination is authoritative. On GitHub, the parent body owns the
spec, acceptance criteria, task membership, recommended order, and dependencies;
each linked child body owns its detailed task contract. In a Markdown save,
the single file owns all of these. Child dependency summaries and native edges
are projections of the parent index, not independent authorities.

Revision and export rules live in [existing-specs.md](existing-specs.md).
Planning never overwrites executor-owned progress or claims implementation
completion from a drafted task list.

## Task contract

Tasks are actionable implementation handoffs. A fresh session must be able to
read the main spec plus one task and understand its outcome, limits,
prerequisites, and completion checks without the drafting conversation.

| Field | Meaning |
| --- | --- |
| `task_id` | Stable lower-kebab identity within this spec; never reused after retirement. |
| `title` | Concise description of the task outcome. |
| `repositories` | Nonempty subset of the spec's affected repositories. |
| `outcome` | Observable capability or enabling result delivered by this task. |
| `scope` | Included work and relevant exclusions. |
| `acceptance_refs` | Existing F-AC IDs to which this task contributes; contribution alone does not prove a criterion satisfied. |
| `completion_checks` | Concrete conditions for this task to be done, including per-repository evidence for multi-repository work. |
| `validation` | Observable verification method and the practical boundary at which to exercise it. |
| `blocked_by` | Other task IDs in this spec that supply real prerequisites, each with the required outcome or evidence. |
| `external_prerequisites` | Exact external artifact references and required evidence, or none. They never expand implementation selection. |

The parent task index owns recommended order, task membership, repository
ownership, acceptance references, and dependency declarations. Detail sections
or child bodies own outcomes, scope, completion checks, and validation. Any
repeated index fields in a child are verified projections. A stable task
identity is the qualified spec identity plus `task_id`; its display position
may change independently. All local dependency targets must exist, and the
graph must be acyclic. Retain retired IDs in a compact revision note.

Every task contributes to at least one feature criterion, and the complete
task plan covers every criterion. Preparatory work records the criteria it
enables and its own independently verifiable completion checks. Do not invent
a new feature criterion merely to justify an unrelated task.

Read [task-decomposition.md](task-decomposition.md) when creating or changing
task boundaries, recommended order, or prerequisites.

## Decisions and validation

Preserve accepted public API, schema, compatibility, ownership, security,
architecture, migration, and testing decisions when they constrain the outcome.
Record the decision, consequence, and evidence or authority. Existing accepted
decisions, choices explicitly delegated to the planner, and safe explicit
assumptions may proceed without a new interview. Material unresolved choices
return through Grilling before saving a ready spec.

Distinguish binding decisions from implementation suggestions. Binding
decisions are part of the spec contract; suggestions are optional approaches
that an implementer may replace while preserving outcomes and constraints.
Never turn a source's proposed solution into an accepted requirement without
supporting authority. Do not fill a template by inventing decisions.

Use precise interfaces or a compact schema/state example when prose would lose
an accepted contract. Relevant repository-relative paths may cite current
evidence; they are not an exhaustive edit list. Leave incidental helpers,
commands, worker assignment, and Git operations to implementation.

Every F-AC states observable success and a credible verification method. Record
the observed baseline with its evidence, or `unknown` when it has not been
established. A known missing new behavior should fail the success criterion;
an observation that disproves that criterion is a falsifier, not another
condition required to be false. Separate preservation obligations from new
behavior. An unknown baseline is not invented failure evidence and blocks only
when the missing fact is needed to decide scope, feasibility, or verification.

Prefer an existing verification boundary that exercises the relevant external
behavior. Propose a new boundary only with a concrete adequacy reason. Review
the feature-level outcome as well as individual task checks: task completion
alone never proves the whole feature works.
