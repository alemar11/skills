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

## Suggested Commands
- `find . -type f -name 'SKILL.md' -not -path '*/.git/*' | sort`
- `find . -type f -path '*/agents/openai.yaml' -not -path '*/.git/*' | sort`
- `rg --files -g '*/references/*.md'`
- `find . -type f -path '*/references/*.md' | awk -F/ '{print $NF}'`
- `rg -n "\./scripts/|agents/openai.yaml|SKILL.md|\\.agents/skills/" -S`

## Reporting Format
- `PASS`: check succeeded
- `FAIL`: blocking inconsistency with file path
- `WARN`: non-blocking cleanup recommendation
