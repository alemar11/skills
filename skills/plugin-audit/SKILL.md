---
name: plugin-audit
description: Audit repo-maintained or user-specified Codex plugins using repo evidence, memory, sessions, and current context to plan updates, additions, merges, or disables. Use when a user asks how the plugins maintained in this repo are performing, wants a one-by-one refinement roadmap, asks to audit one or more named plugins, or wants evidence-based recommendations before changing plugin structure.
---

# Plugin Audit

## Overview

Audit repo-maintained plugins before proposing new ones.

Treat plugins maintained in this repository as first-class packages. Audit the
plugin package itself, not just its bundled skills: manifest, marketplace
entry, bundled skill set, shared runtime surfaces, maintenance project, assets,
and version/cache behavior are all in scope.

Default full-scope audits should focus on the plugins relevant to the current
workflow in this repo, not arbitrary installed plugins. Start from current
prompt signals, repo docs, named tasks, `.agents/plugins/marketplace.json`, and
`plugins/*`.

This skill is Codex-dependent. It may use Codex prompt context, Codex memory
artifacts, rollout summaries, and session JSONL when those are available. It
may also inspect Codex plugin cache copies under
`~/.codex/plugins/cache/<developer>/<plugin>/<version>/` as evidence. Treat the
cache as verification only; the editable source of truth for repo-owned plugins
lives in this checkout.

If the user explicitly names one or more plugins, such as `audit plugin
$gitstack` or `audit only $tanstack`, treat those named plugins as the required
audit scope and resolve them before any broader workflow discovery.

## Scope Resolution

- Resolve user-provided scope first.
  - If the user names one or more plugins explicitly, those names define the
    primary audit target set.
  - Accept singular or plural phrasing such as `audit plugin $foo`, `audit
    plugins $foo and $bar`, or `review only $foo`.
- Default full-scope mode is workflow-first and repo-owned.
  - Start from the current workflow in this repo: prompt context, repo docs,
    touched areas, named tasks, `.agents/plugins/marketplace.json`, and related
    repo-owned plugins under `plugins/*`.
- Offer project-maintained scope explicitly.
  - Include repo-maintained plugin surfaces even when they are not obviously in
    the current workflow only when the user explicitly asks for a broader
    repo-plugin pass.
  - Treat plugin cache copies as evidence surfaces, not part of the editable
    portfolio.
- Keep targeted audits targeted.
  - If the user names specific plugins, do not expand to a wider repo scan.
  - Only bring in non-requested plugins when needed to explain overlap, merge
    candidates, or ownership conflicts.
- Be explicit about misses.
  - If a named plugin cannot be resolved, say so clearly.
  - Do not silently substitute a near match or widen the audit scope.

## Audit Order

1. Resolve scope and map the current repo surface.
   Identify whether the user named specific plugins. If yes, treat them as the
   required audit targets and resolve those names first. Otherwise identify the
   repo root and read the most relevant project guidance first, such as
   `AGENTS.md`, `README.md`, roadmap or ledger files, and docs that define
   plugin layout or validation expectations.

2. Resolve repo-owned plugins from the repo discovery surface.
   Start with `.agents/plugins/marketplace.json`, then inspect the corresponding
   plugin package roots under `plugins/<name>/`.
   - For default full-scope mode, prioritize only the plugins relevant to the
     current workflow instead of auditing every plugin mechanically.
   - If the user named specific plugins, inspect only those resolved plugins
     instead of broadening the scan.

3. Audit the plugin package as a package.
   For each serious plugin candidate, inspect:
   - `.codex-plugin/plugin.json`
   - bundled `skills/*`
   - shared `scripts/*`
   - `projects/*` when present
   - assets and directly coupled docs as needed

4. Check cheap maintenance signals before deep history.
   For each plugin you are seriously evaluating, inspect lightweight staleness
   signals before opening raw sessions:
   - `git log -- <plugin-dir>` for maintenance recency
   - repo docs or adjacent docs that may have become the real source of truth
   - whether `.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json`,
     `README.md`, and `AGENTS.md` still describe the same plugin surface

5. Read memory and session evidence.
   Resolve evidence roots in this order:
   - `$CODEX_HOME/...` when `$CODEX_HOME` is set
   - `~/.codex/...`
   - `~/.agents/...`
   Use the first existing path for each category. Missing memory files are not
   blocking.
   Check these locations:
   - `<root>/memories/MEMORY.md`
   - `<root>/memories/rollout_summaries/`
   - `<root>/sessions/`
   Search the memory index first, then open only the 1-3 most relevant rollout
   summaries. Fall back to raw session JSONL only when the summaries are
   missing exact evidence you need.

6. Inspect cache copies only as a verification surface.
   If a repo-owned plugin has a corresponding installed cache copy under
   `~/.codex/plugins/cache/...`, compare it only when useful for:
   - version drift
   - stale installed packaging
   - missing runtime artifacts
   - asset or manifest shipping gaps
   Never treat the cache copy as the editable source of truth.

7. Inspect current live context when available.
   If the runtime prompt or current turn already exposes relevant prompt
   context, inspect:
   - plugin mentions already present
   - bundled skill mentions already present
   - project docs and other active context competing for prompt budget
   Treat this evidence as opportunistic. Use only what is visible in the
   current prompt context. Do not invent hidden telemetry or unsupported
   internal metrics.

## What To Evaluate

For each audited plugin, evaluate:

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

### 1. Search the memory index first

- Resolve the active evidence root first (`$CODEX_HOME`, then `~/.codex`, then
  `~/.agents`).
- If no `MEMORY.md` exists in any root, record that explicitly and continue; do
  not treat the audit as blocked.
