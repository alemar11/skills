# Upstream Skill Benchmark Playbook

Use this playbook when users ask to benchmark local skills against upstream skill repositories and propose meaningful optimizations for local markdown files.

## Purpose
- Compare local skills against proven upstream patterns.
- Emphasize `SKILL.md` structure quality and trigger/workflow clarity.
- Produce actionable markdown optimization proposals only (no auto-applied edits).

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
  --clone-root .cache/upstream-skills \
  --output-dir .agents/skills/tools/artifacts/openai-skill-benchmark \
  --format both
```

## Defaults
- `--ref main`
- `--scope both`
- `--repo openai/skills --repo anthropics/skills`
- `--clone-root .cache/upstream-skills`
- `--output-dir .agents/skills/tools/artifacts/openai-skill-benchmark`
- `--format both`

## Expected Outputs
- `upstream_inventory.json`
- `local_inventory.json`
- `proposals.json`
- `comparison_report.md`

## Workflow (Mandatory Order)
1. `download`: clone or update mandatory upstream repos into `.cache/upstream-skills/` (`openai/skills` and `anthropics/skills`).
2. `extract-upstream`: parse frontmatter and `SKILL.md` section taxonomy, length metrics, and resource layout from downloaded repos.
3. `audit-local`: inventory local skills (including hidden `.agents/skills/*` paths) with the same rubric.
4. `compare`: compute meaningful deltas against upstream patterns.
5. `propose`: generate non-auto-applied structural recommendations for local skills.
   - Target markdown maintainability first: `SKILL.md`, `references/*.md`, and supporting maintainer docs when directly coupled.
6. `report`: emit JSON + markdown artifacts and summarize PASS/FAIL/NOOP.
7. `review-one-by-one`: after artifacts exist, review every local skill one by one and produce a per-skill decision:
   - `CHANGE`: propose concrete markdown updates for that skill.
   - `NOOP`: explicitly state no meaningful updates are needed for that skill.

## Per-skill Output Requirement (Mandatory)
- Always provide a per-skill list for all locally discovered skills after benchmark artifacts are generated.
- For each skill include:
  - skill path
  - decision (`CHANGE` or `NOOP`)
  - short rationale
  - proposed target markdown files (when `CHANGE`)
- Do not auto-apply benchmark proposals unless the user explicitly asks for implementation.

## Meaningful Proposal Rubric
Propose only when there is a material improvement in:
- Trigger clarity (what activates the skill)
- Structural readability and maintainability
- Progressive disclosure (moving detailed content to `references/` when useful)
- Metadata/doc sync quality
- Markdown ergonomics (scanability, section intent clarity, and reduced duplication across `.md` files)

Do not propose:
- Cosmetic heading renames with no practical gain
- Upstream style mimicry that conflicts with local conventions
- Refactors that increase maintenance burden without clear payoff

## Result Semantics
- `PASS`: meaningful proposals found and clearly justified
- `PASS (NOOP)`: no meaningful proposals
- `FAIL`: benchmark could not complete baseline analysis (for example clone/fetch failure for upstream baselines)

## Temporary Data Policy
- Persistent benchmark artifacts go under:
  - `.agents/skills/tools/artifacts/openai-skill-benchmark/`
- Optional transient scratch data may use:
  - `.cache/` (default clone root: `.cache/upstream-skills/`)
- Clean stale temporary files before final report unless user asks to keep them.

## Network/Clone Failure Notes
- If `git clone`/`git fetch` fails for one or both mandatory repos, report `FAIL` and include captured errors in the report.
- Keep generated local inventory and partial artifacts for diagnostics.
- Retry after network recovery and rerun the same command contract.
