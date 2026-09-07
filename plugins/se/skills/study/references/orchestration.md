# Study Orchestration

Read this reference after Grilling Session returns `refined` or `user-stopped`. It owns
the shared subagent selection, assignment, setup, monitoring, synthesis, and
failure policy for both Study surfaces. Surface references own only controller
placement and the subagent's surface-specific working context.

## Capacity selection

Record these facts before creating any worker:

- `original_requested_count`: the user's explicit number or `unspecified`;
- `planned_worker_count`: the count after applying the absolute five-worker
  cap;
- `created_worker_count`: the number of reserved slots with stable created
  identities;
- `full_capacity_mode`: `yes` exactly when the planned count is five;
- `full_capacity_source`: why five was selected, or `not-applicable`.

Explicit counts take precedence over efficiency. Honor zero through five
exactly. Normalize any larger request to five, disclose the cap before
creation, and retain both counts in the report.

For `original_requested_count=unspecified`, choose the smallest count that
keeps the controller efficient and gives every subagent a substantial,
distinct evidence surface:

- zero for a focused question or any investigation the controller can inspect
  directly without substantial context noise;
- one only when a single large or noisy evidence surface benefits materially
  from context isolation;
- two for two genuinely independent repositories, source families, or
  investigation surfaces;
- three for a genuinely multi-dimensional comparison, such as local contract,
  external subject, and comparative fit;
- four or five only for broad work with four or five independent tracks, such
  as runtime, architecture, maintenance, validation, and user or security
  concerns.

Prefer the lower count when evidence is borderline. Do not add workers merely
to reduce latency or duplicate the same review. A plan of five requires an
explicit report justification.

## Assignment contract

Before assigning workers, read the shared
[`evidence-researcher`](../../../references/subagents.md#evidence-researcher)
role. It owns the worker's purpose, read-only boundary, model settings, and
evidence memo; Study owns the refined assignment, slot lifecycle, and synthesis.

Reserve every planned slot before creation and number it once from 1 through
5. Each worker assignment must include:

- one bounded objective and its relation to the refined handoff;
- included evidence surfaces and explicit non-goals;
- concrete questions to answer;
- repository paths or source families to inspect;
- evidence and acceptance expectations;
- dependencies on other assignments, if any;
- a concise Markdown memo shape;
- the selected research role, read-only boundary, and slot number;
- an absolute prohibition on invoking Study or creating child workers.

Assignments should be mutually distinct and collectively sufficient. Serialize
only those that truly depend on an earlier unstable finding. Workers report to
the active Study controller, not directly to another worker.

## Native subagent setup

For each positive planned slot, create one native subagent under the active
Study controller:

- Request the shared `evidence-researcher` profile explicitly.
- Keep the assignment in the controller's working-directory context.
- Supply the slot number, refined handoff slice, read-only boundary, evidence
  expectations, concise Markdown memo shape, and recursion prohibition.
- Record the stable subagent identity and parent lineage returned by the
  runtime. A label or assignment text is never identity.

Use only native subagents. If that transport is unavailable, a creation request
fails, or setup remains unresolved, retain the reserved slot and its failure.
Do not create a visible App worker task, start an external process, or switch
transport. Never create a replacement beyond the reserved slot.

## Setup and no-replacement policy

Set `worker_transport` to `subagent` for every positive plan. Study never
creates visible App worker tasks. One reserved slot permits at most one
creation request unless authoritative reconciliation
proves that the request had no effect and the same slot can safely complete
its original attempt.

For each slot:

1. Treat the immediate result as setup evidence, not proof beyond what it
   actually establishes.
2. Bind the slot only to a stable worker identity. Never correlate by title,
   label, prompt preview, assignment text, or timing.
3. A definitive failure proving no worker exists sets `creation-failed` and
   permits later reserved slots to proceed.
4. An uncertain effect sets `pending-setup`. Reconcile it through at most three
   bounded authoritative observations. Stop later creation until it resolves.
5. A stable subagent outside the active controller lineage sets
   `structural-verification-failed`; observed drift from the requested role profile sets
   `settings-drift`. Preserve the identity, create no replacement, and stop
   later creation.
6. Failed reconciliation sets `unresolved-setup`; leave later slots
   `not-started` with reason `creation-halted-after-uncertain-slot`.

A failed, drifted, unresolved, or abandoned slot is never freed, renumbered,
or replaced. Never start a second controller, visible worker task, external
worker process, or second subagent layer to make up capacity.

If a positive planned transport is unavailable before any creation request,
mark every reserved slot `creation-failed` with the shared transport blocker.
The controller may still complete direct analysis, but the overall outcome is
at most `partial`.

## Monitoring and evidence

Monitor all stable workers with bounded waits and authoritative observations;
do not busy-poll. Track progress and inspection positions separately when the
runtime exposes both, and deduplicate events by stable revision or event
identity rather than prose.

`needs-attention` and `monitoring-unavailable` are nonterminal. Preserve the
reason and last known state, surface the blocker to the owning user when human
input is possible, and resume only after authoritative observation recovers.
Only the user may direct abandonment of a worker that needs attention.

Do not finish merely because one worker completes. For every stable identity,
capture a final memo or the best available terminal state, reason, error, and
last evidence. Missing evidence is unavailable, never implicit success.

## Synthesis and outcome

The controller owns the final reasoning. It must compare worker claims against
the refined handoff and inspected evidence, resolve contradictions where
possible, and label remaining uncertainty. Worker memos are inputs, not
authority.

Use these overall outcomes:

- `completed`: the controller produced a usable synthesis and every planned
  slot completed with captured terminal evidence; a zero-worker plan may
  complete through controller analysis alone.
- `partial`: the controller produced a usable synthesis, but at least one
  planned slot failed, drifted, remained unresolved, was abandoned, or lacked
  terminal evidence.
- `failed`: no usable synthesis can be returned, including a blocked Grilling Session
  phase or failed App controller setup.

Read [output-template.md](output-template.md) immediately before reporting and
include only the controller section selected by `study_surface` plus the
shared subagent ledger.
