# Skill Upgrade Playbook

Use this playbook when a user asks to upgrade, modernize, tighten, or improve an existing skill.

## Purpose
- Improve one or more existing skills with meaningful, scoped documentation or metadata updates.
- Preserve the skill's intent while making triggers, workflow, guardrails, or supporting docs easier to use and maintain.
- Avoid silently expanding a targeted upgrade into repo-wide refresh work.

## Task Boundary
- `upgrade` is for one or more existing target skills.
- Default scope per target skill:
  - the skill's `SKILL.md`
  - the skill's `agents/openai.yaml`
  - the skill's `references/*.md`
  - directly coupled mentions in `README.md` or `AGENTS.md` when wording or durable repo guidance changes
- Do not refresh domain best-practices content unless the user explicitly asks for `refresh`.

## Workflow
1. Identify the target skill or skills and inspect each current package:
   - `SKILL.md`
   - `agents/openai.yaml`
   - any referenced `references/*.md` and `scripts/*`
   - related mentions in `README.md` and `AGENTS.md`
2. Define the concrete upgrade goals for each target before editing:
   - trigger clarity
   - workflow structure
   - guardrail precision
   - Codex dependency labeling or portability-boundary clarity when relevant
   - metadata/doc sync
   - moving dense guidance into `references/` when that improves maintainability
3. Apply minimal, meaningful edits that preserve each skill's current intent.
4. Run a focused sync pass using `references/metadata-sync.md` for the touched skills and any directly coupled docs.
5. Run a focused consistency pass using the relevant checks from `references/doc-consistency.md`:
   - required files still exist
   - referenced scripts/docs exist
   - no contradictory instructions were introduced
   - `references/` markdown naming still follows repo policy
6. Finish with `references/release-checklist.md` and report `PASS`, `PASS (NOOP)`, or `FAIL`.

## Parallel Subagent Pattern
- Use this only when subagent tools are available and the user explicitly asked for delegation or parallel agent work.
- Safe split for an upgrade request:
  - one explorer subagent reviews the target skill package (`SKILL.md`, `references/*.md`, `scripts/*`)
  - one explorer subagent reviews directly coupled metadata/docs (`agents/openai.yaml`, `README.md`, `AGENTS.md`)
- If edits are substantial and write scopes are disjoint, convert that split into worker ownership:
  - worker 1 owns the target skill package
  - worker 2 owns the coupled repo docs
- Keep upgrade-goal selection, final wording choices, and edit integration in the main agent.

## Quality Gates
- Each upgraded skill has a concrete rationale; avoid cosmetic rewrites with no practical gain.
- Touched docs stay aligned across `SKILL.md`, `agents/openai.yaml`, and `README.md`.
- `AGENTS.md` changes happen only when the upgrade introduces durable repository guidance.
- If a touched skill is Codex-dependent, its required Codex tools/runtime contracts are named plainly; if it is portable, Codex-only helpers remain optional.
- Return `PASS (NOOP)` when no meaningful improvement is needed after inspection.

## Reporting Contract
- Scope covered
- Checks executed
- Files changed
- Why changed
- Result
- Findings
- Any deferred follow-up
