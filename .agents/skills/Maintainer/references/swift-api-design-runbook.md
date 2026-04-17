# Swift API Design Runbook

This runbook is the canonical procedure for refreshing the bundled
`swift-api-design` source asset and maintaining the thin local reference layer
from within the `Maintainer` project skill.

## Hard Rule: Swift API Design Runtime Skill Unawareness

- The runtime `swift-api-design` skill must remain unaware of refresh mechanics.
- Keep refresh scripts, validation logic, and maintainer routing in this
  `Maintainer` skill.
- The runtime `swift-api-design` package should only ship the bundled asset,
  manifest, and `references/*.md`.

## Scope

- Refresh `skills/swift-api-design/assets/api-design-guidelines.md` from
  `swiftlang/swift-org-website`.
- Refresh `skills/swift-api-design/assets/manifest.json`.
- Review and update `skills/swift-api-design/references/*.md` only when local routing
  or link integrity has materially drifted.
- Keep the procedure and maintainer tooling under
  `.agents/skills/Maintainer/`.

## Source-Of-Truth Rule

- Current upstream source of truth is
  `swiftlang/swift-org-website/documentation/api-design-guidelines/index.md`.
- Do not switch the refresh source to `swiftlang/docs` unless that repository
  becomes the substantive source of the live Swift.org page rather than a
  migration target or stub.

## Content Rules

- `assets/api-design-guidelines.md` is the bundled source of truth.
- `references/*.md` are fast paths into that source of truth, not a second
  full copy of the guidelines.
- Prefer short workflow summaries and local asset links over duplicated prose.
- Update reference pages only for meaningful reasons:
  - a common user workflow has no direct fast path
  - a local summary link is broken or stale
  - upstream structure changed enough that routing should change
- Do not churn reference pages for wording polish alone.

## Tooling

- Refresh script:
  `./.agents/skills/Maintainer/scripts/swift_api_design_refresh.py`
- Check script:
  `./.agents/skills/Maintainer/scripts/swift_api_design_check.py`

## Prerequisites

- Run commands from repository root.
- Required tools: `python3`, network access for upstream staleness checks and
  refreshes.

## Refresh Flow

1. Check bundled asset freshness:
   - `python3 .agents/skills/Maintainer/scripts/swift_api_design_refresh.py --check-stale`
2. If stale, refresh the bundle:
   - `python3 .agents/skills/Maintainer/scripts/swift_api_design_refresh.py`
3. Validate the runtime package shape and link integrity:
   - `python3 .agents/skills/Maintainer/scripts/swift_api_design_check.py`
4. Review fast-path coverage manually:
   - `skills/swift-api-design/references/README.md`
   - `skills/swift-api-design/references/official-guidelines.md`
   - `skills/swift-api-design/references/core-principles.md`
   - `skills/swift-api-design/references/naming-and-signatures.md`
   - `skills/swift-api-design/references/common-api-shaping-patterns.md`
   - `skills/swift-api-design/references/review-checklist.md`
5. If curated-reference edits are needed, update those markdown files and rerun:
   - `python3 .agents/skills/Maintainer/scripts/swift_api_design_refresh.py`
   - `python3 .agents/skills/Maintainer/scripts/swift_api_design_check.py`
6. Ensure runtime docs stay clean:
   - no `skills/swift-api-design/scripts/` directory
   - no maintainer-routing references in `skills/swift-api-design/SKILL.md`
   - no maintainer commands in `skills/swift-api-design/references/README.md`

## Validation

- `python3 -m py_compile .agents/skills/Maintainer/scripts/swift_api_design_refresh.py .agents/skills/Maintainer/scripts/swift_api_design_check.py`
- `python3 .agents/skills/Maintainer/scripts/swift_api_design_refresh.py --check-stale`
- `python3 .agents/skills/Maintainer/scripts/swift_api_design_check.py`
- `git diff --check`

## Notes

- `swift_api_design_refresh.py` only downloads a new upstream file when the
  manifest is stale or a refresh is forced; otherwise it leaves the current
  bundle untouched.
- `swift_api_design_check.py` is the architectural guardrail: it verifies the
  runtime skill stays free of maintainer internals and that local reference
  links remain valid.
