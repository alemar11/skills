# Release Checklist

Run this checklist before finalizing maintainer updates.

## Pre-commit Validation
1. Metadata and docs
- Confirm skill names/descriptions are aligned across `SKILL.md`, `agents/openai.yaml`, and README entries.
- Confirm no stale references to removed or renamed skills.
- If Codex-dependency boundaries changed, confirm `AGENTS.md` and the maintainer playbooks reflect the updated classification.

2. Structural consistency
- Confirm required skill files exist.
- Confirm `references/` markdown naming policy is respected.
- Confirm Codex-dependent skills name their required Codex tools/runtime contracts explicitly, and portable skills keep Codex-only helpers optional.

## Command Set (Typical)
- `find . -type f -name 'SKILL.md' -not -path '*/.git/*' -not -path '*/.cache/*' | sort`
- `find . -type f -path '*/agents/openai.yaml' -not -path '*/.git/*' -not -path '*/.cache/*' | sort`
- `rg -n "\\.agents/skills/skills-maintainer|agents/openai.yaml|SKILL.md" -S`
- `rg -n "request_user_input|subagent|\\$CODEX_HOME|~/.codex|Codex CLI|Codex App|MEMORY.md|memory_summary.md" -S`
- `git diff --stat`
- `git diff`

## Parallelism Guardrail
- Read-only manifest listing and grep-style checks may run concurrently or through explorer subagents.
- Keep `git diff --stat`, `git diff`, final findings cleanup, and final PASS/FAIL report assembly in the main agent.
- If the broader maintenance task also includes a commit, keep post-commit verification sequential to avoid stale state.

## Final Report Template
- Scope: `<what was covered>`
- Commands run: `<ordered list of key commands>`
- Files changed: `<absolute or repo-relative paths>` or `none`
- Why changed: `<meaningful-change rationale per changed file>` or `NOOP (no meaningful updates needed)`
- Result: `PASS`, `PASS (NOOP)`, or `FAIL`
- Findings:
  - `P1/P2` blocking items
  - `WARN` cleanup items
- Follow-ups: `<optional next actions>`
