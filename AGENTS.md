# Repository Guidelines

## Overview
This repository hosts reusable Codex skills, repo-local plugins, and project maintainer skills. Reusable skills live under `skills/`, repo-local plugins live under `plugins/`, and project maintainer skills live under `.agents/skills/`. Every reusable or bundled skill is documented by a `SKILL.md` entrypoint, and every plugin must ship `.codex-plugin/plugin.json`. Keep guidance lightweight and focused on building and evolving skills and plugins.
Agent skills follow the specification at `https://agentskills.io/specification`.
Codex skills reference: `https://developers.openai.com/codex/skills/`.

## How to Create a Skill
- Prefer [$skill-creator](/Users/alessandro/.codex/skills/.system/skill-creator/SKILL.md) as the canonical scaffold and workflow reference for new skills or substantial skill reshapes; follow its initialization, metadata, validation, and forward-testing guidance before repo-specific cleanup.
- Create a dedicated directory per skill with a clear, stable name.
- Place reusable skills under `skills/<name>/`; place project maintainer skills under `.agents/skills/<name>/`.
- Add a `SKILL.md` that defines purpose, triggers, and the workflow to follow.
- Add `agents/openai.yaml` with UI metadata for the skill.
- Use the specification at `https://agentskills.io/specification` and `https://developers.openai.com/codex/skills/` when creating new skills.
- Keep `README.md` updated with current reusable and project skill lists, with a one-line description for each.

## How to Create a Plugin
- Prefer [$plugin-creator](/Users/alessandro/.codex/skills/.system/plugin-creator/SKILL.md) as the canonical scaffold and marketplace-entry workflow reference for new plugins or substantial plugin reshapes; follow it for normalized naming, manifest shape, optional folders, and marketplace generation before repo-specific cleanup.
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
- Keep `link.sh` as the canonical local install helper for this repo: it links reusable skills from `skills/` into `~/.agents/skills`, creates per-plugin symlinks under `~/.agents/plugins/plugins/`, and merges this repo's entries into `~/.agents/plugins/marketplace.json` without clobbering other personal plugin sources. (Codex learning)

### Plugin Lifecycle and Versioning
- Treat `.agents/plugins/marketplace.json` as the repo discovery surface for local plugins: Codex can discover a plugin from the workspace marketplace file and resolve each plugin `source.path` relative to the repo root.
- Treat `~/.codex/plugins/cache/<developer>/<plugin>/<version>/` as the installed plugin cache: once a local plugin is installed, Codex may copy the plugin there and refresh that cached copy from the workspace source when the plugin changes. (Codex learning)
- Keep plugin install and update assumptions cache-aware: if a plugin manifest, bundled skill, runtime script, asset, or other shipped plugin file changes, assume Codex may compare or load the cached copy rather than reading only from the workspace path. (Codex learning)
- Any committed change under `plugins/<plugin>/` must update that plugin's `.codex-plugin/plugin.json` `version` in the same rollout.
- Use semantic versioning for plugin version bumps: major for breaking plugin contract changes such as removing or renaming the plugin, removing or renaming bundled skills, incompatible CLI or config changes, or other behavior that can break existing users.
- Use a minor version bump for backward-compatible feature additions or meaningful capability expansion under `plugins/<plugin>/`, such as adding a bundled skill, adding a new runtime command or workflow, or expanding the plugin's install surface without breaking existing behavior.
- Use a patch version bump for backward-compatible fixes and maintenance updates under `plugins/<plugin>/`, including bug fixes, packaging fixes, icon or metadata corrections, prompt or docs adjustments, rebuilds that preserve behavior, and other hotfix-style changes.

### Postgres skill
- Keep Postgres runtime behavior and operator-facing rules in `skills/postgres/SKILL.md` and `skills/postgres/references/*` (not duplicated here).
- The runtime `postgres` skill must not describe or perform self-upgrade, best-practices refresh, or other package-maintenance workflows. It may still expose runtime learnings that could later be promoted into durable runtime guidance.

