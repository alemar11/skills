# Swift API Design Refresh Playbook

Use this playbook when asked to refresh bundled Swift API Design references or
review the `swift-api-design` manifest and local fast-path layer.

## Routing Rule

- Keep `swift-api-design` runtime behavior design-first and unaware of
  maintainer mechanics.
- Use `references/swift-api-design-runbook.md` as the canonical refresh and
  review procedure.
- This task is a skill-specific refresh workflow; do not silently combine it
  with unrelated maintainer workflows or skill upgrades.

## Execution Flow (Mandatory Order)

1. `syntax-check`: run `python3 -m py_compile` on both Swift API Design
   maintainer scripts.
2. `staleness-check`: run
   `python3 .agents/skills/Maintainer/scripts/swift_api_design_refresh.py --check-stale`.
3. `refresh-if-needed`: if the manifest or bundled source file is stale, run
   `python3 .agents/skills/Maintainer/scripts/swift_api_design_refresh.py`.
4. `review-fast-paths`: inspect `skills/swift-api-design/references/*.md`,
   especially `README.md`, `official-guidelines.md`, and the curated summary
   pages such as `common-api-shaping-patterns.md`, for stale local links or
   routing gaps.
5. `integrity-check`: run
   `python3 .agents/skills/Maintainer/scripts/swift_api_design_check.py`.
6. `final-report`: use the release checklist schema and return `PASS (NOOP)` if
   the bundle was already current and no persistent reference edits were needed.

## Read-only Evaluation Mode

When a read-only verification is requested:

- Run `syntax-check` as-is.
- Run `staleness-check`.
- Run `integrity-check`.
- Do not run the refresh step unless the user explicitly wants tracked-file
  updates.

## Guardrails

- Do not add a runtime `skills/swift-api-design/scripts/` directory.
- Do not add `.agents/skills/Maintainer` routing or commands to runtime
  `swift-api-design` docs.
- Treat `skills/swift-api-design/assets/api-design-guidelines.md` as the bundled source
  of truth and keep `references/*.md` thin, task-oriented routing layers.
- Update curated reference pages only when there is a meaningful routing gap,
  stale local link, or upstream drift that changes how the skill should point to
  the bundled source.

## Deliverable

Report:

- Whether the bundled source file was stale
- Whether a refresh occurred
- Which `skills/swift-api-design/references/*.md` files changed
- Which checks were executed
- Why each persistent change was needed
