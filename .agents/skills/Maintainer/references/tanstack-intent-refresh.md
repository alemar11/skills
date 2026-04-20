# TanStack Intent Coverage Refresh Playbook

Use this playbook when asked to review or refresh TanStack Intent coverage for
the local `plugins/tanstack/` plugin.

## Routing Rule

- Treat this as an explicit skill-specific refresh workflow, not as generic
  repo-wide maintenance.
- Review current upstream TanStack Intent coverage before changing local
  verification wording or plugin scope.
- Keep runtime `plugins/tanstack/skills/*/SKILL.md` files free of maintainer
  routing; any maintainer-only review procedure stays here.

## Execution Flow (Mandatory Order)

1. `inventory-local-surface`: inspect `plugins/tanstack/.codex-plugin/plugin.json`,
   bundled `SKILL.md` files, `agents/openai.yaml`, and coupled repo docs such as
   `README.md` to capture the current local claims.
2. `review-upstream-coverage`: check the current TanStack Intent registry and the
   relevant official package pages on `tanstack.com` for first-party Intent
   coverage relevant to the local plugin, especially `@tanstack/react-start`,
   `@tanstack/router-core`, and any newly added Query-related surface.
3. `compare-coverage`: identify whether new upstream first-party Intent skills
   materially change the correct local guidance, such as plugin scope wording,
   verification fallbacks, or which TanStack packages should be called out.
4. `refresh-local-guidance-if-needed`: update local plugin metadata or docs only
   when upstream coverage changes create a real guidance delta. Keep wording
   precise and avoid speculating about unshipped Intent surfaces.
5. `scoped-check`: run a scoped consistency pass across touched TanStack plugin
   files and any directly coupled repo docs.
6. `final-report`: use the release checklist schema and return `PASS (NOOP)` if
   no persistent updates were needed.

## Read-only Evaluation Mode

When the user asks only for a review:

- Run `inventory-local-surface`.
- Run `review-upstream-coverage`.
- Run `compare-coverage`.
- Do not make persistent edits unless the user explicitly asks to refresh or
  update the local plugin guidance.

## Guardrails

- Use TanStack-owned public sources first for the upstream coverage check.
- Do not assume a missing Query Intent surface is permanent; state it as the
  current observed registry state only.
- Do not broaden `plugins/tanstack/` beyond its actual framework coverage
  without a real upstream and local-scope reason.
- Keep local wording aligned with what the plugin actually bundles today, not
  with possible future TanStack Intent expansion.

## Deliverable

Report:

- Which upstream TanStack Intent surfaces were checked
- Whether new first-party coverage was found
- Which local files changed, if any
- Which checks were executed
- Why each persistent change was needed