### Swift-DocC skill
- Keep the runtime `swift-docc` skill focused on bundled authored content (`assets/DocCDocumentation.docc`), `references/*.md` fast paths, and manifest metadata only.
- The runtime `swift-docc` skill must not describe or perform self-upgrade, bundled asset refresh, or reference-layer maintenance workflows.
- Keep Swift-DocC bundled-asset refresh and reference integrity checks in `.agents/skills/Maintainer`, and use `.agents/skills/Maintainer/references/swift-docc-runbook.md` as the canonical procedure.
- Route maintainer-only Swift-DocC refresh work through repo-level maintainer docs and the `Maintainer` skill workflow, not through runtime skill instructions.
- Keep `skills/swift-docc/references/*.md` biased toward thin, high-frequency task routes such as package API docs, async or stateful API docs, and local preview or render workflows. (Codex learning)

### Swift API Design skill
- Keep the runtime `swift-api-design` skill focused on the bundled upstream guideline source (`assets/api-design-guidelines.md`), `references/*.md` fast paths, and manifest metadata only.
- The runtime `swift-api-design` skill must not describe or perform self-upgrade, bundled asset refresh, or reference-layer maintenance workflows.
- Keep Swift API Design bundled-asset refresh and reference integrity checks in `.agents/skills/Maintainer`, and use `.agents/skills/Maintainer/references/swift-api-design-runbook.md` as the canonical procedure.
- Route maintainer-only Swift API Design refresh work through repo-level maintainer docs and the `Maintainer` skill workflow, not through runtime skill instructions.
- Refresh `swift-api-design` from `swiftlang/swift-org-website/documentation/api-design-guidelines/index.md` until the live Swift.org page demonstrably migrates to a different substantive source. (Codex learning)

### Plan Harder skill
- Keep the runtime `plan-harder` skill planning-only: it must create and refine plans, not implement the requested work. (Codex learning)
- By default, `plan-harder` must save generated plans inside `plans/` under the current working directory and create that directory if it does not exist. (Codex learning)
- Keep `plan-harder` as the single reusable home for higher-rigor clarification before planning; do not reintroduce a separate lightweight clarification skill unless that standalone contract is intentionally restored. (Codex learning)
- In `plan-harder`, ask only the minimum high-signal clarification batch, prefer compact defaults-friendly question formats, and avoid asking questions that a quick repo or config read can answer. (Codex learning)

### Maintainer skill
- The `.agents/skills/Maintainer` skill is the default maintainer for improving existing skills and plugins in this repository through shared upgrade tasks and skill-specific refresh workflows.
- `Maintainer` is the only maintainer skill that should orchestrate upgrades, metadata sync, reference refresh, and other repository maintenance for existing skills and plugins in this repository.
- Keep `Maintainer` self-contained: workflow markdown guidance must live under `.agents/skills/Maintainer/references/`.
- Keep the dependency direction one-way: runtime skills must not depend on, reference, or route users to `.agents/skills/Maintainer`; only repo-level maintainer docs may route work to `Maintainer`.
- When updating skill or plugin metadata/docs across the repo, route through the `Maintainer` playbooks and keep README/openai metadata text aligned.
- Treat `maintain skills` as the single public maintenance task; repo-wide pass, targeted maintenance, and metadata-only alignment are internal modes of that task.
- Treat plain-language "maintain this skill", "upgrade this skill", and "sync metadata/docs" requests as one unified maintenance entrypoint whose internal mode depends on scope: repo-wide pass, targeted maintenance, or metadata-only alignment.
- Treat generic `$Maintainer` imperatives like "run" or "run your tasks" as the repo-wide pass of that unified maintenance task: inspect the repo, choose skills with clear actionable drift, update local `SKILL.md`, `agents/openai.yaml`, `README.md`, and `AGENTS.md` as needed, then run audit and `release-checklist.md`; do not infer new-skill creation or `refresh`. (Codex learning)
- For brand-new skill creation, use `$skill-creator` first; use `Maintainer` afterward only for repo integration or follow-up maintenance. (Codex learning)
- When delegation is explicitly requested and the runtime supports subagents, `Maintainer` may spawn multiple subagents only for independent analysis or disjoint write scopes; keep routing, final synthesis, and git verification in the main agent. (Codex learning)
- Keep an explicit `audit codex dependencies` task in `Maintainer` for verifying which skills are Codex-dependent versus portable, updating this `AGENTS.md` inventory when that boundary changes, and tightening Codex-tool/runtime wording in affected `SKILL.md` files.
- During Codex dependency audits, require Codex-dependent skills to name their required Codex tools or runtime contracts precisely, and require portable skills to keep Codex-only helpers optional with a generic fallback.

