# Swift-DocC Refresh Playbook

Use this playbook when asked to refresh bundled Swift-DocC references or review
the `swift-docc` manifest and local fast-path layer.

## Routing Rule
- Keep `swift-docc` runtime behavior authoring-first and unaware of maintainer mechanics.
- Use `references/swift-docc-runbook.md` as the canonical refresh and review procedure.
- This task is a skill-specific refresh workflow; do not silently combine it with
  unrelated maintainer workflows or skill upgrades.

## Execution Flow (Mandatory Order)
1. `syntax-check`: run `python3 -m py_compile` on both Swift-DocC maintainer scripts.
2. `staleness-check`: run `python3 .agents/skills/Maintainer/scripts/swift_docc_refresh.py --check-stale`.
3. `refresh-if-needed`: if the manifest or bundled asset tree is stale, run `python3 .agents/skills/Maintainer/scripts/swift_docc_refresh.py`.
4. `review-fast-paths`: inspect `skills/swift-docc/references/*.md`, especially the workflow pages, async/stateful API routing, local preview guidance, and `source-map.md`, for missing high-frequency layers or stale local links.
5. `integrity-check`: run `python3 .agents/skills/Maintainer/scripts/swift_docc_check.py`.
6. `final-report`: use the release checklist schema and return `PASS (NOOP)` if the bundle was already current and no persistent reference edits were needed.

## Read-only Evaluation Mode
When a read-only verification is requested:
- Run `syntax-check` as-is.
- Run `staleness-check`.
- Run `integrity-check`.
- Do not run the refresh step unless the user explicitly wants tracked-file updates.

## Guardrails
- Do not reintroduce `skills/swift-docc/scripts/` in the runtime skill.
- Do not add `.agents/skills/Maintainer` routing or commands to runtime `swift-docc` docs.
- Treat `assets/DocCDocumentation.docc` as the source of truth and keep `references/*.md` thin, task-oriented routing layers.
- Update fast-path markdown only when there is a meaningful gap, stale local link, or upstream drift that changes routing.

## Deliverable
Report:
- Whether the bundled asset tree was stale
- Whether a refresh occurred
- Which `skills/swift-docc/references/*.md` files changed
- Which checks were executed
- Why each persistent change was needed
