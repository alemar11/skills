# Delivery Closeout

Read at Intake to capture measurements and before every terminal report.
The coordinator always closes out this invocation: successful delivery, partial
or blocked work, pre-acquisition failure, and explicit stop. Use the current
run as evidence about Delivery and the skills it invoked. Do not monitor other
tasks or invoke a separate audit workflow.

## Evidence and measurements

At Intake, record the observed start time and any available run-scoped usage
baseline. Collect material decisions, waits, retries, repairs and handoff results
from ordinary execution evidence; do not create a second ledger or duplicate
transcripts. Preserve timestamps and execution identities across resume.

Report elapsed wall-clock duration from invocation start through the closeout
measurement cutoff, with timestamps and coverage. Include waiting; separate
active work and waiting only when observed. For resumed delivery, distinguish
this invocation from prior attempts and label whether any cumulative span
includes gaps. Never sum concurrent worker durations into elapsed run time.
If the start is missing, report the known interval as partial or duration as
unavailable; do not infer an exact duration from message order.

Report token usage only from attributable runtime telemetry. Identify the
source, cutoff and coverage: coordinator, each included worker, prior attempts,
and any closeout helper. Use observed input/output counts when available and
the provider's definitions. Sum only disjoint usage: a parent aggregate may
already include children, and cached input or reasoning can be subsets of other
counts. Unknown inclusion rules prevent a trustworthy grand total; report
separate observations instead. Missing usage is unavailable, never zero.
Account-wide limits, model settings and self-reported estimates are not run
token counts. Do not reconstruct tokens from transcript length or silently
omit unavailable worker or hosted-review usage from a claimed complete total.
State when current-turn/final-answer usage has not yet been metered.

Use already available evidence and at most a targeted read for missing facts
that materially affect the report. Do not repeatedly poll telemetry, scan
unrelated histories, or replay work to fill measurement gaps.

## Final report

Return two clearly separated parts in the calling task. Keep detail proportional
to the run, with links to evidence instead of copied logs.

**Delivery results:** state complete, deferred or blocked and the selected scope.
Report verified outcomes and task-to-PR mapping, exact repository/base/HEAD
vector, validation, independent local review, explicit hosted acceptance and
required CI, progress updates, repair counts, remaining tasks and merge/closure
actions. Include exact release evidence or retained ownership/uncertainty and
the actionable resume handoff for pauses. Show duration and token usage with
their coverage and limitations. An empty or stopped run still reports what
actually occurred; ready PRs and partial work do not imply the whole spec landed.

**Workflow audit:** cover what worked, what went wrong, and what could improve
in Delivery or its invoked skills. If a category has no supported observation,
say so; do not invent defects or wins to fill it. Keep project implementation
defects in delivery results unless they reveal a reusable workflow weakness.

For each worthwhile improvement, connect:

- The observed event or evidence gap and its effect on this run.
- The general mechanism and owning skill/reference, distinguishing instruction
  gaps from execution mistakes, provider limitations and missing visibility.
- A concrete reusable change, its applicability conditions, and the expected
  effect on speed, resilience or token use, including material tradeoffs.
- Confidence and a representative future check that could validate the proposal.

Prioritize a few high-value changes. A recommendation must remain useful after
removing this project's names, paths, stack and incident-specific workaround.
When evidence suggests only a hypothesis, label it and its validation needs;
one occurrence does not prove a global defect or measurable savings. Report
observed failures even when no transferable recommendation is justified.
Do not weaken acceptance, review or safety gates merely to improve throughput.

## Ownership and bounded analysis

Perform safe release before retrospective analysis. Closeout preserves the
pending delivery outcome; missing metrics or limited retrospective evidence do
not invalidate otherwise verified delivery, hide blockers, or retain claims.
On explicit stop or unresolved actor/release safety, provide a concise report
from existing evidence without starting more work.

The coordinator normally synthesizes the audit itself. When an independent
analysis would materially improve it, it may use one bounded read-only
[`evidence-researcher`](../../../references/subagents.md) after verified safe
release, or when no claim was acquired and no actor safety issue exists. Supply
only relevant captured run evidence and the invoked skill contracts, a small
question set, and a time budget. No implementation, hosted operations, claim
access, recursive delegation or separate visible task. Stop the helper at the
budget and use available evidence if it cannot finish; do not retry it just to
fill the report. Account for its available usage. The coordinator evaluates
generalizability and owns the final report; this helper is not code review and
does not alter any callee's subagent policy.

The audit proposes maintenance; it does not modify skills, install or refresh
plugins, save durable knowledge, create tickets, or publish the report elsewhere.
Those actions require a separate request. Keep recommendations in the calling
task, outside saved spec semantics and execution-progress projections.
