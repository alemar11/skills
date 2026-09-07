---
name: github-delivery-status
description: "Inspect one pull request’s exact-head checks, reviews, merge policy, and delivery readiness read-only."
---

# GitHub Delivery Status

Before any shell command that may contact GitHub, read and follow
[Network execution](../../references/network-execution.md). Before the first
direct `gh` or shared CLI call, load
[G to gh Runtime Preflight](../../references/gh-dependency-preflight.md).

## Role

Own the provider-facing, read-only delivery-status boundary for one pull
request. Preserve GitHub's original fields and add one conservative normalized
classification. Do not decide caller-owned acceptance, implementation, review,
or release policy.

Resolve `<plugin-root>` as two directories above this `SKILL.md`. From the
plugin root, run:

```sh
scripts/g --json pr delivery-status \
  --repo <owner/repository> \
  --pr <number> \
  --expected-head <full-sha>
```

Require `--expected-head` when a composing workflow binds evidence to one
candidate commit. It is optional for general inspection. Read
[workflows.md](references/workflows.md) for the complete read and recovery
sequence and [states.md](references/states.md) for fields and
classification semantics.

## Output contract

Require the stable JSON envelope and inspect:

- `identity`, including exact-head equality;
- `lifecycle` and draft state;
- `technical_mergeability` and provider `mergeStateStatus`;
- policy rules, checks, review decision, and unresolved threads;
- repository and PR automation state;
- closing issue references;
- `classification.disposition`, attribution, blockers, pending evidence, and
  warnings;
- `completeness` and every unavailable provider surface.

Use the canonical dispositions and completeness rules from `states.md`.
Treat `unknown` and incomplete evidence as non-terminal unless the composing
workflow explicitly owns a narrower evidence rule.

Auto-merge capability, an existing PR auto-merge request, or a merge-queue
entry are observations, not authorization and not blockers by themselves.
Report them under `automation` without enabling, disabling, enqueueing,
dequeueing, or merging anything.

## Safety boundary

This skill has no mutation mode. Never merge, bypass protections, update a
branch, enable or disable auto-merge, enqueue or dequeue a PR, request a review,
resolve a thread, rerun CI, or edit hosted content. Route separately authorized
operations to their focused G owner.

Preserve unfamiliar provider enum values in the evidence and classify them as
`unknown` rather than guessing. A successful read with a non-ready disposition
still exits successfully; transport, authentication, invalid input, and
unreadable provider responses are command failures.
