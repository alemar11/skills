---
name: learn
description: "Save or maintain durable repository knowledge when explicitly requested; make only authorized local changes."
---

# Learn Project Context

## Purpose and boundary

Use `$se:learn` for durable, local repository knowledge: always-active rules in
`AGENTS.md`, root-first `CONTEXT.md` routing, conditional topic files, accepted
ADRs, localization guidance, Code Review Rules, and explicit AGENTS.md
compaction proposals.

Learn never owns tracker content, delivery state, branches, pull requests,
provider transport, task graphs, or worker configuration. It may inspect local
evidence and modify only authorized context surfaces. It never contacts a
hosted provider and has no publish mode.

## Select and load one branch

Read [options.md](references/options.md) to resolve the smallest canonical
`memory_slice`. Read [setup-workflow.md](references/setup-workflow.md) for the
Project Context pointer preflight. Then load only the
selected branch:

| Work | Read |
| --- | --- |
| Domain setup/bootstrap | [domain.md](references/domain.md), [domain-modeling.md](references/domain-modeling.md), [context-seed.md](references/context-seed.md), and setup-workflow.md |
| Domain inline update, implementation closeout, or periodic review | [domain-modeling.md](references/domain-modeling.md); add domain.md only for layout ambiguity and [documentation-shapes.md](references/documentation-shapes.md) only when no stronger local shape exists |
| Durable capture | [durable-capture.md](references/durable-capture.md); add only the destination-specific domain, documentation-shape, or translation reference it routes to |
| Translation memory | [translation.md](references/translation.md) and setup-workflow.md |
| AGENTS.md pointers | setup-workflow.md |
| AGENTS.md compaction | [agents-compaction.md](references/agents-compaction.md), documentation-shapes.md, and domain.md only when the context index changes |
| Code Review Rules | [code-review-rules.md](references/code-review-rules.md) and only the evidence or evaluation references it routes to |
| Explicit full setup | domain.md, domain-modeling.md, context-seed.md, setup-workflow.md, and only evidenced optional branches |

Load [session-history.md](references/session-history.md) only for accepted
existing-project evidence. Load [setup-questions.md](references/setup-questions.md)
only when repository evidence and documented defaults leave one material
ambiguity.

## Invocation preflight and authority

Before the selected branch, resolve the actual root-to-target `AGENTS.md`
chain, read root `CONTEXT.md` first when it exists, follow only relevant scoped
routes, and classify the canonical Project Context pointer. Reconcile a pointer
only when the current request already authorizes that context write; otherwise
report the exact proposal. The preflight derives state and never grants write
authority.

Apply these authority rules:

- Inspection, review, proposal, and dry-run requests are read-only.
- Explicit setup, initialization, update, or refresh authorizes only the named
  local context scope.
- An explicit request to remember, save, or preserve one unambiguous durable
  item authorizes that item and its smallest required context bootstrap.
- A composed handoff writes only accepted knowledge with named targets and
  explicit inline-capture authority.
- For AGENTS.md compaction, prepare an exact before/after change. Apply it
  when the request authorizes the edit; a review-only request stays read-only.

When scope, wording, destination, or a conflict remains material, draft the
exact change and stop for confirmation. Never infer capture from ordinary
conversation, tentative ideas, raw session text, secrets, or file churn.

## Workflow graph

Read the shared [workflow-graph.md](../../references/workflow-graph.md) before
using this registry. Read [states.md](references/states.md) before interpreting
workflow, option, derived, result, or persisted state. The registry is the
structural source of truth; Mermaid is its projection.

| node_id | kind | entry condition | transitions | terminal state |
| --- | --- | --- | --- | --- |
| scope | action | explicit repository-knowledge request | inspect, blocked | none |
| inspect | action | repository scope and memory slice resolved | draft, blocked | none |
| draft | decision | evidence and intended target are known | reported, confirm | none |
| confirm | decision | durable write is requested | apply, deferred, blocked | none |
| apply | action | exact target and authority confirmed | verify, blocked | none |
| verify | validation | selected surface was applied | complete, blocked | none |
| reported | terminal | read-only or non-durable result is ready | none | reported |
| deferred | terminal | user decision or confirmation is required | none | deferred |
| complete | terminal | authorized write was verified | none | complete |
| blocked | terminal | required evidence, authority, or verification is unavailable | none | blocked |

~~~mermaid
flowchart TD
    scope --> inspect --> draft
    scope --> blocked
    inspect --> blocked
    draft --> reported
    draft --> confirm
    confirm --> apply --> verify
    confirm --> deferred
    confirm --> blocked
    apply --> blocked
    verify --> complete
    verify --> blocked
~~~

## Execution and result

1. Resolve the smallest slice, repository scope, evidence boundary, and current
   authority.
2. Inspect the applicable context chain and only the evidence required by the
   selected branch.
3. Draft exact targets, wording, evidence, unknowns, and links.
4. Report read-only work; otherwise confirm when required, apply only authorized
   local changes, then read them back and verify links, indexes, preserved
   content, and the diff.
5. Return the terminal state, changed files, capture outcome, pointer state,
   context ownership, and only the selected branch's additional result fields.

Use the current Git repository as the default scope. Cross-repository work
requires explicitly authorized identities and candidate roots verified
one-to-one. Preserve unrelated content. Learn has no persisted workflow
checkpoint, run ledger, generic run mode, or stored write preference.
