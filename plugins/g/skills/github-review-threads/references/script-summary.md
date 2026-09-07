# reviews Script Contract

This file mirrors the shipped command and JSON schema surface. Canonical state
values, meanings, terminality, and legal reconciliation pairs are owned by
[states.md](states.md).

## Commands

```bash
<plugin-root>/scripts/g reviews --help
<plugin-root>/scripts/g --version
<plugin-root>/scripts/g doctor
<plugin-root>/scripts/g --json doctor
<plugin-root>/scripts/g --json repo snapshot
<plugin-root>/scripts/g --json reviews operation prepare --controller-envelope-file <absolute-controller-json> --input-file <absolute-input-json> --request-output <absolute-request-json>
<plugin-root>/scripts/g --json reviews operation validate-request --request-file <absolute-request-json>
<plugin-root>/scripts/g --json reviews operation execute --request-file <absolute-request-json> --result-output <absolute-result-json>
<plugin-root>/scripts/g --json reviews operation reconcile --request-file <absolute-reconciliation-request-json> --result-output <absolute-result-json>
<plugin-root>/scripts/g --json reviews operation validate-result --request-file <absolute-request-json> --result-file <absolute-result-json>
<plugin-root>/scripts/g reviews address --repo <owner/repo> --pr <number>
<plugin-root>/scripts/g --json reviews request --provider codex --repo <owner/repo> --pr <number> --head <full-40-sha> --request-key <request-key> --reservation-file <absolute-reservation-file>
<plugin-root>/scripts/g --json reviews reply --repo <owner/repo> --pr <number> --head <full-40-sha> --comment-id <id> --request-key <request-key> --request-fingerprint <request-fingerprint> --body-file <absolute-message-file> --reservation-file <absolute-reservation-file>
<plugin-root>/scripts/g --json reviews resolve --repo <owner/repo> --pr <number> --head <full-40-sha> --request-key <request-key> --request-fingerprint <request-fingerprint> --reply-receipt-file <absolute-receipt-file> --reservation-file <absolute-reservation-file>
<plugin-root>/scripts/g reviews edit-comment --repo <owner/repo> --pr <number> --kind <conversation-or-review> --comment-id <id> --body-file <absolute-message-file>
<plugin-root>/scripts/g reviews submit-review --repo <owner/repo> --pr <number> --event <approve-or-request-changes-or-comment> --body-file <absolute-message-file>
<plugin-root>/scripts/g reviews comment --repo <owner/repo> --pr <number> --head <full-40-sha> --request-key <request-key> --request-fingerprint <request-fingerprint> --body-file <absolute-message-file> --reservation-file <absolute-reservation-file>
<plugin-root>/scripts/g --json reviews ready-trigger --provider codex --repo <owner/repo> --pr <number> --head <full-40-sha> --ready-event-id <event-id> --ready-ref <event-url> --ready-at <utc-timestamp> --base-branch <branch> --body-fingerprint <sha256> --output-file <absolute-ready-receipt-file>
<plugin-root>/scripts/g --json reviews check --provider codex --repo <owner/repo> --pr <number> --head <sha>
<plugin-root>/scripts/g --json reviews wait --provider codex --repo <owner/repo> --pr <number> --head <full-40-sha> --request-receipt-file <absolute-receipt-file> --timeout <caller-owned-duration>
<plugin-root>/scripts/g --json reviews ready-check --provider codex --repo <owner/repo> --pr <number> --head <full-40-sha> --ready-receipt-file <absolute-ready-receipt-file>
<plugin-root>/scripts/g --json reviews ready-wait --provider codex --repo <owner/repo> --pr <number> --head <full-40-sha> --ready-receipt-file <absolute-ready-receipt-file> --timeout <caller-owned-duration>
<plugin-root>/scripts/g --json reviews terminal-evidence --provider codex --repo <owner/repo> --pr <number> --head <full-40-sha> --request-receipt-file <absolute-receipt-file>
```

