---
name: idea
description: "Capture a conversation’s concrete proposal as an Idea when explicitly requested; publish by default or preview on request."
---

# Idea Capture

Follow the shared [execution scope](../../references/execution-scope.md) for
standalone and composed invocation.

## Purpose and boundary

Use `se:idea` only after an explicit request to capture, select, save, or
preview an Idea from the current session or supplied input. A capture or save
request defaults to the publish branch; preview is available only when
requested explicitly. The skill first builds a transient in-memory capture
bundle, then uses that same bundle for preview or verified hosted output. It
preserves a tentative proposal for later spec planning and then stops.

The workflow is:

`Idea -> Spec -> Delivery Features`

Idea capture does not write Feature specs, acceptance criteria, implementation
plans, execution graphs, project memory, architecture decisions, or code. It does
not create an application task, select a model profile, or delegate to another
task. Ordinary brainstorming must never create or prepare a durable Idea
implicitly.

## Workflow graph

Read the shared [workflow-graph.md](../../references/workflow-graph.md) for the
common graph vocabulary. Read
[workflow-contract.md](../../references/workflow-contract.md) for the Idea
hosted shape. Read [references/states.md](references/states.md) for the
human-readable distinction between workflow nodes, run fields, result values,
typed handoff state, and hosted domain state. The registry below is the
structural source of truth for Idea; Mermaid is its projection.

| node_id | kind | entry condition | transitions | side effects | terminal state |
| --- | --- | --- | --- | --- | --- |
| capture | action | explicit capture request and session or supplied input | normalize, blocked | transient | none |
| normalize | action | source evidence is available | clarify-select, reported, blocked | transient | none |
| clarify-select | decision | candidate set is normalized | freeze, deferred, blocked | none | none |
| freeze | action | selected candidates are complete locally | terminal-operation | transient | none |
| terminal-operation | decision | frozen bundle and default or explicit operation are resolved | preview, publish, blocked | none | none |
| preview | action | preview was explicitly requested | reported | none | none |
| publish | action | default or explicit publish and exact scope are resolved | preflight | transient | none |
| preflight | validation | publish branch is selected | hosted-checks, blocked | dependency-read | none |
| hosted-checks | validation | publication dependency is available | mutate, blocked | hosted-read | none |
| mutate | action | hosted operation is normalized | reconcile-verify | hosted-write | none |
| reconcile-verify | validation | hosted result may be ambiguous or partial | complete, blocked | hosted-read | none |
| reported | terminal | preview or no-candidate report is ready | none | none | reported |
| deferred | terminal | user selection or clarification is required | none | none | deferred |
| complete | terminal | hosted operations were verified | none | none | complete |
| blocked | terminal | required evidence, authority, dependency, or reconciliation is unavailable | none | none | blocked |

~~~mermaid
flowchart TD
    capture --> normalize
    capture --> blocked
    normalize --> clarify-select
    normalize --> reported
    normalize --> blocked
    clarify-select --> freeze
    clarify-select --> deferred
    clarify-select --> blocked
    freeze --> terminal-operation
    terminal-operation -->|explicit preview| preview
    terminal-operation -->|default or explicit publish| publish
    terminal-operation -->|publish selected but target or operation unresolved| blocked
    preview --> reported
    publish --> preflight
    preflight --> hosted-checks
    preflight --> blocked
    hosted-checks --> mutate
    hosted-checks --> blocked
    mutate --> reconcile-verify
    reconcile-verify --> complete
    reconcile-verify --> blocked
~~~

The in-memory bundle is run state, not durable project memory. It may contain
the selected source excerpts, normalized candidates, decisions, target
repositories, rendered bodies, preflight observations, publication order, and
verified results. Discard it after the terminal capture report unless the
hosted issue itself is the explicitly authorized durable output.

## Run contract

Resolve `run_mode` once after the local bundle is frozen. The only accepted
values are:

- `publish` (default): publish Ideas in the exact explicit request's scope and
  verify each hosted result;
- `preview`: calculate and report proposed Ideas without hosted mutations.

Resolve an explicit request to inspect, draft, preview, or avoid writes as
`preview`. Resolve an explicit request to save or create durable Ideas as
`publish`; an omitted mode also selects `publish`. Never silently downgrade a
publish request to preview because a dependency is missing. If the target or
operation is ambiguous, block the publish branch and report the exact missing
scope evidence.

The workflow contract in
[`../../references/workflow-contract.md`](../../references/workflow-contract.md)
owns the exact Idea hosted shape and metadata. Load it before resolving hosted
metadata; do not repair or redefine it during a run.

The shared [workflow-graph.md](../../references/workflow-graph.md) owns the
structural registry and terminal meanings. It does not replace the hosted Idea
contract above.

