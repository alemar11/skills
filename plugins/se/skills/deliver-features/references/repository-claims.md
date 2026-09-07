# Repository Claims

The host-local registry serializes overlapping Delivery repository ownership.
It stores only ownership, never task progress, worker assignments, review
receipts, budgets, or workflow position. The schema remains version 1.

## Identity and authority

Use the GitHub database repository ID as `github:<positive-decimal-id>`, without
leading zeroes or whitespace. Owner/name, GraphQL IDs, paths, and titles are not
identity. Resolve the current coordinator's stable task identity and its saved
project identity before acquisition. Use `projectless` only when no saved
project is associated; this metadata does not create or relocate a task.

Freeze the exact repository set from [task-delivery.md](task-delivery.md).
Generate a fresh 32-character lowercase hexadecimal fencing token for that
acquisition and keep it solely in the coordinator's protected execution context.
Do not send it to subagents or put it in arguments, environment variables,
shared files, logs, progress, or receipts. The current task alone acquires,
binds, and releases; a title or prompt cannot establish that identity.

Each row contains repository key, token, home project key, optional bound task
identity, and diagnostic claim time. The persisted name `orchestrator_task_id`
identifies the current coordinator; it is an existing CLI/schema field, not a
requirement to create another task. The set is immutable while claimed. Release
safely before acquiring an expanded set. Claims do not coordinate other hosts
and have no TTL, heartbeat, expiry, or automatic takeover.

## CLI

Use the shipped `scripts/repository-claims` help and JSON output. Its database
is `~/.cache/dotagents/plugins/se/skills/deliver-features/repository-claims.sqlite3`.

- `doctor` validates without creating a registry.
- `acquire` atomically initializes an empty registry and reserves the complete set
  provisionally. Failed initialization rolls back schema changes; `bind` and
  `release` never initialize a registry.
- `bind` attaches the current coordinator identity to that set.
- `inspect` returns redacted ownership, optionally by repository key.
- `release` removes the exact whole token group, using its bound task identity
  or the original owner's explicit provisional-abandonment assertion.

Mutations read the fencing token through protected standard input. No command
returns it. Invalid arguments must fail before creating or changing a registry;
JSON failures use a structured error and exit code `2`. Help/version stay
ordinary successful output. The CLI owns transactions, schema and permissions.

## Acquire and bind the current task

Acquire the entire set in one operation, then bind it to the current task and
read back the complete binding before any worker, Git, or hosted mutation.
Never create a separate coordinator or a token-bearing task handoff.

A `reuse-bound` group may be reused only with the retained fencing context and
an exact current-task binding. A provisional group belonging to this invocation
may finish that same bind after reconciliation. If binding never took effect,
its original owner may abandon the provisional group once no workers or other
mutations started. Missing fencing context, an uncertain bind, or foreign
ownership blocks mutation; inspect without automatic release or replacement.
A foreign claim does not authorize moving the request into another task.

On overlap, report the known owner and pause; never create a competing writer.
The same coordinator can acquire a new token after a verified release. Resume
rechecks the spec selection, preserved worktrees, branches, PRs, repair counts,
and review evidence before scheduling under its new claim.

## Safe pause and release

Invocation authorizes safe preservation and release on success, a pause,
exhausted repair budget, unavailable review, or a required user decision. First
finish independent runnable work unless the user requests an immediate stop.
Confirm every implementation/research/review subagent stopped and every write
or hosted submission resolved. A provider review or CI job may remain pending
after a confirmed submission; retain its exact request/job evidence for resume.
Release does not require the provider to finish, and never cancels its work.
Uncertain submission effects must still be reconciled before release.
Preserve commits, dirty work and exact worktree
identities without discarding user content. Save current progress and the
resume handoff before release. A safely paused run is not completed delivery.

Then release the exact whole group as the last mutation of this acquisition.
A successful transaction receipt identifies the exact released repository set.
Verify it equals the claimed set, then independently inspect current ownership.
An unclaimed set confirms release. A subsequently acquired foreign group is
valid new ownership, not failure of this release: report it without touching
that group. The old binding must be absent. Present absence or a new owner alone
cannot prove an earlier ambiguous release; require the exact successful release
evidence or pause for reconciliation. Never retry a mutation blindly.

If any actor may still write, work preservation fails, the binding remains,
release is ambiguous, or the registry is corrupt, retain ownership/uncertainty
and report it. Do not force release or repair the database. A verified safe
pause releases claims and returns its blocker or required decision; successful
release never upgrades a paused outcome to delivered.

For an old or foreign owner, absence of visible activity is insufficient proof
of quiescence. There is no automatic takeover, partial release, token expansion,
or force-release command. Schema validation rejects corrupt state before
mutation. Manual intervention requires its own explicit scope.
