# Upstream Skill Benchmark Playbook

Use this playbook when users ask to benchmark local skills against upstream skill repositories and propose meaningful structural improvements.

## Purpose
- Compare local skills against proven upstream patterns.
- Emphasize `SKILL.md` structure quality and trigger/workflow clarity.
- Produce actionable proposals only (no auto-applied edits).

## Mandatory Upstream Baselines
- `openai/skills`
- `anthropics/skills`

Both are required by default unless the user explicitly requests a narrower scope.

## Script Entry Point
- `./.agents/skills/tools/scripts/openai_skill_benchmark.py`

## Command Contract
```bash
./.agents/skills/tools/scripts/openai_skill_benchmark.py \
  --ref main \
  --scope both \
  --repo openai/skills \
  --repo anthropics/skills \
  --output-dir .agents/skills/tools/artifacts/openai-skill-benchmark \
  --format both
```

## Defaults
- `--ref main`
- `--scope both`
- `--repo openai/skills --repo anthropics/skills`
- `--output-dir .agents/skills/tools/artifacts/openai-skill-benchmark`
- `--format both`

## Expected Outputs
- `upstream_inventory.json`
- `local_inventory.json`
- `proposals.json`
- `comparison_report.md`

## Workflow (Mandatory Order)
1. `fetch`: pull upstream skill index/content from mandatory repos via GitHub API/raw endpoints.
2. `extract`: parse frontmatter and `SKILL.md` section taxonomy, length metrics, and resource layout.
3. `audit-local`: inventory local skills (including hidden `.agents/skills/*` paths).
4. `compare`: compute meaningful deltas against upstream patterns.
5. `propose`: generate non-auto-applied structural recommendations.
6. `report`: emit JSON + markdown artifacts and summarize PASS/FAIL/NOOP.

## Meaningful Proposal Rubric
Propose only when there is a material improvement in:
- Trigger clarity (what activates the skill)
- Structural readability and maintainability
- Progressive disclosure (moving detailed content to `references/` when useful)
- Metadata/doc sync quality

Do not propose:
- Cosmetic heading renames with no practical gain
- Upstream style mimicry that conflicts with local conventions
- Refactors that increase maintenance burden without clear payoff

## Result Semantics
- `PASS`: meaningful proposals found and clearly justified
- `PASS (NOOP)`: no meaningful proposals
- `FAIL`: benchmark could not complete baseline analysis (for example hard API failure)

## Temporary Data Policy
- Persistent benchmark artifacts go under:
  - `.agents/skills/tools/artifacts/openai-skill-benchmark/`
- Optional transient scratch data may use:
  - `.cache/`
- Clean stale temporary files before final report unless user asks to keep them.

## Rate Limit Notes
- If GitHub API requests return `403` due rate limits, report `FAIL` with collected errors and keep local inventory artifacts.
- Recommend retrying with `GH_TOKEN` or `GITHUB_TOKEN` set to increase API limits.