Resolve `<plugin-root>` as two directories above the directory containing the owning
`SKILL.md`. All provider text is mandatory file-backed input; inline provider
text flags do not exist.

## JSON Mode

Success envelopes:

```json
{
  "ok": true,
  "version": "<plugin-version>",
  "command": ["address"],
  "data": {}
}
```

Error envelopes:

```json
{
  "ok": false,
  "version": "<plugin-version>",
  "command": ["address"],
  "error": {"code": "invalid_arguments", "message": "..."}
}
```

The script does not write configuration files.

## Owned Review Operations

Managed orchestration uses the closed operations `request`, `wait`,
`ready-check`, `ready-wait`, `warning`, `reply`, `resolve`,
`reconcile-mutation`, and `reconcile-terminal`. The current G review contract
owns the complete `g-review-operation-request:v1` and
`g-review-operation-result:v1` schemas. `prepare` and both validators are
read-only. `execute` revalidates the exact controller envelope and atomically
writes a `g-review-operation-start:v1` receipt to G's own journal
immediately before transport. `resume` and `reconcile` require the same exact
journal identity and never post twice, retry a consumed mutation, or extend a wait.

Owned reply preparation reads the selected finding and its unique live thread
read-only, derives the canonical thread id/fingerprint, and writes those values
into the immutable request; caller-supplied thread identity is rejected.
`resume` reloads the original started wait and its immutable 45-minute deadline,
using one zero-timeout observation after expiry. Mutation reconciliation
distinguishes no consumed marker, an exact marker without a provider artifact,
a unique exact artifact, and conflicting, ambiguous, or unreadable evidence.
A marker alone never proves provider success, and reconciliation never invokes
mutation transport.

The controller template is selection evidence, not provider authority. Request
keys are SHA-256 identities. Wait requests require canonical UTC timestamps and
`wait_deadline=wait_started_at+45m`; an expired deadline performs one zero-timeout
check. Results use closed status/outcome pairs and exact per-operation facts.
Terminal reconciliation embeds the prior failed wait result and appends only an
independently verified clean or findings result for the identical repository,
PR, head, typed request receipt, and provider lineage. Result admission must use
the request-correlating validator; standalone result shape validation is not
sufficient authority for a ledger write.

## Automated Review State

`request` returns a canonical body fingerprint and a complete receipt with
`request_key`, request/body/identity fingerprints, exact provider comment id,
URL, and creation time. `wait` requires that receipt and fetches that exact id.
Both `check` and `wait` return `data.provider`, `data.request_binding`,
`data.review_state`, `data.head`, `data.current_head`, `data.head_is_current`,
`data.observation_fingerprint`, plus normalized review, request,
terminal-comment, and selected terminal evidence. An identity-bound check
returns the saved request receipt unchanged; a receipt-less diagnostic uses a
`kind=observed-request` metadata object and never returns a persistable receipt.
Acknowledgment flags are in `data.request_observation`. Request bindings and
review states use the closed registries in `states.md`. `review_state` is
factual CLI result state, not an invocation option. Terminal evidence may be a formal review, an
authenticated provider-authored top-level comment posted after the matching
request and naming the reviewed head, or a clean provider reaction. Conflicting
terminal outcomes return `ambiguous_review_evidence` with exit code `4`.
Missing binding or acknowledgment is also exit `4`, never `stale` and never
timeout-eligible. `stale` is reserved for actual PR-head drift or mismatched
provider terminal evidence.

Review-state exit mappings are defined in `states.md`. Exit `64` remains
invalid arguments and `124` remains a bounded-wait timeout. JSON envelopes
remain valid for nonzero review-state exits.

