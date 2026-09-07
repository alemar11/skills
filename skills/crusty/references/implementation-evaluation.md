# Implementation Evaluation

Read this reference only when the user explicitly asks Crusty to evaluate an
implementation's correctness, resilience, or test strategy.

## Contract

Inspect code and existing tests; run focused verification when it adds useful
evidence and fits the authorized environment. Ordinary disposable build
artifacts do not require a separate copy. Do not run tests against shared or
production state without authorization. Report failures without repairing them
during the critique; follow an explicit fix request after presenting findings.

Do not execute destructive, unbounded, or host-endangering stress and resource
exhaustion scenarios. Recommend bounded and isolated verification for those
risks instead.

## Workflow

1. Establish the evaluation target:
   - identify the implementation, diff, or behavior in scope;
   - recover its intended contracts, acceptance criteria, compatibility
     constraints, and important invariants from code and project evidence;
   - identify the existing tests and verification commands closest to that
     behavior.
2. Establish the available evidence:
   - inspect relevant code paths, tests, fixtures, mocks, schemas, and failure
     handling;
   - run focused existing tests only when they are safe, relevant, and allowed
     by the current request and environment;
   - report failures as evidence without repairing them, and distinguish likely
     implementation defects from obsolete tests, flakes, environmental
     failures, and unrelated pre-existing failures.
3. Build a risk inventory against the actual behavior. Consider:
   - boundary and empty values;
   - malformed, partial, contradictory, and unexpectedly large inputs;
   - invalid state transitions, stale state, corruption, and recovery;
   - concurrency, reentrancy, cancellation, ordering, and lifecycle hazards;
   - dependency failures, timeouts, retries, partial success, and rollback;
   - bounded resource pressure and cleanup;
   - undocumented assumptions about ownership, identity, persistence, time,
     ordering, platform behavior, and external services.
4. Evaluate test quality by protected behavior rather than raw test count or
   line coverage:
   - prefer stable assertions on meaningful observable outcomes;
   - identify distinct behaviors with no useful regression signal;
   - flag weak assertions, excessive mocking, implementation coupling,
     nondeterminism, and tests that cannot fail for the intended reason;
   - flag likely duplication, but recommend removal or consolidation only when
     equivalent behavioral protection can be demonstrated.
5. For every material finding, provide:
   - the concrete failure mode and affected behavior;
   - direct evidence from the implementation, tests, or verification output;
   - impact, likelihood, and confidence;
   - the smallest useful test or other verification technique;
   - whether the correction is required or optional.
6. For a confirmed defect, recommend adding the smallest permanent regression
   test that reproduces it before fixing the root cause. Do not add the test or
   perform the fix as Crusty.
7. State the residual risks, evidence limitations, and what further proof would
   materially increase confidence. Never claim exhaustive or comprehensive
   coverage without concrete evidence.

Use the cheapest verification technique that can expose the risk. Do not force
concurrency, resource pressure, fault injection, property testing, fuzzing, or
integration behavior into unit tests when another test layer is the meaningful
one.

## Output

Use this specialized output instead of the general output shape in `SKILL.md`:

- a concise verdict on the implementation and its verification quality;
- prioritized confirmed defects and risky assumptions;
- material test gaps with the recommended verification and priority;
- weak, fragile, or redundant existing tests and the reason for the judgment;
- required corrections separated from optional improvements;
- commands run and relevant results;
- residual risks and missing evidence.

Omit empty sections. Keep recommendations concrete enough for a separate
implementation workflow to apply without making Crusty responsible for the
changes.
