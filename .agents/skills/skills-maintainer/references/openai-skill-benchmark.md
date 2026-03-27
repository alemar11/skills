# Upstream Skill Benchmark Playbook

Use this playbook when users ask to benchmark local skills against upstream skill repositories and propose meaningful optimizations for local markdown files. The main focus is learning from official OpenAI skills and using those patterns to improve local `SKILL.md` files.

## Purpose
- Compare local skills against proven official OpenAI patterns first.
- Emphasize `SKILL.md` structure quality and trigger/workflow clarity.
- Include both standard skill repos and plugin-packaged skills when they are part of the configured OpenAI baselines.
- Use non-OpenAI repositories only as optional comparison context, not as the main benchmark bar.
- Produce actionable markdown optimization proposals only (no auto-applied edits).

## Primary OpenAI Baselines
- `openai/skills`
- `openai/plugins`

Both are required by default.

## Optional Comparison Baselines
- `anthropics/skills`
- other upstream skill repositories explicitly requested by the user

## Script Entry Point
- `./.agents/skills/skills-maintainer/scripts/openai_skill_benchmark.py`

## Command Contract
```bash
./.agents/skills/skills-maintainer/scripts/openai_skill_benchmark.py \
  --ref main \
  --scope both \
  --repo openai/skills \
  --repo openai/plugins \
  --clone-root .cache/upstream-skills \
  --output-dir .agents/skills/skills-maintainer/artifacts/openai-skill-benchmark \
  --format both
```

## Defaults
- `--ref main`
- `--scope both`
- `--repo openai/skills --repo openai/plugins`
- `--clone-root .cache/upstream-skills`
- `--output-dir .agents/skills/skills-maintainer/artifacts/openai-skill-benchmark`
- `--format both`

## Expected Outputs
- `upstream_inventory.json`
- `local_inventory.json`
- `proposals.json`
- `per_skill_review.json`
- `comparison_report.md`

## Workflow (Mandatory Order)
1. `download`: clone or update the primary OpenAI baselines into `.cache/upstream-skills/` (`openai/skills` and `openai/plugins`).
   - If the user explicitly requested comparison repos, clone/update those too.
2. `extract-upstream`: parse frontmatter and `SKILL.md` section taxonomy, length metrics, and resource layout from downloaded repos.
   - For standard skill repositories, inspect top-level `skills/*`.
   - For plugin repositories such as `openai/plugins`, also inspect plugin-packaged skills under `plugins/*/skills/*`.
3. `audit-local`: inventory local skills (including hidden `.agents/skills/*` paths) with the same rubric.
4. `compare`: compute meaningful deltas against the primary OpenAI baselines first.
   - If comparison repos were configured, use them only as secondary context in the report.
5. `propose`: generate non-auto-applied structural recommendations for local skills.
   - Target markdown maintainability first: `SKILL.md`, `references/*.md`, and supporting maintainer docs when directly coupled.
6. `report`: emit JSON + markdown artifacts and summarize PASS/FAIL/NOOP.
7. `review-one-by-one`: after artifacts exist, review every local skill one by one and produce a per-skill decision:
   - `CHANGE`: propose concrete markdown updates for that skill.
   - `NOOP`: explicitly state no meaningful updates are needed for that skill.
   - If subagents are available and the user explicitly requested parallel work, shard the skill list across them and merge the final `CHANGE`/`NOOP` decisions in the parent agent.

## Parallel Subagent Pattern
- Use this only when subagent tools are available and the user explicitly asked for delegation or parallel agent work.
- Keep the benchmark script as the default way to generate baseline artifacts; do not replace the script with ad-hoc subagent work when the script can run cleanly.
- Safe parallel splits around that baseline:
  - after `download`, spawn one explorer subagent per OpenAI repo to inspect structure patterns independently
  - in parallel with upstream inspection, spawn one explorer subagent to inventory local skills if that does not overlap with the baseline artifact writer
  - after artifacts exist, spawn multiple explorer subagents for disjoint local-skill review buckets such as top-level reusable skills vs `.agents/skills/*`
- If you delegate per-skill proposal implementation later, assign disjoint file ownership to worker subagents and keep final proposal synthesis local.
- Keep artifact generation, comparison logic, final proposal merge, and PASS/FAIL result assembly in the main agent.
- Do not run multiple copies of `openai_skill_benchmark.py` concurrently against the same clone root or output directory. If isolated parallel analysis is required, give each subagent separate scratch paths and merge the results in the parent agent.

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
- Alignment with strong official OpenAI skill patterns such as concise overview framing, explicit workflow guidance, references navigation, and clear output expectations when they materially help.

Do not propose:
- Cosmetic heading renames with no practical gain
- Upstream style mimicry that conflicts with local conventions
- Refactors that increase maintenance burden without clear payoff

## Result Semantics
- `PASS`: meaningful proposals found and clearly justified
- `PASS (NOOP)`: no meaningful proposals
- `FAIL`: benchmark could not complete the primary OpenAI baseline analysis (for example clone/fetch failure for `openai/skills` or `openai/plugins`)

## Temporary Data Policy
- Persistent benchmark artifacts go under:
  - `.agents/skills/skills-maintainer/artifacts/openai-skill-benchmark/`
- Optional transient scratch data may use:
  - `.cache/` (default clone root: `.cache/upstream-skills/`)
- Clean stale temporary files before final report unless user asks to keep them.

## Network/Clone Failure Notes
- If `git clone`/`git fetch` fails for one or more primary OpenAI baselines, report `FAIL` and include captured errors in the report.
- Keep generated local inventory and partial artifacts for diagnostics.
- Retry after network recovery and rerun the same command contract.
