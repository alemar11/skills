# GitHub Review Workflows

Use [states.md](states.md) for canonical feedback, request-binding, review,
recovery, operation-result, reconciliation, and resolution states.

## Check Or Wait For Automated Review

### Initial automatic review

When automatic Codex review is configured and the caller selects that route,
opening a PR for review triggers the
first review without an `@codex review` comment. Bind that cycle to the exact
G-owned draft-to-ready transition receipt and published full SHA:

```bash
<plugin-root>/scripts/g --json reviews ready-check --provider codex --repo <owner/repo> --pr <number> --head <full-40-sha> --ready-receipt-file <absolute-ready-receipt-file>
<plugin-root>/scripts/g --json reviews ready-wait --provider codex --repo <owner/repo> --pr <number> --head <full-40-sha> --ready-receipt-file <absolute-ready-receipt-file> --timeout <caller-owned-duration>
```

`ready-check` reads once. `ready-wait` polls with bounded backoff. Neither posts
or searches for an explicit request comment. G may normalize a clean formal
review, authenticated terminal comment, or provider-authored PR-level 👍
reaction created after the ready transition as terminal clean evidence.
Findings are terminal for that reviewed head. Absence of
comments, zero unresolved threads, or a generic `not-requested` observation is
not terminal evidence for this ready-triggered lineage.

### Explicit review of a ready PR

When the caller requires an explicit review, verify the PR is ready and create
one typed request for its current full SHA, including the first review when
automatic review is disabled. After fixes are committed, validated, and pushed,
request a new review for the changed HEAD. Resume an existing cycle using its
receipt rather than posting another request. G owns the only accepted request
grammar and returns the complete provider identity receipt:

```bash
<plugin-root>/scripts/g --json reviews request --provider codex --repo <owner/repo> --pr <number> --head <full-40-sha> --request-key <request-key> --reservation-file <absolute-reservation-file>
```

The generated body is exactly `@codex review <full-40-sha>` followed by the
versioned G marker and request fingerprint. Callers cannot provide or
assemble request text. The operation reuses only one exact matching comment;
plain, markerless, malformed, conflicting, or duplicate requests fail closed.

In the current G review contract, `prepare` and `validate` remain read-only
packet creation and inspection surfaces. Provider mutations require the exact
G reservation; G itself owns its atomic one-use consumption and recovery state
and has no runtime dependency on an orchestrator skill or its ledger.
After the one-use marker is consumed, a replay performs one read-only lookup:
only one exact marker/target/body/thread/actor artifact may return a recovered
receipt. Missing or ambiguous evidence returns the owner-recovery disposition
from `states.md` and never posts or resolves again.

Use the returned receipt for the one-shot read or bounded wait:

```bash
<plugin-root>/scripts/g --json reviews check --provider codex --repo <owner/repo> --pr <number> --head <full-40-sha> --request-receipt-file <absolute-receipt-file>
<plugin-root>/scripts/g --json reviews wait --provider codex --repo <owner/repo> --pr <number> --head <full-40-sha> --request-receipt-file <absolute-receipt-file> --timeout <caller-owned-duration>
```

For composition, `<caller-owned-duration>` is the remaining time derived from
the caller's deadline. G does not select, extend, or segment that bound.

`check` reads once. `wait` requires the complete persisted receipt and polls
with bounded backoff until it sees `clean` or `findings`, detects a typed
terminal state or binding failure, or reaches its timeout. The
current provider adapter is `codex`; provider-specific bot identities,
acknowledgements, formal reviews, inline findings, authenticated top-level
terminal comments, clean reactions, and current-head matching belong to the
CLI rather than this workflow. A terminal comment counts only when it follows
the matching request, names the expected reviewed commit, and comes from the
authenticated provider identity. Conflicting terminal outcomes or overlapping
requests for the same head that prevent safe result correlation return an API
error rather than an arbitrary result.

The returned `observation_fingerprint` covers normalized review and request
evidence but excludes attempts and elapsed time. A caller may persist the
first observation and later transitions, but must not rewrite control state or
emit progress for an unchanged fingerprint. Use one bounded `wait`; do not
build a manual `check` plus shell-sleep loop around it.

Repeat the fix, push, fresh typed request, and wait cycle within the caller's
repair budget and acceptance policy; return unresolved findings when it is
exhausted. A timed-out
wait returns exit code `124`, the last observed state, attempt count,
transition count, and unchanged-attempt count; a calling orchestrator decides
whether to schedule a later heartbeat.

## List Review Context

Resolve `<plugin-root>` as two directories above the directory containing the owning
`SKILL.md` before using these commands.

```bash
<plugin-root>/scripts/g reviews address --repo <owner/repo> --pr <number>
<plugin-root>/scripts/g --json reviews address --repo <owner/repo> --pr <number>
```

By default, resolved or outdated review threads are omitted. Add
`--include-resolved` only when the user asks for full history.
JSON thread-comment entries include the current full `head_sha` and canonical
`thread_fingerprint`; pass those typed values to `reviews prepare` for a reply
or resolution reservation instead of reimplementing the thread hash.

## Reply To One Review Comment

First inspect the current-head result. `review.finding_comment_ids` is the
addressable inline subset and its length equals `review.findings`; a terminal
`findings` verdict may legitimately have zero addressable inline findings.
Reply to exactly one listed REST review-comment id and bind the reply to the
current full head:

