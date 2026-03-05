# Release Checklist

Run this checklist before finalizing maintainer updates.

## Pre-commit Validation
1. Metadata and docs
- Confirm skill names/descriptions are aligned across `SKILL.md`, `agents/openai.yaml`, and README entries.
- Confirm no stale references to removed or renamed skills.

2. Structural consistency
- Confirm required skill files exist.
- Confirm `references/` markdown naming policy is respected.

3. Domain-specific workflows
- If Postgres docs were refreshed, confirm runbook compliance and meaningful-change rationale.
- If upstream benchmarking was run, confirm benchmark artifacts and proposal report were generated under `.agents/skills/tools/artifacts/openai-skill-benchmark/`.

## Command Set (Typical)
- `find . -type f -name 'SKILL.md' -not -path '*/.git/*' | sort`
- `find . -type f -path '*/agents/openai.yaml' -not -path '*/.git/*' | sort`
- `rg -n "postgres-best-practices-runbook|openai-skill-benchmark|\\.agents/skills/tools|agents/openai.yaml|SKILL.md" -S`
- `git diff --stat`
- `git diff`

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
