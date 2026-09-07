# Hosted Codex Review

Read for inspection, requests, waits, and resume. [states.md](states.md) owns
result meanings. G owns provider parsing, explicit request identity, receipt
recovery, bounded waiting, and terminal evidence. Use its focused review
operations rather than implementing another provider adapter or waiter.

## Select the exact request

Resolve the repository/PR, expected full HEAD (the current HEAD when the caller
has not bound it), current ready state, and available explicit request lineage.

- Reuse a verified terminal explicit review for this target, whether clean or
  findings, and return it without another request or wait.
- Resume a matching pending explicit request through G with its original receipt
  and deadline. Do not repost merely because Codex has not answered yet.
- When no applicable explicit lineage exists, reconcile prior uncertain effects,
  then request review and wait. Automatic/ready-triggered reviews or results for
  an older HEAD do not satisfy this skill's explicit current-target contract.

Inspect-only scope overrides request-and-wait and reports missing evidence as a
gap. Missing local receipt output alone never proves no request exists. Recover
an existing request through G when supported; if its identity/correlation cannot
be established, report blocked rather than duplicating the request.

Before a new request or wait, verify ready state and unchanged expected full HEAD.
A draft returns deferred to the caller; this skill never marks it ready. Use G
to post `@codex review` bound to the exact commit, including the initial review.
No local candidate review is required by this skill. Delivery supplies its own
local gate before invoking it.

Use one request identity per intended cycle and preserve G's complete receipt.
Reconcile uncertain request effects before any retry. Only an explicitly requested
fresh cycle may replace a verified existing same-target lineage. If the expected
HEAD changes during the run, return the drift to the caller; never silently
follow a moving branch or consume old evidence for the new HEAD. A subsequent
invocation bound to a newly published HEAD may request that new target.

## Bounded observation and return

Wait through G until terminal review evidence, caller stop, a blocking failure,
or the original deadline. Keep the existing total 30-minute limit per explicit
lineage. Resume preserves that deadline; never segment or extend it. If the
deadline is exhausted, read-only reconciliation may recover a result that has
since arrived, but it cannot start a fresh wait window or replacement request.
Return pending when the review remains unanswered at timeout or caller stop.
Do not schedule an automation or spawn a monitoring task/subagent.

Return completed only when G establishes a terminal provider verdict for the
exact selected request and expected HEAD. Clean and findings both end monitoring.
Return the findings and links without proposing or performing repair batches,
rebuttals, replies, or resolutions. Zero unresolved threads, absence of comments,
generic not-requested, automatic review, stale results, and ambiguous correlation
cannot stand in for terminal evidence. G owns recognition of supported clean
reactions and other provider result forms; do not infer completion yourself.

Infrastructure failures or unreconciled effects return blocked with the exact
available receipt and evidence. Preserve provider verdict separately from the
monitoring result. No CI check, local code review, or delivery acceptance gate
is part of this monitor, and no workflow position is stored in a new ledger.
