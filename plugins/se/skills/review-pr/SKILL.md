---
name: review-pr
description: "Request or resume a hosted Codex PR review, wait for its result, and report it to the caller."
---

# Review PR

Follow the shared [execution scope](../../references/execution-scope.md) for
standalone and composed invocation.

Obtain the hosted Codex review result for one exact GitHub PR and HEAD. Run in
the calling session/task, standalone or composed by Delivery, with the same
behavior in both cases. Do not create tasks or subagents. No spec, local checkout,
implementation context, candidate-review receipt, or repair budget is required.

## Scope and authority

Default invocation authorizes the needed explicit `@codex review` request and
bounded wait without another confirmation. Reuse a completed current-target
review, resume a matching pending request, or request and wait when no applicable
explicit lineage exists and prior effects are reconciled. Both clean and findings
are completed provider results; findings do not trigger a repair or another
unchanged-HEAD request.

An explicit audit-only, inspect-only, or read-only request reports existing
evidence without posting or starting a wait. The only hosted write this skill
owns is the requested Codex review mention. It does not change draft state,
implement fixes, rebut findings, reply to or resolve threads, publish commits,
inspect CI or merge policy, update planning progress, or decide delivery acceptance.
The calling task owns those follow-up actions under its own authority.

Read [states.md](references/states.md) for result meanings and
[hosted-review.md](references/hosted-review.md) before inspection, requests,
waiting or resume. Apply the [G preflight](../../references/codex-dependency-preflight.md)
before hosted access and [hosted-content safety](../../references/hosted-content-safety.md)
immediately before a review-request write.

## Result and caller handoff

Return the PR URL, expected and observed full HEAD, exact explicit request
identity and unchanged G receipt/deadline, `review_pr_result`, provider verdict,
findings with provider links when present, and any pending state or blocker.
Report the provider result faithfully; do not adjudicate findings or turn
review completion into acceptance of the code. A clean response is review
evidence, not proof of CI, spec completion, or merge readiness.

Delivery supplies its exact published ready candidate and any existing G receipt.
Return the result directly to that coordinator. Delivery alone decides whether
to repair, rebut, defer, or accept, manages agents and budgets, and invokes this
skill again when the next published candidate needs hosted review. Standalone
invocation reports the same evidence directly to the user in the calling task.

## Skill Dependencies

Installed `g@alemar11` supplies `g:github-review-threads` for exact review requests,
inspection, bounded waiting, and reconciliation. Compose only those operations;
its feedback-to-code and reply/resolution branches are outside this skill's scope.
Never install, refresh, or substitute the dependency.
