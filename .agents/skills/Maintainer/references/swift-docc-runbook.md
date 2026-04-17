# Swift-DocC Runbook

This runbook is the canonical procedure for refreshing the bundled `swift-docc`
asset tree and maintaining the local fast-path reference layer from within the
`Maintainer` project skill.

## Hard Rule: Swift-DocC Runtime Skill Unawareness
- The runtime `swift-docc` skill must remain unaware of refresh mechanics.
- Keep refresh scripts, validation logic, and maintainer routing in this
  `Maintainer` skill.
- The runtime `swift-docc` package should only ship the bundled assets,
  manifest, `references/*.md`, and generated outputs such as `source-map.md`.

## Scope
- Refresh `skills/swift-docc/assets/DocCDocumentation.docc/` from `swiftlang/swift-docc`.
- Refresh `skills/swift-docc/assets/manifest.json` and `skills/swift-docc/references/source-map.md`.
- Review and update `skills/swift-docc/references/*.md` only when local fast-path
  coverage or link integrity has materially drifted.
- Keep the procedure and maintainer tooling under `.agents/skills/Maintainer/`.

## Temporary Data Policy
- Use the refresh script's temporary directory handling for upstream downloads.
- Use `.cache/` only for ad hoc scratch work or investigation notes.
- Do not leave ad hoc temporary files in `skills/swift-docc/`.

## Content Rules
- `assets/DocCDocumentation.docc` is the bundled source of truth.
- `references/*.md` are fast paths into that source of truth, not a second
  knowledge base.
- Prefer thin workflow summaries and local asset links over duplicated prose.
- Update reference pages only for meaningful reasons:
  - a common user workflow has no direct fast path
  - a local summary link is broken or stale
  - upstream structure changed enough that routing should change
- Do not churn reference pages for wording polish alone.

## Tooling
- Refresh script: `./.agents/skills/Maintainer/scripts/swift_docc_refresh.py`
- Check script: `./.agents/skills/Maintainer/scripts/swift_docc_check.py`

## Prerequisites
- Run commands from repository root.
- Required tools: `python3`, network access for upstream staleness checks and refreshes.

## Refresh Flow
1. Check bundled asset freshness:
   - `python3 .agents/skills/Maintainer/scripts/swift_docc_refresh.py --check-stale`
2. If stale, refresh the bundle and regenerate `source-map.md`:
   - `python3 .agents/skills/Maintainer/scripts/swift_docc_refresh.py`
3. Validate the runtime package shape and link integrity:
   - `python3 .agents/skills/Maintainer/scripts/swift_docc_check.py`
4. Review fast-path coverage manually:
   - `skills/swift-docc/references/README.md`
   - `skills/swift-docc/references/source-map.md`
   - workflow pages such as `document-a-swift-package.md`, `document-public-symbols.md`, `document-async-and-stateful-apis.md`, `add-a-docc-catalog.md`, `preview-and-publish.md`, and `tutorial-workflow.md`
5. If fast-path edits are needed, update those markdown files and rerun:
   - `python3 .agents/skills/Maintainer/scripts/swift_docc_refresh.py`
   - `python3 .agents/skills/Maintainer/scripts/swift_docc_check.py`
6. Ensure runtime docs stay clean:
   - no `skills/swift-docc/scripts/` directory
   - no maintainer-routing references in `skills/swift-docc/SKILL.md`
   - no maintainer commands in `skills/swift-docc/references/README.md`

## Validation
- `python3 -m py_compile .agents/skills/Maintainer/scripts/swift_docc_refresh.py .agents/skills/Maintainer/scripts/swift_docc_check.py`
- `python3 .agents/skills/Maintainer/scripts/swift_docc_refresh.py --check-stale`
- `python3 .agents/skills/Maintainer/scripts/swift_docc_check.py`
- `git diff --check`

## Notes
- `swift_docc_refresh.py` only downloads a new upstream DocC tree when the
  manifest is stale or a refresh is forced; otherwise it keeps the current
  bundle and regenerates `source-map.md` from the current catalog.
- `swift_docc_check.py` is the architectural guardrail: it verifies the runtime
  skill stays free of maintainer internals and that local reference links remain valid.
