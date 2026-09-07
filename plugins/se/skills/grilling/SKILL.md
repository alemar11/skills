---
name: grilling
description: "Refine a topic or handoff one question at a time when explicitly requested or composed by SE."
---

# Grilling

Follow the shared [execution scope](../../references/execution-scope.md) for
standalone and composed invocation.

## Purpose and boundary

Use `$se:grilling` to turn a topic, proposal, plan, or composed handoff into a
clearer decision-ready brief through a demanding but constructive interview.
Infer the topic from the invoking prompt or supplied handoff when it is clear;
ask the user to choose only when multiple materially different topics remain.

Grilling is conversational and read-only. It may inspect repository context,
source, documentation, and other read-only evidence, but it never edits project
files, persists the transcript, creates tasks, or delegates work. If the user
asks to preserve an accepted rule or decision, return it as a durable-knowledge
candidate and use `$se:learn` separately only with the authority that request
provides. A parent read-only workflow may forbid even that follow-up capture.

Read [references/states.md](references/states.md) before interpreting workflow
or result state. Read the shared
[workflow-graph.md](../../references/workflow-graph.md) before using the
registry below.

## Context preflight

Before the first question, compose `$se:learn` in a strictly read-only context
inspection using `memory_slice=domain-memory`,
`domain_operation=periodic-review`, and `capture_mode=defer-to-caller`.
Require it to read the applicable `AGENTS.md` chain, root `CONTEXT.md`, matched
first-class subproject context, and only the topic files or ADRs relevant to
the inferred subject. Do not request setup, repair, compaction, or capture.

Treat repository evidence as grounding, not as a substitute for the user's
intent. If Learn is unavailable, stop before questioning and report the
dependency. If no repository context exists, continue from the supplied
conversation or handoff and state that the context read returned no established
project knowledge.

## Interview contract

- Ask exactly one question per turn.
- Pair that question with one concrete recommended answer and a concise reason
  it is the best current default. End by asking the user to accept it or state
  what should change.
- Make the recommendation falsifiable and specific enough to correct. Mark it
  provisional when evidence is incomplete; never hide uncertainty or present
  an unsupported preference as repository fact.
- Ask the highest-leverage unanswered question first: desired outcome, user or
  actor, success boundary, invariant, non-goal, failure behavior, tradeoff, or
  evidence requirement.
- Prefer concrete scenarios, counterexamples, and forced tradeoffs over broad
  invitations such as "tell me more."
- Challenge contradictions, vague nouns, hidden assumptions, and solutions
  presented as requirements. Stay direct and constructive rather than
  adversarial or performative.
- Do not ask for facts available in the repository or supplied handoff.
- After each answer, update the working interpretation silently. Briefly expose
  a correction only when it changes the meaning of the next question.
- Continue until no material ambiguity remains, the user asks to stop, or the
  session is blocked. Never choose a fixed question count.
- Before declaring the brief refined, ask one final confirmation question that
  presents the compact interpretation and invites correction.

When composed by Study, use the complete curated handoff as the starting brief
and ask the first question in the selected Study controller immediately after
the Learn read. For `study_surface=app-task`, keep every question and answer in
the separate visible Study task; the invoking parent may point the user there
but must not relay the interview turn by turn. For
`study_surface=cli-session`, keep every question and answer directly in the
invoking CLI session. On either surface, do not plan or create Study workers
until the Grilling outcome is `refined` or `user-stopped`.

## Workflow graph

The registry owns transitions; Mermaid is its projection.

| node_id | kind | purpose | entry_conditions | inputs | outputs | transitions | stop_if | side_effects | terminal_states |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| context-read | action | Ground the session in applicable Project Context through Learn. | explicit invocation or authorized parent handoff | topic or supplied handoff, repository scope | relevant context evidence or an empty-context observation | frame, blocked | Learn is unavailable or responsible repository scope cannot be resolved | read, transient | none |
| frame | decision | Infer the subject and select the highest-leverage ambiguity. | context inspection completed | supplied brief and context evidence | working interpretation and next ambiguity | question, blocked | no coherent topic can be selected without unavailable user input | transient | none |
| question | action | Ask exactly one focused question with a recommended answer, then incorporate the user's response. | one material ambiguity or final confirmation remains | working interpretation and latest user answer | recommendation, concise rationale, and updated interpretation or stop request | question, confirm, reported, blocked | required user input cannot be obtained | transient | none |
| confirm | decision | Present the compact interpretation for final user confirmation. | no known material ambiguity remains | working interpretation | confirmation, correction, or stop request | question, complete, reported | none | transient | none |
| complete | terminal | Return the user-confirmed refined handoff. | user confirms the compact interpretation | confirmed brief and evidence | refined handoff | none | terminal | none | complete |
| reported | terminal | Return the best-supported handoff after the user stops questioning. | user asks to stop before confirmation | working interpretation and evidence | handoff with unconfirmed items | none | terminal | none | reported |
| blocked | terminal | Report why responsible questioning or synthesis cannot continue. | required dependency, context, or input is unavailable | retained evidence and blocker | blocker and smallest recovery input | none | terminal | none | blocked |

## Transition conditions

This matrix owns the condition for every edge declared above.

| from | to | when |
| --- | --- | --- |
| context-read | frame | Learn returns relevant context evidence or a valid empty-context observation. |
| context-read | blocked | Learn is unavailable or repository scope cannot be resolved responsibly. |
| frame | question | one coherent topic and its next material ambiguity are known. |
| frame | blocked | a coherent topic cannot be selected and user input is unavailable. |
| question | question | the latest answer leaves another material ambiguity. |
| question | confirm | no known material ambiguity remains. |
| question | reported | the user asks to stop. |
| question | blocked | required user input cannot be obtained. |
| confirm | question | the user corrects or extends the compact interpretation. |
| confirm | complete | the user confirms the compact interpretation. |
| confirm | reported | the user asks to stop without confirming. |

~~~mermaid
flowchart TD
    context-read --> frame --> question
    context-read --> blocked
    frame --> blocked
    question --> question
    question --> confirm
    question --> reported
    question --> blocked
    confirm --> question
    confirm --> complete
    confirm --> reported
~~~

## Refined handoff

On `complete`, return a compact Markdown handoff containing:

- objective and intended user outcome;
- confirmed scope, non-goals, constraints, and invariants;
- accepted decisions and important terminology;
- success and failure criteria;
- evidence or validation expectations;
- remaining assumptions, risks, and genuinely unresolved questions;
- durable-knowledge candidates, if any, clearly marked as not captured.

On `reported`, return the same shape using the best supported interpretation and
label every unconfirmed item. On `blocked`, return the exact blocker and the
smallest input needed to resume. Do not include the raw interview transcript.

## Skill Dependencies

This skill requires the installed `$se:learn` skill for its initial read-only
Project Context inspection. It never installs, refreshes, substitutes, or
silently bypasses that dependency.