- Search `MEMORY.md` with `rg` using:
  - repo name
  - repo basename
  - current `cwd`
  - plugin names
  - important plugin scripts, manifests, or file names
- Capture:
  - repeated workflows
  - repeated validation commands
  - repeated failure modes
  - ownership confusion
  - packaging drift

### 2. Open targeted rollout summaries

- If no rollout summary directory exists in the resolved roots, record that
  explicitly and move to raw sessions only if needed.
- Prefer summaries whose filenames, `cwd`, or `rollout_path` match the current
  project or plugin names.
- Extract:
  - what the user asked for repeatedly
  - which repo-owned plugins or bundled skills would have helped
  - what broke repeatedly
  - what commands proved correctness
  - which plugin instructions look stale, weak, or missing in hindsight

### 3. Check git history before raw sessions

- Before reading raw session JSONL, inspect git history for the plugins under
  review with `git log -- <plugin-dir>`.
- Use this as a cheap signal for:
  - whether the plugin is actively maintained
  - whether one plugin keeps changing while overlapping plugin surfaces stay
    stale
  - whether repo docs are evolving faster than the plugin package itself
- If git history already explains the likely staleness or ownership gap, prefer
  that evidence over a deeper session scan.

### 4. Use raw sessions only as a fallback

- Search the resolved `sessions/` JSONL root only when memory, rollout
  summaries, and git-history signals still do not contain the concrete detail
  you need.
- Search by:
  - exact `cwd`
  - repo basename
  - plugin name
  - thread ID from a rollout summary
  - specific file paths, commands, or failure text
- Use raw sessions to recover exact prompts, command sequences, injected plugin
  evidence, diffs, or failure text.

## Recommendation Types

- `Update`
  Use when a plugin is still the right owner but has stale manifest wording,
  metadata drift, weak packaging, poor bundled-skill boundaries, missing
  validation steps, outdated paths, or stale runtime guidance.

- `Add`
  Use when repeated plugin-level work exists and no audited repo-owned plugin is
  a good owner even after evaluating existing plugin packages and bundled
  skills. Prefer a plugin improvement or better repo docs before introducing a
  new plugin.

- `Merge`
  Use when two repo-owned plugins overlap enough that one should absorb,
  narrow, or specialize the other.

- `Disable`
  Use when a plugin is low-value, duplicate, misleading, or not worth its
  maintenance cost.

## Output Expectations

Return a compact audit with these sections:

1. `Audited repo-owned plugins`
   List the audited repo-owned plugins and the current role each one plays. If
   the user named plugins explicitly, list only the resolved requested plugins
   plus any directly relevant overlap needed to explain the recommendation.

2. `Evidence summary`
   Summarize the strongest repo, memory, session, cache-verification, and
   live-context signals that informed the audit.

3. `Per-plugin update roadmap`
   For each audited plugin, include:
   - plugin name
   - current role
   - observed strengths
   - missing or weak behavior
   - evidence source
   - highest-value next update
   - whether the issue should be solved in the plugin package, a bundled skill,
     repo docs, or `Maintainer`

4. `Add / merge / disable candidates`
   List only the candidates justified by evidence after reviewing the audited
   scope. For user-targeted audits, do not introduce unrelated portfolio
   candidates.

5. `Priority order`
   Rank the top recommendations by expected value, starting with the most
   useful update to make next.

## Decision Rules

- Audit repo-owned plugins before considering any broader external plugin
  surfaces.
- When the user names specific plugins, treat those named plugins as the
  primary and usually exclusive audit scope.
- Resolve user-named plugins before broader workflow discovery.
- Prefer improving an existing repo-owned plugin before adding a new one.
- Prefer improving a bundled skill or repo docs when the problem does not
  justify a plugin-level change.
- Recommend a new plugin only after checking whether an audited repo-owned
  plugin could own the workflow cleanly.
- Treat cache copies as verification only; never route fixes to the cache path.
- Treat live context-window analysis as best-effort only; rely only on evidence
  exposed in the current runtime prompt.
- Do not substitute a near-match for a user-named plugin without saying so
  explicitly.
- Only widen beyond the user-passed plugins when overlap, merge, or ownership
  evidence requires it.

## Failure Shields

- Do not invent recurring patterns without repo, memory, or session evidence.
- Do not confuse bundled-skill recurrence with plugin effectiveness.
- Do not recommend disabling a plugin without overlap, low-value, or
  misleading-behavior evidence.
- Do not flatten plugin-package, bundled-skill, and cache-state issues into one
  bucket; keep ownership decisions explicit.
- Do not jump to new-plugin recommendations before evaluating existing
  repo-owned plugins as possible owners.
- Do not bulk-load all rollout summaries or raw sessions; stay targeted.
- Do not skip cheap git-history checks and jump straight to raw sessions when
  staleness is the main question.
- Do not silently expand a user-targeted audit into a wider workflow or
  portfolio review.
- Do not mutate `~/.codex/plugins/cache/...`; treat it as evidence only.

## Follow-up

If the user asks to create, merge, or update one of the recommendations, switch
to `$plugin-creator` for a brand-new plugin or implement the chosen
repo-owned plugin or repo-doc change directly instead of continuing the audit.

## Examples

- "Audit the repo-maintained plugins used in this workflow and tell me which
  one should be updated first."
- "Review only plugin $gitstack and suggest the highest-value improvements."
- "Before we add a new plugin, check whether an existing repo-owned plugin or
  repo docs should own this workflow instead."
- "Audit only $tanstack and call out any bundled-skill overlap or stale
  packaging."
