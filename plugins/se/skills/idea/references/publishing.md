# SE Idea Publication

Read this reference when `run_mode=publish` has been resolved, including the
default publish branch. The G-owned GitHub issue workflow remains the only
transport and owns safe body handling, issue creation, verification, and
partial-failure mechanics.

Load the shared
[hosted-content-safety.md](../../../references/hosted-content-safety.md) before
the first write. SE owns the final portable title/body projection; G owns safe
file transport and readback but does not sanitize semantic content.

This reference is the only external terminal phase of the Idea workflow. The
capture and preview paths must not load the G dependency preflight, inspect
GitHub, or mutate hosted state.

## Dependency preflight

All hosted issue reads and writes belong to the repository's G-owned GitHub
issue workflow. Do not call a provider API directly, construct an alternative
transport, or return executable provider commands to the user. Capture and
explicit preview are fully local: they must not load G, inspect hosted issues,
or claim current hosted duplicate/collision state.

Only after the default or explicit `run_mode=publish` is resolved, before its
first hosted read or write, load
[`../../../references/codex-dependency-preflight.md`](../../../references/codex-dependency-preflight.md)
and complete its read-only availability gate. If the required G workflow is
missing, disabled, malformed, or unresolvable, fail closed before hosted
access; remediation is advisory and must never install, enable, refresh, or
substitute the dependency.

This is a hard hosted-access barrier. Until the preflight produces verified
G-dependency evidence, do not inspect hosted issues, repository metadata,
duplicate or collision state, native Issue Types, relations, or any other
hosted state. Resolve tracker ownership only from explicit local or session
evidence. If a hosted read is attempted before this barrier, stop and report a
preflight-order blocker instead of continuing or treating the read as a valid
preflight result.

The dependency gate authorizes the next workflow handoff only. The explicit
Idea request already authorizes the resolved in-scope Idea operations; the gate
does not broaden that scope.

## Hosted artifact

Each durable Idea is an open issue with:

- title `Idea: <Name>`;
- native Issue Type unset;
- the seven sections from `idea-template.md`.

Return a globally qualified durable ref such as `owner/repository#<number>` or
the canonical hosted URL. A bare issue number is not a source identity.

## Publication preflight

Before the first hosted mutation:

1. resolve the exact `owner/repository` target for every accepted candidate;
2. verify the SE workflow contract and hosted Idea shape;
3. inspect open issues for exact and near title matches, then inspect candidate
   bodies, state, and native Issue Type;
4. reuse only an exact equivalent with the same substantive proposal, owner,
   compatible open state, and absent native Issue Type;
5. ask for a decision on a materially different collision; do not silently
   edit, reopen, or remove an Issue Type.

The `Idea:` title prefix and canonical body are the complete semantic hosted
shape.

## Handoff and verification

Translate each operation into the G workflow's normalized issue lifecycle
boundary. Keep caller-owned fields such as `run_mode`, candidate selection,
and publication policy outside that handoff. The handoff must identify one
exact target and one issue operation at a time.

Use the reconciled transient capture bundle as the only publication input. It
contains the selected candidate, final body, target owner, preflight evidence,
and publication order. Do not reconstruct a candidate from stale transcript
context after publication starts. The bundle is discarded after the terminal
report; only the explicitly published issue is durable.

Publish in checkpoints:

1. reconcile the exact target and current collision state;
2. apply the shared hosted-content safety gate to the exact final title and body
   immediately before the write;
3. create one missing Idea with that verified title and body;
4. read the result back before processing the next candidate;
5. verify title, open state, body, and absent native Issue Type;
6. record the durable qualified ref.

Do not set a native Issue Type or apply workflow-state metadata. Open questions
in an Idea body do not imply a workflow state.

## Failure and recovery

If an operation returns an error, no result, or ambiguous acknowledgement, stop
the batch and inspect the current hosted issue state. Reuse a verified issue
that the attempted operation actually created. Retry only an issue or
assignment proven absent. Never replay the complete batch from the original
candidate list.

On partial publication, report verified created and reused refs, the exact
missing work, and the safe resume point. Clean up transient composition
artifacts through the G workflow's own recovery boundary.
