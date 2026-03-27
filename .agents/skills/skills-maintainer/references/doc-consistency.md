# Doc Consistency Playbook

Use this playbook for repository-wide structure and policy checks.

## Checks
1. Naming and layout
- Skill folders are stable and clearly named.
- `references/` markdown filenames are lowercase (except `README.md` and `AGENTS.md`).

2. Required files
- Each skill has `SKILL.md`.
- Skills with UI metadata have `agents/openai.yaml`.
- Hidden/project skills under `.agents/skills/*` are included in audits.

3. Script/reference integrity
- Script paths referenced in docs exist.
- High-level docs do not point to removed files.

4. Policy alignment
- AGENTS guidance matches current repository conventions.
- Skill-specific rules (for example Postgres guardrails) are not contradicted by newer docs.
- Benchmark playbook commands and script flags match the benchmark script contract.

## Severity Rules
- `FAIL` (blocking):
  - Missing required skill files (`SKILL.md`, required `agents/openai.yaml` where expected).
  - Broken script/reference links in active playbooks.
  - Policy contradictions that can cause unsafe or incorrect task execution.
- `WARN` (non-blocking):
  - Cleanup opportunities (wording drift, overly broad commands, minor doc mismatches).
  - Recommendations that improve maintainability but do not break current behavior.
- `PASS`:
  - No blocking issues and no unresolved warnings requiring immediate action.

## Suggested Commands
- `find . -type f -name 'SKILL.md' -not -path '*/.git/*' -not -path '*/.cache/*' | sort`
- `find . -type f -path '*/agents/openai.yaml' -not -path '*/.git/*' -not -path '*/.cache/*' | sort`
- `find . -type f -path '*/references/*.md' -not -path '*/.git/*' -not -path '*/.cache/*' | sort`
- `find . -type f -path '*/references/*.md' -not -path '*/.git/*' -not -path '*/.cache/*' | awk -F/ '{print $NF}'`
- `rg -n "\./scripts/|agents/openai.yaml|SKILL.md|\\.agents/skills/" -S`

## Parallel Subagent Pattern
- Use this only when subagent tools are available and the user explicitly asked for delegation or parallel agent work.
- Safe explorer split:
  - one subagent for naming/layout and required-file checks
  - one subagent for script/reference integrity
  - one subagent for policy alignment and benchmark-playbook contract review
- Keep final severity assignment, duplicate-findings cleanup, and the user-facing PASS/FAIL/WARN report in the main agent.

## Reporting Format
- `PASS`: check succeeded
- `FAIL`: blocking inconsistency with file path
- `WARN`: non-blocking cleanup recommendation
