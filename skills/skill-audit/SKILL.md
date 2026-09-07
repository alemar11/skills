---
name: skill-audit
description: Audit skill or plugin instructions and usage evidence read-only. Use only when explicitly invoked as $skill-audit.
---

# Skill Audit

Audit the requested installed skills or plugins. Resolve editable owners;
installed caches, memory, and session archives are evidence, not edit targets.
For a portfolio request, include the requested scope, including this skill
when it falls within that scope.

An audit alone is read-only. If the user requests fixes, complete the findings
and proceed under that authorization using the owning maintenance workflow;
use skill-creator for substantial skill reshapes. Never steer or mutate a
monitored task without separate authorization.

## Evidence routes

Read [states](references/states.md) to classify target and evidence. Resolve
unclear cache paths with [cache resolution](references/cache-resolution.md).
Then select the target overlay: [standalone skills](references/standalone-skills.md),
[plugins](references/plugins.md), or [bundled skills](references/bundled-plugin-skills.md).

- Static wording, triggers, or ownership: inspect target instructions and
  relevant consumers directly. No history helper is needed.
- Prior runtime behavior: [historical evidence](references/historical-evidence.md).
- Current task monitoring: [live monitoring](references/live-monitoring.md).
  Do not substitute archives for unavailable live evidence.
- Portfolio overlap or cost: [portfolio hygiene](references/portfolio-hygiene.md).
- Instruction density: [writing review](references/writing-style-review.md).

Use `scripts/session-evidence` only for invocation or behavioral history;
`scripts/portfolio-health` only for inventory, budget, or usage questions.
Neither proves a runtime defect without representative evidence.

Return the applicable [output format](references/output-format.md), scaled to
the findings. Distinguish static concerns from observed failures and report
missing evidence. Recommend new surfaces only when existing owners cannot
serve the need.