### Codex Changelog skill
- Split `codex-changelog` output into `Codex CLI` and `Codex App` sections when reporting release notes. (Codex learning)
- Always fetch Codex CLI notes from `openai/codex` GitHub releases, even if the OpenAI Codex changelog page also lists CLI entries. (Codex learning)
- Fetch Codex App notes from `https://developers.openai.com/codex/changelog` and match the installed desktop app version when possible. (Codex learning)

### Skill CLI Creator skill
- Standardize embedded CLIs around a two-surface model: `scripts/` contains the shipped runnable artifacts used in normal execution, and `projects/<tool>/` is the optional maintenance-only build project behind one shipped CLI. (Codex learning)
- Keep `skill-cli-creator` host-aware: it must support skill-owned CLIs and plugin-owned CLIs under one doctrine, with the first decision being the host mode and owner boundary. (Codex learning)
- For embedded CLIs, require normal runtime usage to execute from `scripts/...`; do not direct normal users to run code from `projects/<tool>/`. (Codex learning)
- In embedded CLIs, inspect `projects/<tool>/` only when fixing, improving, rebuilding, or extending the implementation behind the `scripts/...` surface; do not treat it as part of the normal runtime surface. (Codex learning)
- Use `projects/<tool>/` only when the embedded CLI is large enough to benefit from a conventional project layout; keep script-native shipped artifacts entirely in `scripts/`. (Codex learning)
- Require all embedded CLIs to expose `scripts/<tool> --version` and keep one semver source of truth, using the runtime-native manifest version when available and a single explicit code or file source otherwise. (Codex learning)
- Do not treat `target/`, `dist/`, virtualenv paths, or similar build locations as supported runtime entrypoints for embedded CLIs; compiled outputs must be restored into `scripts/` before normal use. (Codex learning)
- Name embedded CLIs independently from their hosts by default: the skill or plugin name is the guidance/package container, while the CLI/tool name owns `scripts/<tool>` and `projects/<tool>/`. Reuse the host name only when it is intentionally the clearest ecosystem-standard runtime noun. (Codex learning)
- When an embedded CLI introduces project-local generated build, cache, module, or environment directories inside `projects/<tool>/`, create or update `projects/<tool>/.gitignore`; keep it conditional and scoped to that tool's generated paths rather than duplicating repo-wide ignore rules. (Codex learning)
- Owning runtime docs must include a `CLI Maintenance` section that keeps normal runtime work on `scripts/...` and routes bug fixes, performance work, rebuilds, and feature additions through the maintained implementation. (Codex learning)
- If `projects/<tool>/` exists for an embedded CLI, require `projects/<tool>/AGENTS.md` with build, test, rebuild, runtime-prerequisite, safe-maintenance instructions, the version source of truth, the semver bump policy, and rebuild steps that restore the shipped artifact in `scripts/...`. (Codex learning)
- Embedded CLI `projects/<tool>/AGENTS.md` files must define semver bumps as: major for breaking CLI contract changes, minor for backward-compatible new features or meaningful capability additions, and patch for backward-compatible bug fixes or corrections. (Codex learning)
- Keep persisted embedded-CLI config owner-aligned: skill-owned CLIs use `<project-root>/.skills/<skill>/config.toml`, shared plugin-owned CLIs use `<project-root>/.plugins/<plugin>/config.toml`, and plugin-owned single-skill CLIs stay under the owning skill's `.skills/...` namespace. (Codex learning)
- Treat `<project-root>/.skills/<skill>/` and `<project-root>/.plugins/<plugin>/` as config-only; do not place helper scripts or implementation code there. (Codex learning)
- Treat owner-level `config.toml` files under `.skills/...` or `.plugins/...` as local persisted operator config, not repo content; consuming repos should gitignore those files, and migrations from legacy `<skill>.toml` names must update ignore rules in the same rollout. (Codex learning)
- For embedded CLIs, prefer owner-aligned project-local config first, allow environment variables for one-off runs, and use external config paths only when the user explicitly asks. (Codex learning)
- Standardize persisted config on owner-level `config.toml` with required `schema_version` and optional non-authoritative `[meta]`; do not require top-level `version` or per-tool version fields as normative config state. (Codex learning)
- When a plugin-owned single-skill CLI becomes shared across bundled skills, move the shipped artifact, maintenance project, and config namespace together, then document one deterministic read path instead of silently reading both old and new config locations. (Codex learning)
- Treat plugin-root `scripts/` as a repo convention for plugin-owned shared CLIs, not as an officially documented Codex plugin manifest component. (Codex learning)
- Do not standardize alternative generic maintenance folder names such as `src/`, `code/`, `impl/`, or `source/` for embedded CLIs; prefer `projects/<tool>/` when a private implementation tree is needed. (Codex learning)
- In embedded-CLI docs, separate the artifact path from the public runtime noun: use `scripts/<tool>` for ownership or rebuild instructions, but prefer `<tool> ...` in normal user-facing examples when the CLI exposes that stable command name. (Codex learning)