```bash
<plugin-root>/scripts/g --json repo snapshot
<plugin-root>/scripts/g --json reviews reply --repo <owner/repo> --pr <number> --head <full-40-sha> --comment-id <id> --request-key <request-key> --request-fingerprint <request-fingerprint> --body-file <absolute-message-file> --reservation-file <absolute-reservation-file> --expected-worktree-fingerprint <sha256> --dry-run
<plugin-root>/scripts/g --json reviews reply --repo <owner/repo> --pr <number> --head <full-40-sha> --comment-id <id> --request-key <request-key> --request-fingerprint <request-fingerprint> --body-file <absolute-message-file> --reservation-file <absolute-reservation-file> --expected-worktree-fingerprint <sha256>
```

Write reply text to an absolute UTF-8 regular non-symlink file outside the
repository. The command rejects inline text. Remove temporary message files
after provider identity, target, body fingerprint, and worktree proof are
verified.

Use `--dry-run` unless the user already approved posting or a calling workflow
supplies `mutation_mode=apply`, the exact PR and comment id, reply body, and
`review_operation=reply`.

The successful result contains a typed reply receipt binding repository, PR,
finding head, reply head, exact finding and reply REST and GraphQL node ids,
thread id, author, URLs, timestamps, and body and identity fingerprints.
G re-reads the PR head after the reply proof and emits no reusable
receipt if that post-write head cannot be proven unchanged. Persist a returned
receipt unchanged.

## Resolve One Actionable Finding

Resolve only after the requested fix and evidence reply are complete:

```bash
<plugin-root>/scripts/g --json reviews resolve --repo <owner/repo> --pr <number> --head <full-40-sha> --request-key <request-key> --request-fingerprint <request-fingerprint> --reply-receipt-file <absolute-receipt-file> --reservation-file <absolute-reservation-file> --expected-worktree-fingerprint <sha256> --dry-run
<plugin-root>/scripts/g --json reviews resolve --repo <owner/repo> --pr <number> --head <full-40-sha> --request-key <request-key> --request-fingerprint <request-fingerprint> --reply-receipt-file <absolute-receipt-file> --reservation-file <absolute-reservation-file> --expected-worktree-fingerprint <sha256>
```

The resolver validates the complete receipt, re-reads the exact REST finding
and reply, paginates every GraphQL review-thread and comment page, and requires
one unique thread containing both exact node ids in the exact repository and
PR. After every mutation attempt it performs one independent exact-thread
read-back and checks the current head. A proven success reports
`mutation_attempted=true` and `mutation_may_have_applied=false`; an uncertain
post-attempt failure reports both as true. `already-resolved`
is idempotent only after all the same proof succeeds and makes no claim about
who resolved the thread.

If the mutation may have applied but exact read-back or head proof is
uncertain, the typed error includes `mutation_may_have_applied=true`. Do not
retry, undo, or fall back to raw GraphQL. V1 does not resolve no-change
dispositions.

## Edit Comments Or Submit Reviews

```bash
<plugin-root>/scripts/g reviews edit-comment --repo <owner/repo> --pr <number> --kind <conversation-or-review> --comment-id <id> --body-file <absolute-message-file> --expected-worktree-fingerprint <sha256>
<plugin-root>/scripts/g reviews submit-review --repo <owner/repo> --pr <number> --event <approve-or-request-changes-or-comment> --body-file <absolute-message-file> --expected-worktree-fingerprint <sha256>
```

Each command verifies the existing target before writing and the returned
provider object afterward. On an ambiguous write it performs one exact-target
read-back and fails closed; do not retry it blindly.

## Post Top-Level PR Discussion Comments

Use the helper for normal PR discussion comments. The separate typed
review-request operation owns request composition, head binding, identity,
acknowledgment, and waiting.

```bash
<plugin-root>/scripts/g reviews comment --repo <owner/repo> --pr <number> --head <full-40-sha> --request-key <request-key> --request-fingerprint <request-fingerprint> --body-file <absolute-message-file> --reservation-file <absolute-reservation-file> --expected-worktree-fingerprint <sha256> --dry-run
<plugin-root>/scripts/g reviews comment --repo <owner/repo> --pr <number> --head <full-40-sha> --request-key <request-key> --request-fingerprint <request-fingerprint> --body-file <absolute-message-file> --reservation-file <absolute-reservation-file> --expected-worktree-fingerprint <sha256>
```

Use `--dry-run` unless the user explicitly asked to post the discussion comment
or a calling workflow supplies `mutation_mode=apply`, the exact PR, the comment
body, and `review_operation=comment` for another discussion comment. Use the
typed `reviews request` operation for automated-review requests. Caller-specific
authorization and phase fields must be normalized before this boundary.

## Direct Commands

Use direct `gh` only for a genuinely file-backed operation. If no safe
file-backed operation exists, fail closed and report the unavailable operation.

```bash
gh pr comment <number> --repo <owner/repo> --body-file <message-file>
gh pr view <number> --repo <owner/repo> --comments
```

There is no direct legacy fallback for typed review requests or typed thread
resolution; use G so receipts and exact-head bindings are preserved.