The shared
[hosted-content-safety.md](../../references/hosted-content-safety.md) is the
canonical owner for portable hosted content. Load it after the final Idea title
and body are rendered and apply its complete gate immediately before each
hosted write.

## Dependency boundary

Capture and preview remain local: do not load G or inspect hosted state. On the
publish branch, read [publishing.md](references/publishing.md) before any hosted
access. It owns dependency preflight, collision checks, mutation handoff, and
recovery; the explicit Idea request supplies only its resolved in-scope authority.

## Workflow

### 1. Resolve the source and repository

Use the current session or supplied input as source evidence. Resolve one exact
tracker-owning repository for every candidate from explicit user scope and
repository evidence. A task identity, saved project, filesystem location, or
display title is not repository ownership evidence.

For each candidate, keep a portable source description under the shared hosted
content safety contract. Keep Idea-specific source selection tentative and
relevant; do not redefine the common portability rules here.

### 2. Extract and normalize candidates

Identify only concrete proposals actually present in the session or supplied
input. For each candidate, derive:

- a concise human name and deterministic lower-kebab `idea_slug`;
- exactly one tracker-owning repository;
- the summary, problem or opportunity, proposed direction, expected value,
  known context and constraints, open questions, and portable source evidence.

Deduplicate by substantive intended outcome, not by title wording. Do not merge
proposals whose outcomes, owners, or planning boundaries materially differ.
Preserve tentative language and unknowns. Do not add goals, non-goals,
acceptance criteria, implementation scope, dependencies, readiness, or
planning conclusions.

Keep these facts in one transient capture bundle for the rest of the run:

- the portable source snapshot and its provenance;
- the normalized candidate set and selection decisions;
- the resolved tracker owner for each candidate;
- rendered bodies and intended publication order;
- duplicate, equivalence, collision, and metadata observations;
- preview refs or verified hosted results.

Do not persist this bundle as project memory or split it across unrelated
artifacts. Reconcile it after every user decision or hosted operation before
continuing.

If no concrete proposal exists, report that nothing was captured and stop.
Honor an explicitly selected set, including an unambiguous request to capture
all candidates, without another selection question. A single candidate under
explicit capture authority also needs no confirmation. Ask one focused
selection question only when multiple candidates leave the requested set
unresolved, then capture only that set. If one selected proposal
has a material gap in its problem, value, or direction, ask at most one
lightweight intake question; preserve any remaining non-blocking uncertainty
under `Open Questions`.

Read [`references/idea-template.md`](references/idea-template.md) when
rendering the canonical body. Keep its seven sections in order and do not add
planning sections.

### 3. Freeze the local accepted set

Complete the local capture bundle before choosing the terminal operation:

1. finalize every candidate's name, slug, body, owner, target, and intended
   metadata;
2. confirm that every candidate has exactly one tracker owner and portable
   source evidence;
3. derive its deterministic `proposed-idea:` ref for preview or retain the
   publication identity as unresolved until publish;
4. recheck all candidates after any user-directed rename, merge, or split.

After the local bundle is frozen, enter the terminal-operation decision. Do not
inspect hosted state or load the publication dependency before that decision.

Do not inspect hosted issues, native Issue Types, or current duplicate and
collision state in this phase. Those checks belong to the publish terminal
operation. Preview must report that hosted equivalence and collision evidence
was not consulted rather than claiming that no conflict exists.

### 4. Preview or publish

The terminal-operation node must resolve the run mode exactly once. For
run_mode=preview, which must have been explicitly requested, return the relevant
in-memory bundle contents: each
candidate's intended target, title, canonical body, metadata, publication
order, and deterministic `proposed-idea:` ref. Mark every proposed ref
non-durable. Do not load the G dependency preflight, read GitHub, request a
dry-run mutation, or perform any hosted operation.

For run_mode=publish, use [publishing.md](references/publishing.md) with the
frozen bundle. It owns the publication sequence and partial-failure recovery.
The hosted issue is durable; the bundle remains transient.

### 5. Report

Report every selected candidate as `created`, `reused`, `proposed`, `skipped`,
or `failed`, with its owner, name, and qualified durable or explicitly
non-durable ref. Report blockers and safe resume work precisely. Stop after
capture reporting.

## Spec handoff

When the user explicitly asks to continue a captured proposal into Spec
planning, render the transient [Idea Source Handoff](references/idea-source.md).
The handoff is a typed artifact, not an automatic invocation of Spec.

Keep the handoff tentative: preserve the proposal summary, problem or
opportunity, proposed direction, evidence, repository identity, and open
questions. Do not add Feature requirements, acceptance criteria, allowed paths,
execution units, dependency IDs, implementation plans, or readiness claims.
Spec Intake keeps source_route as new-source, reloads repository context, and
derives its own Feature spec fields.

## Independence

Do not import or modify other Idea implementations. This skill runs in the
invoking task; it creates no application task and selects no model profile.
