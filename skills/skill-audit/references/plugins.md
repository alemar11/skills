# Plugin Audits

Use this workflow for plugin package audits.

Treat the plugin package as a first-class install surface. Audit the package
itself, not just its bundled skills.

## Resolution

- Start from visible plugin discovery surfaces:
  - `.agents/plugins/marketplace.json`
  - `plugins/<name>/`
- If the user names a specific plugin, resolve that plugin first.
- In default full-scope mode, prioritize only the plugins relevant to the
  current workflow instead of auditing every local plugin mechanically.

## What To Inspect

- `.codex-plugin/plugin.json`
- `.agents/plugins/marketplace.json`
- bundled `skills/*`
- shared `scripts/*`
- `projects/*` when present
- assets and directly coupled docs as needed
- cache copies under `~/.codex/plugins/cache/...` only as a verification
  surface

## What To Evaluate

- current role in the repo or workflow
- whether the plugin package is still the right install surface
- whether `.codex-plugin/plugin.json` is current and coherent
- whether `.agents/plugins/marketplace.json` matches the plugin package
- whether the bundled skill set is coherent, overlapping, or missing an obvious
  owner boundary
- whether shared `scripts/*` and `projects/*` still follow the documented
  runtime versus maintenance split
- whether assets and repo-relative paths are valid from the plugin root
- whether versioning and cache-awareness rules are reflected in the package
- whether gaps belong in the plugin package, a bundled skill, repo docs, or
  `Maintainer`

## Evidence Workflow

1. Search the memory index first.
   - Search `MEMORY.md` with repo name, repo basename, current `cwd`, plugin
     names, manifests, runtime scripts, and package files.
2. Open targeted rollout summaries.
   - Prefer summaries whose filenames, `cwd`, or `rollout_path` match the
     current project or plugin names.
3. Check cheap maintenance signals before raw sessions.
   - Use `git log -- <plugin-dir>` and compare repo docs against the package.
4. Use raw sessions when package behavior is in question, and as a fallback
   otherwise.
   - Search by plugin name, `.codex-plugin/plugin.json`, marketplace path,
     exact `cwd`, thread ID, or specific failure text.

## Cache Rules

- Treat `~/.codex/plugins/cache/...` as verification only.
- Use cache inspection to answer questions such as:
  - version drift
  - stale installed packaging
  - missing runtime artifacts
  - asset or manifest shipping gaps
- Never route fixes or edits to the cache path.

## Ownership Guidance

- Put findings on `plugin` when the issue is in the package manifest,
  marketplace registration, bundled-skill boundaries, runtime package layout,
  assets, or version/cache behavior.
- Put findings on `bundled plugin skill` when the issue is isolated to one
  bundled skill contract.
- Put findings on `docs` when the package is fine but the repo guidance is the
  real source of drift.
