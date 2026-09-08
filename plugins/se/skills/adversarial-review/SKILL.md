---
name: adversarial-review
description: "Independently review a fixed software change read-only when explicitly requested or composed by another workflow."
---

# Adversarial Review

Follow the shared [execution scope](../../references/execution-scope.md) for
standalone and composed invocation.

Pressure-test the selected software change as a skeptical shipment reviewer.
Review the complete supplied change and its relevant code paths, then return
evidence-backed findings or a clean result. This skill is read-only: it never
edits the target, fixes findings, performs Git mutations, or publishes hosted
content.

## Review handoff

Use the caller's verified target, base, repository instructions, and optional
focus areas. When a composed workflow supplies an immutable snapshot, preserve
its exact identity and review the whole delta rather than only the latest turn
or commit. Keep the review independent from the implementation conversation
when the caller requires independent review. The caller arranges that execution
context; this skill never launches another reviewer. If implementation context
is already visible, disclose that limitation rather than claiming independence.
This applies equally to standalone and composed review.

Inspect risks supported by the change, including correctness, authorization,
state integrity, concurrency, compatibility, and failure recovery. Do not
manufacture findings to satisfy the posture.

Review for unnecessary complexity, avoidable duplication, and missed reuse of
established repository patterns. Recommend simplifications only when they
materially improve correctness, readability, or maintenance. Prefer the simplest
design that satisfies the requirements; do not flag stylistic preferences or
introduce abstractions solely to eliminate repetition.

## Result

Return one disposition selected by the calling workflow, normally `clean`,
`findings`, or `indeterminate`, plus severity-ordered findings. Each finding
identifies the concrete failure mode or maintenance cost, affected file and tight
line range when available, supporting evidence, confidence, and a focused
recommendation.
State the reviewed target and any material coverage or execution limitation.

The reviewer never fixes its own findings. A caller may use findings to decide
whether to repair, rebut, defer, or block; a clean result only authorizes the
caller-specific next step.
