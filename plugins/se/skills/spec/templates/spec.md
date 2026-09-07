# <Feature title>

- spec_id: <stable lower-kebab identity>
- spec_revision: <positive integer>
- owner_repository: <verified repository identity>
- repositories: <affected repository identities>
- source_refs: <relevant sources>
- acceptance_high_water: <highest allocated F-AC number>

## Problem and outcome

<Affected actors, current problem, and the observable result.>

## Scope and non-goals

<Included behavior and explicit exclusions.>

## Behavior and constraints

<Expected behavior, important failure cases, compatibility, and invariants.>

## Decisions and evidence

<Accepted decisions, rationale, and sources; distinguish implementation
suggestions and explicit assumptions from binding decisions.>

## Acceptance criteria

- [F-AC-01] <observable success criterion>
  - baseline: <observed current behavior with evidence, or unknown>
  - verification: <observation or test boundary that demonstrates success>

## Tasks

| Order | task_id | Title | Repositories | F-AC refs | Blocked by / required evidence | External prerequisites | Details |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | <stable-task-id> | <outcome> | <repositories> | <F-AC IDs> | <task IDs and prerequisite outcomes, or none> | <exact references and evidence, or none> | <stable local anchor or verified task issue> |

Order is recommended; blockers are hard prerequisites. Every row has a complete
detailed task contract. For a single-file save or complete preview, repeat the
following anchor and the contents of task.md for each task:

<a id="task-<task_id>"></a>

<Task details. GitHub child bodies replace these inline detail sections only
after every child has been saved and read back.>

## Risks and open questions

<Only relevant risks and non-blocking unknowns; material unresolved decisions
prevent the spec from being ready to save.>