### GitStack plugin
- Keep `plugins/gitstack/` as the preferred full-stack install surface for linked git authoring, GitHub operations, and publish orchestration.
- Keep `plugins/gitstack/scripts/ghops` as the shared runtime for bundled GitHub skills; do not add bundled skill-local runtime copies.
- Bundle `git-commit`, `github`, `github-triage`, `github-reviews`, `github-ci`, `github-releases`, and `yeet` under `plugins/gitstack/skills/`.
- Do not keep standalone reusable copies of `git-commit`, `github`, or `yeet` under `skills/`; GitStack is the supported distributable surface for those workflows in this repo. (Codex learning)
- Keep `git-commit` bundled as skill-only in `gitstack`; do not add a `ghops commit ...` surface in v1.
- Keep bundled `github` as the umbrella skill and allow the specialist bundled skills only when they map cleanly to one existing GitHub domain slice.
- Do not add `github-publish`; keep publish or lifecycle work in bundled `github` and full local publish in bundled `yeet`. (Codex learning)

### GitHub skill
- Keep the bundled `github` skill under `plugins/gitstack/skills/github/` as the single GitHub runtime entrypoint for repo-scoped work plus authenticated-user star and star-list workflows across triage, reviews, CI, releases, and PR publish or lifecycle work, and reserve bundled `yeet` only for full local-worktree publish.
- Treat the GitHub consolidation as intentionally breaking: the supported install surface for GitHub workflows in this repo is `plugins/gitstack`, not parallel reusable skills under `skills/`.
- Do not reintroduce `github-reviews`, `github-ci`, `github-releases`, or `github-publish` as standalone reusable skills, install prompts, or examples.
- Keep the bundled `github` skill self-owned and self-sufficient; do not require the upstream GitHub plugin for runtime routing or execution.
- Benchmark GitHub-skill parity work against the upstream `openai/plugins` GitHub bundle when useful, but keep runtime instructions and helper flows fully repo-local.
- Keep authenticated-user star and star-list flows in the `triage` domain, not in a new top-level GitHub sub-skill. (Codex learning)
- Resolve GitHub star-list selectors by exact slug first, then exact name; require `--list-id` when the selector is ambiguous. (Codex learning)
- For GitHub star-list membership changes, read current memberships first and send the full desired list id set to `updateUserListsForItem` so unrelated memberships are preserved. (Codex learning)
- Keep full publish-from-worktree guidance in `plugins/gitstack/skills/yeet/SKILL.md` and `plugins/gitstack/skills/yeet/references/*`, not in `plugins/gitstack/skills/github`. (Codex learning)
- Organize bundled GitHub references under `plugins/gitstack/skills/github/references/` into domain slices: `core`, `triage`, `reviews`, `ci`, `releases`, and `publish`, and keep the shared runtime under `plugins/gitstack/scripts/ghops`. (Codex learning)
- Future extractable GitHub plugin skills must map cleanly to one domain slice under `plugins/gitstack/skills/github/references/<domain>/`. (Codex learning)
- Domain docs and helpers may depend only on the shared `plugins/gitstack/scripts/ghops` runtime plus same-domain reference material; do not create cross-domain helper dependencies. (Codex learning)
- Run `github` publish-domain helpers from the target repository root, even
  when the helper path itself lives in another checkout. (Codex learning)
