# Repository Guidelines

## Overview
This repository hosts reusable Codex skills, repo-local plugins, and project maintainer skills. Reusable skills live under `skills/`, repo-local plugins live under `plugins/`, and project maintainer skills live under `.agents/skills/`. Every reusable or bundled skill is documented by a `SKILL.md` entrypoint, and every plugin must ship `.codex-plugin/plugin.json`. Keep guidance lightweight and focused on building and evolving skills and plugins.
Agent skills follow the specification at `https://agentskills.io/specification`.
Codex skills reference: `https://developers.openai.com/codex/skills/`.

## How to Create a Skill
- Prefer `$skill-creator` as the canonical scaffold and workflow reference for new skills or substantial skill reshapes; follow its initialization, metadata, validation, and forward-testing guidance before repo-specific cleanup.
- When a new or reshaped skill needs an embedded CLI under `scripts/` or a maintenance project under `projects/<tool>/`, route that CLI design and layout work through `$skill-cli-creator`.
- Create a dedicated directory per skill with a clear, stable name.
- Place reusable skills under `skills/<name>/`; place project maintainer skills under `.agents/skills/<name>/`.
- Add a `SKILL.md` that defines purpose, triggers, and the workflow to follow.
- Add `agents/openai.yaml` with UI metadata for the skill.
- Use the specification at `https://agentskills.io/specification` and `https://developers.openai.com/codex/skills/` when creating new skills.
- Keep `README.md` updated with current reusable and project skill lists, with a one-line description for each.

## How to Create a Plugin
- Prefer `$plugin-creator` as the canonical scaffold and marketplace-entry workflow reference for new plugins or substantial plugin reshapes; follow it for normalized naming, manifest shape, optional folders, and marketplace generation before repo-specific cleanup.
- When a new or reshaped plugin needs an embedded CLI under `scripts/`, `skills/<skill>/scripts/`, or a maintenance project under `projects/<tool>/`, route that CLI design and layout work through `$skill-cli-creator`.
- Use the specification at `https://developers.openai.com/codex/plugins` when creating new plugins.
- Create a dedicated directory under `plugins/<name>/` with a clear, stable plugin name.
- Add `.codex-plugin/plugin.json` and treat it as the plugin manifest source of truth for bundled metadata, assets, and bundled skill exposure.
- Register each repo-local plugin in `.agents/plugins/marketplace.json` in the same change that adds, removes, or renames the plugin.
- If the plugin bundles skills, place them under `plugins/<name>/skills/<skill>/` and give each bundled skill its own `SKILL.md`; add `agents/openai.yaml` when that bundled skill has UI metadata in this repo.
- Keep shared plugin runtime artifacts under `plugins/<name>/scripts/` and any maintenance-only implementation under `plugins/<name>/projects/<tool>/`.
- Keep `README.md` updated with the current plugin list and one-line descriptions, including bundled-skill summaries when that improves discoverability.

## Git Commits
- If changes affect multiple skills or plugins, split them into separate, meaningful commits.

