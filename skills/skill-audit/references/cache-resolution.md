# Cached Plugin Skill Resolution

Use this workflow whenever a named target path lives under
`~/.codex/plugins/cache/...` or when a bundled plugin skill's editable owner is
unclear.

## Rules

- If a named skill path lives under `~/.codex/plugins/cache/...`, treat it as
  an installed snapshot.
- Do not assume the cache path is the editable source of truth.
- Resolve the owning plugin through visible workspace discovery surfaces when
  possible.

## Resolution Order

1. Parse identity from the cache path.
   - developer
   - plugin
   - version
   - bundled skill path
2. Check visible workspace plugin discovery surfaces:
   - `.agents/plugins/marketplace.json`
   - the owning plugin package's `.codex-plugin/plugin.json`
3. If the plugin is registered locally, resolve the editable workspace source
   and compare the cache copy only as evidence.
4. If no workspace mapping is available, report that:
   - the cache path was resolved to plugin identity
   - the editable source was not confirmed

## What To Report

- cache snapshot path
- resolved plugin identity
- confirmed editable workspace source when found
- whether the cache and workspace copies appear aligned when that comparison is
  useful
- whether the inability to resolve an editable owner limits the confidence of
  the audit

## Failure Shields

- Never mutate `~/.codex/plugins/cache/...`.
- Never present a cache path as the editable source of truth.
- Do not guess the workspace owner when no visible mapping exists.