- When `prs_open_current_branch.sh` is asked to use an explicit `--base`, do
  not silently reuse an existing PR that targets a different base; surface the
  mismatch and require an explicit base update instead. (Codex learning)
- For release-backed tag creation in the `releases` domain, resolve the repository default branch explicitly and surface the exact target SHA before mutation; do not hardcode `main`.
- For release creation in the `releases` domain, standardize the notes choice as three options: infer from the last published release tag, keep blank, or use user-provided notes; recommend infer when the user leaves it unspecified.
- For tag-creation requests in the `releases` domain, distinguish "release-backed tag" (`gh release create`) from "tag-only" (`git tag` / `gh api`) before choosing commands.
- For GitHub Actions investigations in the `ci` domain, distinguish PR-associated failures from generic branch, SHA, workflow, schedule, manual, or explicit run-id runs; use `gh pr checks` only for PR-associated runs and prefer `gh run list` / `gh run view` otherwise.

### Git Commit skill
- `git-commit` may be bundled inside `plugins/gitstack`, but keep its contract unchanged: selective staging, commit authoring, and post-commit verification stay skill-owned rather than moving into `ghops`. (Codex learning)

### Yeet skill
- Keep `yeet` focused on full publish from local checkout to draft PR while staying orchestration-only: branch strategy and push belong in `yeet`, commit discipline belongs in `git-commit`, and post-push PR logic belongs in `github`. (Codex learning)
- Keep `yeet` dependency-aware rather than runtime-independent: it should require `git-commit` and `github` instead of vendoring a duplicate GitHub helper layer. (Codex learning)
- Within `plugins/gitstack`, keep `yeet` wired to bundled `git-commit` plus the shared `ghops publish ...` runtime surface instead of legacy helper-script paths. (Codex learning)
- Treat long-lived branches such as `stable`, `release/*`, `develop`, or
  `main` as PR bases, not publish branches: create a fresh short-lived branch
  from them and open the PR back against that long-lived branch. (Codex learning)
- Prefer the active repo or runtime branch-prefix convention for new `yeet`
  branches instead of hardcoding `topic/`. (Codex learning)

### Learn skill
- Keep `learn` scoped to `AGENTS.md` writes only; do not instruct it to write `MEMORY.md`, `memory_summary.md`, or other memory files.
- When `learn` writes to `AGENTS.md`, place entries in the most appropriate existing section when possible, otherwise create a fitting section; use `## Codex Learnings` only as a fallback, and suffix each inserted bullet with ` (Codex learning)`.

### Skill Audit skill
- Keep `skill-audit` biased toward improving shared skills first, especially for broad reusable skills such as `postgres`.
- When a gap is project-specific but lightweight, prefer project docs, `AGENTS.md`, repo references, or memory over proposing a project-local specialization.
- Recommend a project-local specialization only as a last resort when the workflow is highly stable, repeatedly needed, and too project-specific to fit cleanly in the shared skill or repo docs.
- In full-portfolio audits, require `skill-audit` to ignore itself by default, propose suggestions for the other audited skills first, then ask the user whether they want a follow-up audit of `skill-audit` too.
- In user-targeted audits, require `skill-audit` to audit only the explicitly requested skills and ignore itself unless `skill-audit` was explicitly requested too.