## Rules
- Keep README.md skill descriptions, list, and install prompts in sync with `agents/openai.yaml` and any skill adds/removes/renames.
- Keep README.md plugin descriptions and list in sync with `.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json`, and any plugin adds/removes/renames.
- Keep a `Skill Dependencies` section in `README.md` only when one or more skills explicitly require loading other skills at runtime; list each such skill and the required companion skills, update the section when those requirements change, and remove or omit the section entirely when no such requirements exist.
- Keep `AGENTS.md` focused on repository structure, ownership boundaries, implementation notes, maintenance routing, portability notes, and durable learnings; keep invocation behavior, trigger rules, workflows, outputs, and other user-facing runtime contracts in the relevant `SKILL.md` and reference docs.
- Keep `AGENTS.md` lean: record only repo-specific rules or durable learnings that are hard to infer from the tree, and prefer linking or routing to `SKILL.md`, reference docs, or local package manifests instead of duplicating detailed doctrine, migration history, or exhaustive anti-regression lists.
- When new durable rules are discovered while creating or updating skills, add them to this AGENTS.md under the appropriate skill section.
- Use this section only as a fallback when no more appropriate section exists in AGENTS.md.
- In `references/` folders, keep `.md` filenames lowercase except for `README.md` and `AGENTS.md`.
- If `brand_color` isn’t provided, pick a random hex color not already used by other skills in this repo and set it in `agents/openai.yaml`.
- Plugin manifests must keep asset and bundled-skill paths repo-relative and valid from the plugin root; update them together with any plugin layout move. (Codex learning)
- Bundled plugin skills must follow the same runtime/maintenance split as reusable skills under `skills/`: runtime guidance stays in their `SKILL.md`, while repo-maintenance routing stays in repo-level maintainer docs. (Codex learning)
- Runtime skills must stay unaware of `.agents/skills/Maintainer`: do not reference it, its runbooks, or maintainer-routing instructions from runtime `SKILL.md` files or runtime usage references. Keep that routing only in repo-level maintainer docs such as this `AGENTS.md`.
- Runtime skills may surface runtime learnings or durable guidance candidates, but they must not perform self-upgrade, metadata-sync, reference-refresh, or other repo-maintenance workflows from their own runtime instructions.
- Route skill-maintenance and repo-maintenance work through `.agents/skills/Maintainer` from repo-level maintainer docs, not from runtime `SKILL.md` files.
- Keep the repo-level source of truth for skill portability in this `AGENTS.md`: record which skills are Codex-dependent vs portable when that boundary matters for maintenance or runtime behavior.
- Codex-dependent skills must explicitly name the Codex runtime tools, artifacts, or filesystem contracts they require in `SKILL.md`; skills intended to stay portable may mention Codex-only helpers only as optional accelerators with a generic fallback.
- Scope per-user cache files under `~/.cache/dotagents/` by owner: reusable skills use `~/.cache/dotagents/skills/<skill-name>/...`, plugin-shared caches use `~/.cache/dotagents/plugins/<plugin-name>/...`, and plugin-bundled skill caches use `~/.cache/dotagents/plugins/<plugin-name>/skills/<skill-name>/...`. (Codex learning)

### Codex Dependency Classification
- In this section, `portable` means "not dependent on Codex-only runtime features"; it does not necessarily mean the skill is repository-agnostic or broadly reusable unchanged.
- Current Codex-dependent skills are `codex-changelog`, `learn`, and `skill-audit`.
- Treat `plan-harder` as Codex-aware but portable because Codex-only helpers such as `request_user_input` or subagents are optional and have a non-Codex fallback path.
- Treat `.agents/skills/Maintainer` as a portable project-local maintainer skill because it relies on this repository layout and local shell/docs workflows, while any subagent usage remains optional.
- Treat `xcode-changelog` as portable and runtime-dependent on macOS plus network access: it requires `python3`, `xcodebuild`, `xcode-select`, `plutil`, and outbound access to Apple’s documentation endpoints.
- When a skill becomes Codex-dependent or stops being Codex-dependent, update this section in the same change as the skill docs.
- Keep this list updated whenever a skill is added, removed, renamed, or its portability boundary changes.

### Repo-local Plugins
- Keep repo-local plugin registration centralized in `.agents/plugins/marketplace.json`; do not add a plugin without wiring it there in the same rollout.
- Treat `.codex-plugin/plugin.json` as the plugin-local source of truth for plugin name, version, assets, and bundled-skill exposure.
- Keep plugin-bundled skills discoverable under `plugins/<plugin>/skills/` and keep any plugin-owned shared runtime surfaces under `plugins/<plugin>/scripts/`.
- When a plugin grows a maintenance-only implementation tree, keep it under `plugins/<plugin>/projects/<tool>/` and document rebuild/runtime rules there with a local `AGENTS.md`.
- Keep `skills-link.sh` as the canonical local install helper for this repo's reusable skills: it links `skills/` into `~/.agents/skills` only and must not install, mirror, or rewrite plugin marketplace entries. (Codex learning)

### Plugin Lifecycle and Versioning
- Treat `.agents/plugins/marketplace.json` as the repo discovery surface for local plugins: Codex can discover a plugin from the workspace marketplace file and resolve each plugin `source.path` relative to the repo root.
- Treat `~/.codex/plugins/cache/<developer>/<plugin>/<version>/` as the installed plugin cache: once a local plugin is installed, Codex may copy the plugin there and refresh that cached copy from the workspace source when the plugin changes. (Codex learning)
- Keep plugin install and update assumptions cache-aware: if a plugin manifest, bundled skill, runtime script, asset, or other shipped plugin file changes, assume Codex may compare or load the cached copy rather than reading only from the workspace path. (Codex learning)
- Any committed change under `plugins/<plugin>/` must update that plugin's `.codex-plugin/plugin.json` `version` in the same rollout.
- Use semantic versioning for plugin version bumps: major for breaking plugin contract changes such as removing or renaming the plugin, removing or renaming bundled skills, incompatible CLI or config changes, or other behavior that can break existing users.
- Use a minor version bump for backward-compatible feature additions or meaningful capability expansion under `plugins/<plugin>/`, such as adding a bundled skill, adding a new runtime command or workflow, or expanding the plugin's install surface without breaking existing behavior.
- Use a patch version bump for backward-compatible fixes and maintenance updates under `plugins/<plugin>/`, including bug fixes, packaging fixes, icon or metadata corrections, prompt or docs adjustments, rebuilds that preserve behavior, and other hotfix-style changes.

