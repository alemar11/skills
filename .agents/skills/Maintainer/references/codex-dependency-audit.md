# Codex Dependency Audit Playbook

Use this playbook when the user asks to audit which skills are Codex-dependent versus portable, or to tighten how Codex-specific runtime tools and contracts are documented.

## Purpose
- Keep the repo-level source of truth for skill portability accurate in `AGENTS.md`.
- Ensure Codex-dependent skills explicitly name the Codex tools, artifacts, or filesystem contracts they require.
- Ensure portable skills keep Codex-only helpers optional and provide a generic fallback path.

## Classification Rules
- `Codex-dependent`
  - The skill cannot run seamlessly in another agent runtime without adaptation because it requires Codex-branded/runtime-specific tools, paths, or artifacts.
  - Common signals:
    - Codex CLI or Codex App version discovery
    - `~/.codex/*`, `$CODEX_HOME`, Codex memory/session files, or Codex-only repo contracts
    - Codex-only maintainer workflows or runtime tools with no generic fallback
- `Codex-aware but portable`
  - The skill may mention Codex-only helpers, but they are optional accelerators and the skill still describes a generic fallback.
  - Common signals:
    - `request_user_input` with a normal chat fallback
    - optional subagent review with a local review fallback
- `Portable`
  - The skill's workflow is expressed in general shell, git, docs, or project-local terms and does not materially depend on Codex-specific runtime features.

## Workflow
1. Read the current Codex-dependency inventory in `AGENTS.md`.
2. Inspect the targeted skills' `SKILL.md` files and directly coupled docs for:
   - Codex-branded runtime/tool mentions
   - Codex filesystem or memory/session path assumptions
   - whether those dependencies are required or optional
   - whether a generic fallback exists when Codex-only helpers are mentioned
3. Classify each targeted skill as `Codex-dependent`, `Codex-aware but portable`, or `Portable`.
4. If the classification changed, update `AGENTS.md` in the same change.
5. For Codex-dependent skills, tighten wording so the exact required Codex tool/runtime contract is named plainly instead of vaguely.
6. For portable skills, rewrite Codex-only helper mentions so they stay explicitly optional and keep a generic fallback.
7. Run `metadata-sync.md` if any repo-facing descriptions changed.
8. Run the relevant checks from `doc-consistency.md` and finish with `release-checklist.md`.

## Quality Gates
- `AGENTS.md` accurately lists the current Codex-dependent skills when that inventory changes.
- Every Codex-dependent skill clearly names the Codex tool/runtime contract it requires.
- No portable skill accidentally hard-requires a Codex-only helper.
- `PASS (NOOP)` is valid when the inventory and wording are already correct.

## Reporting Contract
- Scope covered
- Skills audited
- Classification result per skill
- Files changed
- Why changed
- Result
- Any deferred follow-up
