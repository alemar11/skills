<!-- SE-owned reference derived from the durable repository-context contract. -->

# Durable Capture

Use this reference for `memory_slice=durable-capture` when the user states a
correction, preference, policy, accepted decision, localization convention, or
other knowledge intended to survive the current task.

## Durability Filter

Capture only guidance likely to remain useful across future work. Exclude:

- one-off instructions tied only to the current files or task;
- tentative, rejected, or unresolved ideas;
- raw transcript text, session paths, credentials, secrets, or private payloads;
- generic architecture advice not grounded in this repository or an accepted
  decision.

Strong durability signals include `always`, `never`, `default`, `from now on`,
`remember`, or `hard rule`. A signal mentioned descriptively is not authority
to write. An explicit instruction to remember, save, or preserve a specific
durable item is direct capture authority when repository scope and destination
are unambiguous.

## Setup Prerequisite

Before capturing a rule, apply [context-preflight.md](context-preflight.md). If
the selected Git root or first-class subproject lacks its required `CONTEXT.md`
or current canonical Project Context pointer, include the smallest setup
bootstrap in the capture run. Under direct scoped authority, create or repair
the root-first context chain and pointers, then capture the rule in the closest
applicable `AGENTS.md`. Do not expand the prerequisite to full setup or create
empty conditional surfaces.

## Scope Resolution

Determine the narrowest suitable scope before drafting:

1. repository root or affected subpath when the guidance concerns this project;
2. a global `AGENTS.md` only when the rule is genuinely cross-project and the
   user explicitly approves that target;
3. never fall back to global because a project target is missing.

For a subpath, prefer the closest existing `AGENTS.md`. If an evidenced
first-class subproject does not have one, create or propose that local target
and its root-first context prerequisite rather than silently widening scope.

## Destination Classification

| Knowledge | Destination |
| --- | --- |
| Rule that must apply on every task in scope | Closest applicable `AGENTS.md` |
| Conditional detail, example, rationale, or operational note | Nearest context owner's `project-context/<topic>.md` |
| Accepted load-bearing architectural decision | Root `project-context/adr/` when cross-project; local `project-context/adr/` when subproject-only |
| Localization or translation convention | `TRANSLATION.md` beside the owning context |
| Shared overview, vocabulary, routing, or explicit unknown | `CONTEXT.md` |

Keep the normative minimum in `AGENTS.md`. A topic file or ADR may be linked
from it, but it must not become a hidden replacement for an always-active rule.
Do not create a topic, ADR directory, or translation sidecar merely because a
candidate was mentioned; create it only after the durable target is authorized.

## Proposal And Confirmation

Before writing, show:

- the absolute target path and scope;
- the existing section or a proposed new section;
- exact wording and a concise rationale;
- meaningful before/after content;
- companion pointer, index, or link changes;
- duplicate or conflict handling;
- evidence supporting durability and destination choice.

For direct capture without unambiguous save/remember/preserve authority, wait
for affirmative approval of both target and wording. Silence, an unrelated
follow-up, or a target-selection reply is not approval. A composed caller may
authorize inline capture only when it supplies accepted knowledge, named
targets, repository scope, and capture authority.

## Apply And Verify

After authorization:

1. reread every target and stop on drift or conflict;
2. apply and verify any required minimal setup before the capture target;
3. update only the selected surface and preserve unrelated custom text;
4. update `CONTEXT.md` indexes, `adr/index.md`, or short AGENTS pointers when
   required; when the destination is `AGENTS.md`, ensure each inserted learning
   bullet ends with ` (Codex learning)` and do not add that marker to unrelated
   prose;
5. read the result back and verify relative links and target existence;
6. scan for duplicate normative wording and run `git diff --check`;
7. report `captured`, `deferred`, or `no-durable-change` with destinations and
   reasons separated from the knowledge data.