### Postgres skill
- Keep Postgres runtime and operator guidance in `skills/postgres/SKILL.md` and `skills/postgres/references/*`, not in this repo-level file.

### Swift-DocC skill
- Keep Swift-DocC bundled-asset refresh and reference integrity checks in `.agents/skills/Maintainer`, and use `.agents/skills/Maintainer/references/swift-docc-runbook.md` as the canonical procedure.
- Keep runtime Swift-DocC docs and fast-path reference design in `skills/swift-docc/`; keep maintainer-only refresh routing here. (Codex learning)

### Swift API Design skill
- Keep Swift API Design bundled-asset refresh and reference integrity checks in `.agents/skills/Maintainer`, and use `.agents/skills/Maintainer/references/swift-api-design-runbook.md` as the canonical procedure.
- Keep runtime Swift API Design docs and bundled-source usage details in `skills/swift-api-design/`; keep maintainer-only refresh routing here.
- Refresh `swift-api-design` from `swiftlang/swift-org-website/documentation/api-design-guidelines/index.md` until the live Swift.org page demonstrably migrates to a different substantive source. (Codex learning)

### Plan Harder skill
- Keep `plan-harder` as the single reusable home for higher-rigor planning support in this repo; do not reintroduce a separate lightweight clarification skill unless that package boundary is intentionally restored. (Codex learning)
- Keep `plan-harder` runtime workflow, clarification behavior, and output details in `skills/plan-harder/SKILL.md` and its references, not in this `AGENTS.md`.

### Maintainer skill
- The `.agents/skills/Maintainer` skill is the default maintainer for improving existing skills and plugins in this repository through shared upgrade tasks and skill-specific refresh workflows.
- `Maintainer` is the only maintainer skill that should orchestrate upgrades, metadata sync, reference refresh, and other repository maintenance for existing skills and plugins in this repository.
- Keep `Maintainer` self-contained: workflow markdown guidance must live under `.agents/skills/Maintainer/references/`.
- Keep the dependency direction one-way: runtime skills must not depend on, reference, or route users to `.agents/skills/Maintainer`; only repo-level maintainer docs may route work to `Maintainer`.
- When updating skill or plugin metadata/docs across the repo, route through the `Maintainer` playbooks and keep README/openai metadata text aligned.
- For brand-new skill creation, use `$skill-creator` first; use `Maintainer` afterward only for repo integration or follow-up maintenance. (Codex learning)
- Keep Codex-dependency audits and TanStack Intent coverage refresh as explicit maintainer-owned maintenance tracks; do not spread those maintenance workflows into runtime skills. (Codex learning)
- During Codex dependency audits, require Codex-dependent skills to name their required Codex tools or runtime contracts precisely, and require portable skills to keep Codex-only helpers optional with a generic fallback.

### Codex Changelog skill
- Keep `codex-changelog` as a Codex-dependent reusable skill under `skills/codex-changelog/`; release-source selection and output formatting belong in its own `SKILL.md` and references, not in this `AGENTS.md`.

### Skill CLI Creator skill
- Route embedded-CLI design and layout work through `$skill-cli-creator`; keep detailed host, execution, and migration doctrine in `skills/skill-cli-creator/SKILL.md` and its references.
- Repo-level embedded-CLI invariants are: shipped artifacts live under `scripts/`, maintenance-only implementations live under `projects/<tool>/`, and ownership stays aligned when a CLI is skill-owned, plugin-shared, or owned by one bundled plugin skill. (Codex learning)
- Persist embedded-CLI config in owner-aligned `config.toml` files under `<project-root>/.skills/...` or `<project-root>/.plugins/...`, and treat those directories as config-only. (Codex learning)
- Require the shipped artifact to expose `--version` with one semver source of truth, and if `projects/<tool>/` exists require `projects/<tool>/AGENTS.md` plus a scoped `projects/<tool>/.gitignore` when generated state exists. (Codex learning)

