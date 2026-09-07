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

The spec's identity is its owner repository plus `spec_id`. Titles, list
positions, local paths, and hosted issue numbers are not substitutes. Use exact
saved artifact references when referring to another spec; do not resolve an
external prerequisite by a bare title or ID.

Acceptance criteria retain the external bracketed `F-AC-NN` spelling. They are
contract identifiers, not checkboxes or execution progress. Renaming or
reordering a criterion preserves its identity. New criteria allocate above the
highest active or retired criterion number, starting at 01 for a new spec.
Semantic replacement records the retired ID in a compact revision note; never
reuse it. Keep source links beside the decisions or claims they support rather
than maintaining a duplicate source registry.

One saved destination is authoritative. On GitHub, the parent body owns the
spec, acceptance criteria, task membership, and recommended order. Each linked
child body owns its task contract, including repository scope, acceptance links,
and prerequisites. In a Markdown save, the single file contains these same
authorities in its main spec and task sections. Native dependency edges project
task prerequisites; they never define additional requirements.

Revision and export rules live in [existing-specs.md](existing-specs.md).
Planning never overwrites executor-owned progress or claims implementation
completion from a drafted task list.

Delivery owns the separate execution section under
[progress.md](../../deliver-features/references/progress.md). That section and
provider status are excluded from semantic contract identity and do not advance
`spec_revision`; all requirements, decisions and task contracts remain included.
The [delivery-authorization marker](delivery-authorization.md) is also excluded:
it records permission for pickup, not requirements or execution progress. Its
exact GitHub and Markdown representations have that reference as their sole owner.

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
| `checks` | Each check pairs an observable completion condition with its test or observation; include per-repository and assembled integration evidence where needed. |
| `blocked_by` | Other task IDs in this spec that supply real prerequisites, each with the required outcome or evidence. |
| `external_prerequisites` | Exact external artifact references and required evidence, or none. They never expand implementation selection. |

The parent task index is an ordered list of task IDs, titles, and detail links.
It owns membership and recommended order; task details own all other task
fields. Do not duplicate repository assignments, acceptance links, or dependency
descriptions in the index. Read every task to establish coverage and the full
dependency graph. Task titles in the index mirror their details.

A stable task identity is the qualified spec identity plus `task_id`; display
position may change independently. All local dependency targets must exist and
the graph must be acyclic. Retain retired IDs in a compact revision note.

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
return through Grilling Session before saving a ready spec.

Distinguish binding decisions from implementation suggestions. Binding
decisions are part of the spec contract; suggestions are optional approaches
that an implementer may replace while preserving outcomes and constraints.
Never turn a source's proposed solution into an accepted requirement without
supporting authority. Do not fill a template by inventing decisions.

Use precise interfaces or a compact schema/state example when prose would lose
an accepted contract. Relevant repository-relative paths may cite current
evidence; they are not an exhaustive edit list. Leave incidental helpers,
commands, worker assignment, and Git operations to implementation.

Every F-AC pairs observable success with a credible verification method. Add
current-behavior evidence when it affects scope, regression preservation,
migration, feasibility, or verification; do not require a baseline field on
every criterion. Label an unverified material baseline as unknown and investigate
it when a decision depends on it. Never invent failure evidence or confuse a
completed preparatory task with the requested feature outcome. Separate
preservation obligations from new behavior.

Prefer an existing verification boundary that exercises the relevant external
behavior. Propose a new boundary only with a concrete adequacy reason. Review
the feature-level outcome as well as individual task checks: task completion
alone never proves the whole feature works.

## Rendering

Templates are presentation guides, not text to publish verbatim. Omit empty
optional sections and authoring instructions. Keep required task metadata and
explicit `none` prerequisites so missing information is distinguishable from
no dependency. GitHub uses standalone task bodies; Markdown embeds task sections
with stable anchors and headings nested under the main spec. Output references
own those destination details.
