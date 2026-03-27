---
name: swift-api-design
description: Design or review Swift APIs using the official Swift API Design Guidelines, with focus on naming, argument labels, documentation comments, side effects, and call-site clarity.
---

# Swift API Design

## Goal

Design or review Swift APIs so they feel native to the language and are clear at the call site.

This skill bundles a local reference of the official Swift API Design Guidelines, plus shorter navigation references:
- https://swift.org/documentation/api-design-guidelines/
- https://github.com/swiftlang/swift-org-website/blob/main/documentation/api-design-guidelines/index.md

## Trigger rules

- Use when the user asks to design, rename, review, or refactor a Swift API.
- Use when the task involves Swift method names, argument labels, initializer shape, protocol/type naming, documentation comments, or mutating/nonmutating pairs.
- Use when comparing multiple Swift API shapes and choosing the most idiomatic one.
- Do not use for general Swift implementation work unless the API surface itself is part of the request.

## Quick workflow

1. Start from the call site.
   - Sketch 2-3 realistic usages before judging the declaration.
   - Optimize for clarity at the point of use, not for declaration cleverness.
2. Classify the API surface.
   - Is it a type, protocol, property, method, initializer, factory, boolean query, mutating operation, or nonmutating transformation?
   - Apply the naming pattern that matches that role before tweaking labels.
3. Audit the signature.
   - Check the base name, first argument label, remaining labels, default arguments, parameter names, and whether the API reads fluently in code.
4. Audit semantics.
   - Side-effecting operations should read like verb phrases.
   - Nonmutating queries and values should read like noun phrases or assertions.
   - Mutating/nonmutating pairs should use consistent naming.
5. Write or review the doc comment.
   - Every public declaration should have a concise summary.
   - If the API is hard to explain simply, redesign it before polishing it.
6. Present recommendations with evidence.
   - Show before/after call sites.
   - Explain the change in terms of clarity, fluency, and guideline fit.

## References

- Read [official-guidelines.md](references/official-guidelines.md) when you need the local reference of the official Swift API Design Guidelines, including the good/bad examples.
- Read [core-principles.md](references/core-principles.md) first for the high-level design rules that should drive every decision.
- Read [naming-and-signatures.md](references/naming-and-signatures.md) when choosing names, argument labels, defaults, or overload shapes.
- Read [review-checklist.md](references/review-checklist.md) when auditing an existing API or summarizing recommended changes.

## Default review rubric

When reviewing a Swift API, check in this order:
- clarity at the call site
- correct noun/verb/assertion shape
- argument-label fluency
- side-effect signaling
- mutating/nonmutating consistency
- terminology and abbreviation quality
- documentation comment quality
- overload ambiguity and default-argument ergonomics

## Output shape

Prefer responses that include:
- the recommended signature
- 2-3 example call sites
- the specific guideline(s) motivating the change
- any tradeoff or ambiguity that remains