### GitStack plugin
- Keep `plugins/gitstack/` as the preferred full-stack install surface for linked git authoring, GitHub operations, and publish orchestration.
- Keep `plugins/gitstack/scripts/ghflow` as the shared runtime for bundled GitHub skills; do not add bundled skill-local runtime copies.
- Keep `ghflow` intentionally narrow in implementation scope; avoid expanding it into wrappers for routine `git` or `gh` operations that do not need shared higher-level behavior. (Codex learning)
- Bundle `git-commit`, `github`, `github-triage`, `github-reviews`, `github-ci`, `github-releases`, and `yeet` under `plugins/gitstack/skills/`.
- Keep GitHub-oriented skills distributed through `plugins/gitstack/`, not duplicated as standalone reusable skills under `skills/`. (Codex learning)

### GitHub skill
- Keep the bundled `github` skill under `plugins/gitstack/skills/github/` as the umbrella GitHub skill surface inside this repo-local plugin, with full publish-from-worktree remaining owned by bundled `yeet`.
- Keep shared install and dependency guidance for the bundled `github` skill centralized in `plugins/gitstack/skills/github/references/core/installation.md`. (Codex learning)
- Keep the bundled `github` skill self-owned and self-sufficient; do not require the upstream GitHub plugin for runtime routing or execution.
- Benchmark GitHub-skill parity work against the upstream `openai/plugins` GitHub bundle when useful, but keep repo-owned runtime instructions and helper flows local to this plugin.
- Keep full publish-from-worktree guidance in `plugins/gitstack/skills/yeet/SKILL.md` and `plugins/gitstack/skills/yeet/references/*`, not in `plugins/gitstack/skills/github`. (Codex learning)
- Organize bundled GitHub references under `plugins/gitstack/skills/github/references/` into domain slices: `core`, `triage`, `reviews`, `ci`, `releases`, and `publish`, and keep the shared runtime under `plugins/gitstack/scripts/ghflow`. (Codex learning)
- Domain docs and helpers may depend only on the shared `plugins/gitstack/scripts/ghflow` runtime plus same-domain reference material; do not create cross-domain helper dependencies. (Codex learning)

### Git Commit skill
- `git-commit` may be bundled inside `plugins/gitstack`, but keep it as a distinct skill-owned surface rather than folding commit authoring or staging responsibilities into `ghflow`. (Codex learning)

### Yeet skill
- Keep `yeet` focused on publish orchestration from a local checkout rather than duplicating commit-authoring or generic GitHub skill ownership. (Codex learning)
- Keep `yeet` dependency-aware: require bundled `git-commit` and `github` instead of vendoring a duplicate GitHub helper layer. (Codex learning)
- Within `plugins/gitstack`, keep `yeet` wired to bundled `git-commit` plus the shared `ghflow publish ...` runtime surface instead of legacy helper-script paths. (Codex learning)
- Treat GitStack plugin cache artifacts as the installed runtime surface for shared CLIs such as `ghflow`; do not treat cache-path resolution rules as repo-level API behavior. (Codex learning)

### Learn skill
- Keep `learn` as the repo-facing persistence surface for durable `AGENTS.md` updates in this repository; broader memory-system files are outside this repo's editable scope.
- When durable learnings are added through `learn`, place them in the most appropriate existing section when possible, otherwise create a fitting section; use `## Codex Learnings` only as a fallback, and suffix each inserted bullet with ` (Codex learning)`.

### Skill Audit skill
- Keep `skill-audit` as the single audit surface for installed Codex surfaces: standalone skills, plugin packages, and bundled plugin skills.
- Keep `skill-audit` implementation centered on local discovery surfaces first, with shared or cached installations used as verification surfaces rather than editable sources. (Codex learning)
- When auditing a bundled plugin skill, require `skill-audit` to inspect both the bundled skill contract and the owning plugin package, including `.codex-plugin/plugin.json` when available. (Codex learning)
- Treat Codex plugin cache copies under `~/.codex/plugins/cache/...` as verification only; do not route fixes or edits to cache paths. (Codex learning)
- When a named target path lives under `~/.codex/plugins/cache/...`, require `skill-audit` to resolve plugin identity first, then use visible workspace plugin discovery surfaces such as `.agents/plugins/marketplace.json` and the owning `.codex-plugin/plugin.json` to confirm the editable source when possible; if no workspace mapping is visible, report that the editable source was not confirmed. (Codex learning)
- When plugin-package issues are actually bundled-skill issues, prefer recommending the narrowest owning surface: bundled plugin skill, plugin package, repo docs, or `Maintainer`.
