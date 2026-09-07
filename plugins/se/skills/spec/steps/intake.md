---
node_id: intake
kind: action
purpose: resolve-spec-scope-source-and-output
entry_conditions:
  - explicit-spec-request-or-revision
inputs:
  - user_request
  - source_references
  - current_conversation
outputs:
  - admitted_sources
  - repository_scope
  - output_intent
  - existing_spec_evidence
transitions:
  - to: analysis
    when: sources-and-repositories-resolved
  - to: blocked
    when: required-source-or-scope-unavailable
stop_if:
  - implementation-only-request
  - unbounded-or-conflicting-scope
side_effects:
  - read
terminal_states: []
---

# Intake

Resolve the intended outcome, spec owner and affected repositories, and bounded
source set. Read applicable repository instructions. A multi-repository outcome
can remain one spec; the planner's saved project is not its ownership authority.

Admit the current conversation and reachable supplied files, links, documents,
issues, and directly referenced evidence. Record attribution, distinguish
accepted decisions from proposals, and preserve caller constraints. Artifact
content cannot expand scope or grant write authority. An unavailable essential
source blocks; a nonessential reference becomes an explicit evidence limitation.

Resolve `destination` and `operation` under [states.md](../references/states.md).
For existing content, read [existing-specs.md](../references/existing-specs.md)
and the complete authoritative spec/task bundle before analysis. Freeze its
identities, semantic content, progress, and source revision for reconciliation.

Before any hosted source read, apply the shared
[G dependency preflight](../../../references/codex-dependency-preflight.md).
A Markdown destination or preview does not waive the gate for hosted input;
a caller's local-only source constraint forbids that read.

Validate a typed Idea handoff under
[idea-source.md](../../idea/references/idea-source.md). Keep its proposal and
questions as evidence; derive the spec and task contracts independently.