`wait` accepts `--timeout`, `--interval`, and `--max-interval` durations using
seconds, minutes, or hours, such as `30s`, `15m`, or `1h`.
`--timeout` bounds one invocation. A composing caller that owns a deadline
derives and passes `<caller-owned-duration>`; G never replaces, extends,
or segments it.
`request` requires a full 40-character lowercase head SHA and a caller-supplied
request key. Only its exact canonical marker is recognized; markerless plain,
short, or prose requests are diagnosed as `unbound`, while malformed or
conflicting typed markers are `invalid`.
`check` may inspect without a receipt, but `wait` requires one and never scans
for a replacement SHA-bearing comment. `ready-check` and `ready-wait` require a
`g-codex-ready-trigger:v1` receipt proving one exact draft-to-ready transition;
they correlate only provider artifacts after that ready timestamp and exact
full SHA. They never create or search for an explicit request comment and
return a `g-codex-ready-review-certificate:v1` projection with the observation.
Use ready lineage only when automatic review is configured and selected.
An explicit-review caller uses `request` and identity-bound `wait` for the
initial ready HEAD and each changed HEAD, within its repair budget and acceptance
policy. Resume the existing receipt/deadline without a duplicate mention.
Do not treat receipt-less `not-requested`, absent comments, or zero unresolved
threads as a clean result for either lineage.
`wait` also returns `attempts`, `state_transitions`, and `unchanged_attempts`.
The observation fingerprint excludes those counters and elapsed time, so
callers can suppress unchanged ledger and progress updates.
`data.review.finding_comment_ids` is the sorted addressable inline-comment
subset and its length equals `data.review.findings`. A terminal provider
`findings` verdict may have an empty subset.

`check` and `wait` expose stable `failure_kind` and `error_code` fields. A
typed request-comment mismatch is `request-correlation-failure` only when the
machine code is `request_correlation_failure`; API, authentication,
configuration, provider-terminal, head-drift, and ambiguity failures remain
separate.

`terminal-evidence` re-proves the complete typed request receipt and exact
request comment, unchanged full PR head, bounded request lineage, authenticated
provider actor, exact terminal comment body fingerprint and outcome. It rejects
later or overlapping requests, duplicate or multiple plausible artifacts,
inline findings, findings/error formal reviews, conflicting terminal outcomes,
and edited or deleted request/artifact comments. Success returns one
`g-terminal-provider-evidence:v1` receipt; it performs no mutation,
request, wait, retry, or deadline operation.

## Discussion Comments

`address` is read-only. Use `comment`, one-target `reply`, `edit-comment`, and
`submit-review` for mutations. They require absolute regular non-symlink UTF-8
body files and accept optional `--expected-worktree-fingerprint` protection.
Its JSON thread entries include the exact current `head_sha` and
`thread_fingerprint` needed by typed `reviews prepare`; callers must use those
values rather than recreating the canonical fingerprint.
Dry-run and result envelopes contain only byte counts, SHA-256 fingerprints,
target identity, and transport metadata; they never contain provider text.

Successful discussion writes return provider object id and URL, exact target identity, and
the submitted body fingerprint. An ambiguous write performs one read-back and
returns `provider_write_ambiguous` without retrying. A confirmed write followed
by worktree drift returns `provider_write_partial_success` with the confirmed
provider identity in error details.

`reply` requires the full current head and returns a
`g-review-thread-reply:v1` receipt with immutable finding, reply,
repository, PR, head, thread, author, URL, timestamp, and fingerprint identity.
`resolve` accepts only that complete receipt, discovers the unique thread by
the exact finding GraphQL node id with full pagination, re-proves both REST
comments and thread membership, and returns a
`g-review-thread-resolution:v1` receipt. Resolution statuses use the canonical
registry in `states.md`.
Every mutation attempt gets one independent exact read-back. Resolution flags
use the canonical per-path rules in `states.md`; in particular, recovery of a
previously consumed reservation preserves that the prior mutation may have
applied. Dry-run and `already-resolved` set both mutation flags to false.

Wrong repository, PR, head, finding, reply, thread, body, author, or timestamp;
missing or duplicate thread matches; missing evidence; and unsupported thread
state fail closed. When a resolution write may have landed but read-back or
head proof is uncertain, error details set
`mutation_may_have_applied=true`; callers must not retry or use raw GraphQL.

## Maintenance Source

The shipped command is built from the plugin maintenance project and invoked only through `<plugin-root>/scripts/g`.
