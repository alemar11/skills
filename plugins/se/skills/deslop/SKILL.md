---
name: deslop
description: Audit and safely remove low-value repository code. Use only when explicitly invoked by the user.
---

# Deslop

Audit this repository for low-value code: redundant tests, trivial wrappers,
dead abstractions, duplicate helpers, stale comments, and unnecessary ceremony.
Verify each removal is safe, make the smallest cleanup, run focused tests and
lint, and report what changed with evidence. Inspect every major directory
before finishing.

## Coverage and judgment

Inventory the repository's major directories, including source, tests, tooling,
configuration and documentation. Inspect each one's purpose and representative
contents, then trace cleanup candidates through their callers and dependencies.
Track coverage during the audit; report inaccessible or excluded areas and why.
Generated and vendored directories need an ownership check, not manual cleanup.
Do not claim a repository-wide audit is complete with major areas uninspected.

Small code is not automatically low-value. A wrapper may enforce a boundary, an
abstraction may encode a contract, and a simple test may protect a regression.
Remove only demonstrated redundancy or obsolete behavior, not unfamiliar style.
Zero changes is a valid result; retain uncertain candidates and explain material
uncertainty rather than manufacturing cleanup.

## Safe cleanup

Before each removal, verify callers, exports, public contracts, configuration,
and applicable dynamic discovery or registration. No search hits alone do not
prove code is unused. Check behavior and side effects before inlining wrappers
or consolidating helpers; avoid expanding the patch into an architectural rewrite.

For test removals, identify which remaining tests preserve the meaningful
assertions, scenarios and regression coverage. Passing tests alone do not prove
that deleting a test was safe. For comments, verify the statement is stale or
redundant and preserve rationale and non-obvious constraints.

Make the smallest change for each verified finding, preserving observable
behavior and unrelated work. Run the affected tests and lint using repository
commands; include type or build checks when the changed boundary needs them.
Review the final diff for unintended behavior changes. If safety cannot be
established, leave the candidate unchanged; report unavailable checks and their
effect on confidence.

Report changed paths, why each cleanup is safe, the checks run and their results,
and major-directory coverage. Group related removals when they share evidence.
Invocation authorizes local cleanup; commits and publication require user
authorization. Execute in the current task without creating workers.
