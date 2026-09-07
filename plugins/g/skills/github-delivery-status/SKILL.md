---
name: github-delivery-status
description: "Inspect one pull request’s exact-head checks, reviews, merge policy, and delivery readiness read-only."
---

# GitHub Delivery Status

Inspect one exact repository and PR through authenticated `gh`. Read
[Network execution](../../references/network-execution.md) and the
[gh preflight](../../references/gh-dependency-preflight.md) before provider
access. This workflow does not require the G executable.

For collection, read [workflows.md](references/workflows.md); for readiness
interpretation, read [states.md](references/states.md). Require the caller's
expected full HEAD SHA when inspecting a bound candidate; general inspection
may use the current HEAD. Never reuse evidence from another HEAD.

Report the PR URL and full observed HEAD, expected-head comparison when
applicable, canonical disposition and attribution, material blockers or
pending gates, and unavailable or incomplete evidence. Include provider-native
values, relevant check links, review/thread findings, policy attribution,
automation observations, and closing issues where they explain the result.
Use concise evidence prose or a table, not a fixed JSON envelope.

This skill is read-only. Readiness does not authorize merging, bypassing
protections, updating branches, changing auto-merge or queue membership,
requesting reviews, resolving threads, rerunning CI, or editing hosted content.
Composing workflows own acceptance, implementation, review, and release policy.
