# Feature Planner Task Profile

This profile owns the one required application-task launch for `se:spec`.
It is intentionally separate from Delivery Features orchestration and repository-claim
handling.

```yaml
task_profile: feature-planner
role: planner
model: gpt-5.6-sol
reasoning: high
topology: single-planner-task
title_template: "📚 Plan Feature · <outcome>"
execution: direct-local-project
```

Resolve and pass `model` and `reasoning` explicitly when creating or resuming
the planner. Do not rely on ambient inheritance. These values are required
request inputs, not a post-effect attestation protocol: retain what was
requested, but do not require the planner to read back or self-certify its
effective profile.

Explicit `se:spec` invocation authorizes exactly one visible planner task.
Request the deterministic title when the runtime supports it, but never gate
planning on title observation or correction. Run in the caller-selected direct
local project checkout without a worktree or fork. The planner may inspect
every repository explicitly in scope; application project metadata does not
establish repository identity or constrain the spec.

An accepted creation or resume receipt with a stable task identity starts the
planner. Its first turn begins `intake` and performs role work immediately. Do
not request an `assigned_task_bootstrap`, effective-profile comparison,
execution-target self-check, goal, title reconciliation, or a second planner.

When the task effect is ambiguous, inspect that same attempt once. Resume the
observed identity when it exists. Create another planner only after
authoritative evidence proves the original effect did not apply. If creation
is rejected or remains ambiguous, report the launch blocker without beginning
publication.

Before optional delegation, read the selected role in
[subagents.md](../../../references/subagents.md): `evidence-researcher` for
bounded evidence gathering or `spec-reviewer` for the complete draft review.
Use that role's profile instead of inheriting the planner's settings. Helpers
remain subordinate and never become required application tasks. Keep their
assignments within the planner's admitted scope, reconcile every created helper,
and assess its findings before continuing. When delegation is unavailable or
prohibited, fall back to serial planner work.
