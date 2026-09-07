# GitHub Issues Maintenance

This skill owns issue lifecycle, metadata classification, and read-only taxonomy
proposals. Keep exact operation mechanics in `references/lifecycle.md` and
`references/workflows.md`, classification in `references/metadata-classification.md`,
and result registries in `references/states.md`. Shared invocation fields remain
plugin-owned.

Use the shared attachment artifact; do not create a second issue transport.
Preserve classification's additive metadata scope and taxonomy's no-write
boundary when changing lifecycle behavior. Validate issue workflow edits with
read-only or dry-run fixtures before any authorized remote write; shared CLI
changes follow `projects/g/AGENTS.md`.
