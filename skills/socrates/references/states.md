# Socrates State Contract

This file owns Socrates workflow nodes, transitions, and field meanings.

Socrates persists no learner or workflow state. Workflow position, counters,
offer suppression, exercise selection, scaffolding, and assessments exist only
in the current conversation. Repository contents, diffs, test results, logs,
documentation, and explicit user replies are external evidence rather than
Socrates-owned state.

## Field-qualified states

| Owner | Allowed values | Class and lifetime | Meaning |
| --- | --- | --- | --- |
| `activation_source` | `explicit`, `implicit` | Derived run fact; transient | Distinguishes a user-requested exercise from a post-work candidate. |
| `offer_gate` | `open`, `suppressed-after-decline`, `suppressed-after-limit`, `suppressed-by-user` | Conversation control; transient | Controls implicit offers only. An explicit exercise request may start a new run despite suppression. |
| `evidence_status` | `ready`, `stale`, `conflicting`, `insufficient` | Derived evidence fact; transient | Records whether the selected anchor can support a fair assessment. |
| `exercise_pattern` | `predict-observe-reflect`, `design-compare`, `trace-path`, `debug-scenario`, `teach-back`, `retrieve-transfer` | Selected run field; transient | Chooses the exercise shape defined in `exercises.md`. |
| `scaffold_level` | `exact-anchor`, `area-anchor`, `self-locate` | Selected run field; transient | Controls how specifically the learner is directed to relevant evidence without revealing the answer. |
| `answer_assessment` | `accurate`, `partially-accurate`, `incorrect`, `stuck`, `uncheckable` | Derived response fact; transient | Describes only the learner's expressed answer relative to current evidence. |
| `allow_implicit_invocation` | `true` | Persisted skill metadata | Lets Socrates consider a post-work offer; it does not authorize starting an exercise without consent. |

The current objective, evidence anchors, learner response, offered milestone,
and `completed_exercise_count` are transient run data rather than additional
configuration or enum states. Keep the count in the inclusive range `0..2`.

## Terminal effects

| Terminal node | Counter effect | Offer-gate effect |
| --- | --- | --- |
| `skipped` | None | Preserve the current gate. |
| `declined` | None | Set `suppressed-after-decline`. |
| `complete` | Increment `completed_exercise_count`; cap at 2. | Set `suppressed-after-limit` when the count reaches 2; otherwise preserve the current gate. |
| `stopped` | None | Set `suppressed-by-user`. |
| `blocked` | None | Do not implicitly repeat the same topic; preserve the broader gate. |

Terminal nodes end the current exercise. A later explicit request begins a new
run at `qualify`; it does not mutate the prior terminal node.

## Evidence ownership

- Source files, diffs, tests, logs, and documentation are external evidence.
  Their existence is not proof that they are current or mutually consistent.
- Consent, decline, stop, skip, and answers come from explicit user turns. Do
  not infer them from silence, sentiment, or an earlier unrelated request.
- Socrates owns only its transient interpretation of that evidence. It never
  persists a learner model, schedule, score, milestone ledger, or mastery
  claim.

## Transitions

| node_id | kind | entry condition | transitions | terminal state |
| --- | --- | --- | --- | --- |
| `qualify` | decision | Socrates was explicitly requested or a possible post-work opportunity exists | `offer`, `prepare`, `skipped` | none |
| `offer` | output | An eligible implicit opportunity exists and the offer gate is open | `await-consent` | none |
| `await-consent` | wait | One consent question was emitted | `offer`, `prepare`, `declined`, `stopped` | none |
| `prepare` | action | Consent exists | `prompt`, `blocked`, `stopped` | none |
| `prompt` | output | One objective, exercise pattern, and trustworthy evidence anchor are ready | `await-answer` | none |
| `await-answer` | wait | One learning question was emitted | `evaluate`, `stopped` | none |
| `evaluate` | validation | The learner answered or requested help or the answer | `coach`, `reconcile` | none |
| `coach` | action | The response was checked against current evidence | `prompt`, `prepare`, `complete`, `stopped` | none |
| `reconcile` | recovery | Evidence is stale, conflicting, or insufficient for the attempted assessment | `evaluate`, `prepare`, `blocked`, `stopped` | none |
| `skipped` | terminal | The opportunity was ineligible, duplicated, or suppressed | none | `skipped` |
| `declined` | terminal | The learner declined an implicit offer | none | `declined` |
| `complete` | terminal | The objective closed or the requested direct answer was supplied | none | `complete` |
| `stopped` | terminal | The learner skipped, stopped, or changed objectives | none | `stopped` |
| `blocked` | terminal | No trustworthy evidence-backed exercise can be formed | none | `blocked` |
