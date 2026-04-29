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

## Current Local Layout

- Treat `plugins/tanstack/` as a macro-area plugin surface.
- `tanstack-query`, `tanstack-router`, `tanstack-start`, `tanstack-cli`, and
  `tanstack-integration` are the stable bundled entrypoints.
- `tanstack-router`, `tanstack-start`, and `tanstack-cli` own dense workflow
  routing through local `references/*.md` files.
- Focused bundled skills remain valid direct-trigger surfaces; do not replace
  them with reference files only.
- When upstream coverage expands, prefer:
  - refreshing umbrella `references/*.md` routing first
  - then adding, removing, or renaming focused bundled skills only when the
    workflow boundary truly changed

## Execution Flow (Mandatory Order)

1. `inventory-local-surface`: inspect `plugins/tanstack/.codex-plugin/plugin.json`,
   bundled `SKILL.md` files, umbrella `references/*.md` files, `agents/openai.yaml`,
   and coupled repo docs such as `README.md` to capture the current local claims.
2. `review-upstream-coverage`: check the current TanStack Intent registry and the
   relevant official package pages on `tanstack.com` for first-party Intent
   coverage relevant to the local plugin, especially Router, Start, CLI, and any
   newly added Query-related surface.
3. `compare-coverage`: identify whether new upstream first-party Intent skills
   materially change the correct local guidance, such as plugin scope wording,
   umbrella routing, verification fallbacks, or which TanStack packages should be
   called out.
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

## Upstream Fetch Order

Use TanStack-owned public sources first and prefer `latest` documentation
surfaces when they exist.

1. TanStack Intent registry index:
   - `https://tanstack.com/intent/registry`
   - Use this to discover which first-party packages currently ship skills.
2. TanStack Intent package pages:
   - `https://tanstack.com/intent/registry/%40tanstack__router-core`
   - `https://tanstack.com/intent/registry/%40tanstack__router-plugin`
   - `https://tanstack.com/intent/registry/%40tanstack__react-start`
   - `https://tanstack.com/intent/registry/%40tanstack__start-client-core`
   - `https://tanstack.com/intent/registry/%40tanstack__start-server-core`
   - `https://tanstack.com/intent/registry/%40tanstack__cli`
   - Use package pages and their skill pages to capture the current skill tree,
     current wording, and any version notes surfaced in the page content.
3. TanStack Intent docs:
   - `https://tanstack.com/intent/latest/docs`
   - `https://tanstack.com/intent/latest/docs/registry`
   - Use these to confirm current Intent packaging, discovery, validation, and
     staleness mechanics.
4. Product docs on `latest` endpoints:
   - `https://tanstack.com/router/latest`
   - `https://tanstack.com/start/latest/docs`
   - `https://tanstack.com/cli/latest/docs`
   - Use these to refresh umbrella guidance and `references/*.md` routing when
     the official docs reorganize task boundaries or terminology.
5. Fallback for ambiguous package-version questions:
   - Use npm package metadata only when the TanStack registry page or product
     docs do not make the currently published package version clear enough for
     the maintainer task.

## Layout Refresh Rules

- Keep macro-area workflows in umbrella skills plus `references/*.md`.
- Use focused bundled skills for direct-triggerable narrow tasks only.
- When a new official TanStack domain appears:
  - add it to the nearest umbrella `references/README.md`
  - decide whether it deserves a new focused bundled skill or belongs inside an
    existing macro guide
- When an official domain disappears or merges:
  - update umbrella `references/*.md` first
  - remove or merge focused bundled skills only if the old trigger boundary is
    now actively misleading
- Keep `README.md`, `.codex-plugin/plugin.json`, and umbrella `SKILL.md` files
  aligned on whether the plugin is describing macro areas, focused sub-skills,
  or both

## Guardrails

- Use TanStack-owned public sources first for the upstream coverage check.
- Do not assume a missing Query Intent surface is permanent; state it as the
  current observed registry state only.
- Do not broaden `plugins/tanstack/` beyond its actual framework coverage
  without a real upstream and local-scope reason.
- Keep local wording aligned with what the plugin actually bundles today, not
  with possible future TanStack Intent expansion.
- Do not collapse focused bundled skills into reference files only; keep
  discoverable bundled entrypoints where the plugin already owns a direct
  trigger surface.

## Deliverable

Report:

- Which upstream TanStack Intent surfaces were checked
- Which TanStack `latest` docs surfaces were checked
- Whether new first-party coverage was found
- Which local files changed, if any
- Which checks were executed
- Why each persistent change was needed
