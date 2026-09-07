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
`SKILL.md`:

```bash
<plugin-root>/scripts/g --help
<plugin-root>/scripts/g --version
<plugin-root>/scripts/g --json doctor
<plugin-root>/scripts/g --json repo snapshot
<plugin-root>/scripts/g --json reviews address --repo <owner/repo> --pr <number>
<plugin-root>/scripts/g --json reviews request --provider codex --repo <owner/repo> --pr <number> --head <full-40-sha> --request-key <request-key> --reservation-file <absolute-reservation-file>
<plugin-root>/scripts/g --json reviews check --provider codex --repo <owner/repo> --pr <number> --head <sha>
<plugin-root>/scripts/g --json reviews wait --provider codex --repo <owner/repo> --pr <number> --head <full-40-sha> --request-receipt-file <absolute-receipt-file> --timeout <caller-owned-duration>
<plugin-root>/scripts/g --json reviews terminal-evidence --provider codex --repo <owner/repo> --pr <number> --head <full-40-sha> --request-receipt-file <absolute-receipt-file>
<plugin-root>/scripts/g --json reviews reply --repo <owner/repo> --pr <number> --head <full-40-sha> --comment-id <id> --request-key <request-key> --request-fingerprint <request-fingerprint> --body-file <absolute-message-file> --reservation-file <absolute-reservation-file> --expected-worktree-fingerprint <sha256>
<plugin-root>/scripts/g --json reviews resolve --repo <owner/repo> --pr <number> --head <full-40-sha> --request-key <request-key> --request-fingerprint <request-fingerprint> --reply-receipt-file <absolute-receipt-file> --reservation-file <absolute-reservation-file> --expected-worktree-fingerprint <sha256>
<plugin-root>/scripts/g reviews comment --repo <owner/repo> --pr <number> --head <full-40-sha> --request-key <request-key> --request-fingerprint <request-fingerprint> --body-file <absolute-message-file> --reservation-file <absolute-reservation-file> --expected-worktree-fingerprint <sha256> --dry-run
```

The CLI validates absolute regular non-symlink UTF-8 files, sends JSON to `gh
api --input -`, emits byte counts and SHA-256 fingerprints instead of text, and
verifies provider identity, target, response text, and an optional Git
worktree fingerprint. It writes no implicit config.
Its Codex adapter normalizes formal reviews,
inline findings, authenticated top-level terminal result comments, and clean
reactions into one current-head state and one stable observation fingerprint.

The current G review contract is self-contained. The four provider mutation
commands (`request`, timeout-warning `comment`, `reply`, and `resolve`) require
an exact immutable G reservation packet. G atomically consumes that packet
before transport and owns the durable one-use marker and recovery readback; it
does not locate, load, or execute another skill to authorize the mutation.
Use JSON `reviews address` as the typed source for a review thread's current
`head_sha` and `thread_fingerprint` before preparing reply or resolution
authority; do not reproduce the hash locally.

Managed orchestration uses the closed `reviews operation` family. G owns
the complete request/result schemas for `request`, `wait`, `ready-check`,
`ready-wait`, `warning`, `reply`, `resolve`, `reconcile-mutation`, and
`reconcile-terminal`. Preparation and
validation are read-only. Execution atomically appends a
`g-review-operation-start:v1` receipt to G's own per-user journal
before transport; resume and reconciliation read the same exact journal and
never create a second mutation, repost, or reset a wait deadline.
For an owned `reply`, prepare derives the exact live thread id and pre-reply
fingerprint through read-only provider inspection; callers do not supply those
fields. `resume` reloads the original wait and deadline. `reconcile-mutation`
keeps marker absence, marker-only state, unique provider readback, and
conflicting/ambiguous readback distinct, and never treats a consumed marker as
sufficient proof of success.

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
