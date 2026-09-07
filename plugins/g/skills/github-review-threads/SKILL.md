---
name: github-review-threads
description: "Inspect hosted review feedback and implement requested fixes. Posting replies or resolving threads requires authorization."
---

# GitHub Review Threads

Before any shell command that may contact GitHub or a package registry, read
and follow [Network execution](../../references/network-execution.md).

## Role

Own the feedback-to-code workflow for pull-request reviews: preserve thread
context, identify actionable feedback, implement only selected fixes, validate
them, and draft or publish dispositions with explicit authority.
Load [references/states.md](references/states.md) before classifying feedback,
review observations, reconciliation, or resolution results.

## Transport and CLI

Use the typed G commands below, backed by authenticated `gh`, for thread-aware
listing, resolution state, and mutations. Keep provider text file-backed and
require exact readback. Never place a title, body, description, reply, or
review text in argv or a shell string.

Before the first provider-facing shared CLI command, load
[`../../references/gh-dependency-preflight.md`](../../references/gh-dependency-preflight.md)
and require its host and authentication checks.

Resolve `<plugin-root>` as two directories above the directory containing this
`SKILL.md`. Before an operation, read the matching section of
[workflows.md](references/workflows.md): review inspection/waiting, thread
listing, replies, resolution, or other authorized discussion writes. Read
[script-summary.md](references/script-summary.md) when exact command/schema
fields or managed `reviews operation` orchestration are needed.

G owns immutable one-use mutation reservations and recovery. Preserve its
returned identities, fingerprints, and complete receipts; do not reconstruct
thread hashes or substitute raw GraphQL. Preparation and validation do not
authorize execution, and a consumed marker alone never proves provider success.

## Workflow

1. Resolve the base repository and PR, then list review threads with resolution
   state and enough surrounding diff context to understand each comment. When
   automatic review is configured and selected by the caller, use
   `reviews ready-check` or `reviews ready-wait` with that exact typed
   ready-transition receipt. These operations are read-only and never post
   `@codex review`. When the caller requires an explicit review, including the
   first ready PR review, independently verify its ready state and current full
   head SHA, then use a new caller-owned request key, invoke `reviews request`,
   and persist its
   complete request receipt. Pass that receipt unchanged to `reviews wait`; the
   waiter fetches the exact provider comment id and never substitutes a newer
   comment.
   Never accept review evidence from an older head. Reuse the returned
   `observation_fingerprint`; unchanged observations are not state transitions
   and must not cause caller-side ledger writes or progress messages.
   Use `reviews terminal-evidence` only to independently verify one exact typed
   explicit-request lineage after a caller has recorded a correlation failure.
   It is a read-only proof operation, never a replacement request or waiter.
2. Group duplicates and classify feedback with the canonical disposition from
   `references/states.md`.
3. Present or honor the selected actionable set. Do not silently implement
   every comment when the request selects only some.
4. Inspect adjacent code and tests, implement the selected changes locally, and
   validate the affected behavior.
5. Draft a disposition per selected thread that names the change and proof.
   Keep provider text in UTF-8 regular files outside the repository. Capture a
   `repo snapshot` immediately before each mutation and pass its fingerprint
   when the caller requires worktree protection.
6. Post replies, edit comments, submit reviews, or resolve threads only when the
   user explicitly authorizes publication or a calling workflow supplies exact
   PR/action authority. Never infer it from an inspect or review request.
   Reply only to one returned `finding_comment_ids` entry and persist the
   complete typed reply receipt. Resolve by passing that receipt unchanged to
   `reviews resolve`; never assemble a GraphQL thread id. Every resolution
   mutation gets one independent exact-target read-back and no blind retry. Preserve
   returned partial-success evidence if the provider write is confirmed but
   the worktree guard fails.
7. The v1 typed resolver is limited to actionable findings whose requested
   change was implemented and validated. It re-reads the exact finding, reply,
   head, and thread membership before resolving. `already-resolved` is a safe
   no-op only after the same proof succeeds; it does not identify who resolved
   the thread. Never substitute a top-level PR comment for a thread reply.
8. After pushing a review fix, request a fresh automated review with a new
   request key when required and check or wait against the new full head SHA.
   Repeat only within the caller's repair budget and acceptance policy. Return
   findings or blockers to that owner rather than imposing an unbounded loop.
   A generic `not-requested` observation, absence of comments, or zero
   unresolved threads never substitutes for the terminal result of the selected
   explicit-request or configured automatic-review lineage. An interrupted wait
   resumes its existing receipt and deadline without posting another request.
   If a bounded wait times out and
   continued monitoring is authorized, return the pending state to the caller;
   scheduling or heartbeat ownership remains with that caller. Callers must use
   the bounded waiter instead of wrapping one-shot checks in manual sleep loops.
   A composing caller owns and passes its duration; G never selects,
   extends, or segments that caller's deadline.

For a composed workflow, require the exact PR target and one canonical
`review_operation`. Mutating operations additionally require
`mutation_mode=apply`. Caller-specific authorization and phase policy must be
normalized before invocation; reject those caller-owned fields instead of
interpreting them here.

## References

- `references/workflows.md`: feedback, reply, resolution, and direct-command flows.
- `references/states.md`: feedback, review, reconciliation, and resolution
  states.
- `references/script-summary.md`: shared `g reviews` contract.
- `../../references/options.md`: shared canonical G options and caller handoffs.
