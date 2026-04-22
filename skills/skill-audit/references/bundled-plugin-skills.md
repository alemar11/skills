# Bundled Plugin Skill Audits

Use this workflow when the target is a skill bundled inside a plugin package.

Audit the bundled skill as a skill, but also inspect the owning plugin package.
Do not assume the problem belongs to the bundled skill alone.

## Resolution

- Resolve the bundled skill path or bundle name first.
- Identify the owning plugin package.
- Inspect the plugin package alongside the bundled skill, including
  `.codex-plugin/plugin.json`.
- When the bundled skill path is inside `~/.codex/plugins/cache/...`, also open
  `references/cache-resolution.md`.

## What To Inspect

- bundled skill `SKILL.md`
- bundled skill `agents/openai.yaml` when present
- owning plugin `.codex-plugin/plugin.json`
- `.agents/plugins/marketplace.json` when available
- plugin-level `scripts/*`, `projects/*`, assets, or docs only when they are
  relevant to the question

## What To Evaluate

- whether the bundled skill contract is clear, current, and aligned with its
  metadata
- whether the bundled skill still belongs inside the current plugin package
- whether the plugin manifest or marketplace registration describes the bundled
  surface coherently
- whether the problem belongs to:
  - the bundled skill only
  - the plugin package only
  - both, with a split recommendation
  - docs only
- whether cache/install behavior is hiding a packaging problem rather than a
  skill-contract problem

## Evidence Workflow

1. Search the memory index first.
   - Use repo name, plugin name, bundled skill name, and important paths.
2. Open targeted rollout summaries.
   - Prefer summaries matching the plugin name, bundled skill name, or owning
     project.
3. Check cheap maintenance signals.
   - Use `git log -- <bundled-skill-dir>` and `git log -- <plugin-dir>` when
     both are available.
4. Use raw sessions when behavior is in question, and as a fallback otherwise.
   - Search by bundled skill name, skill path, plugin name, `.codex-plugin`,
     exact `cwd`, thread ID, or failure text.

## Ownership Guidance

- Put findings on `bundled plugin skill` when the issue is in that skill's
  triggers, guardrails, references, or bundled-skill metadata.
- Put findings on `plugin` when the issue is package-level:
  - `.codex-plugin/plugin.json`
  - marketplace registration
  - bundled-skill exposure
  - shared runtime layout
  - asset or package shipping gaps
- Put findings on both when the bundled skill and plugin package drift together.
- Put findings on `docs` when the code/package surfaces are fine but repo
  guidance is stale or misleading.
