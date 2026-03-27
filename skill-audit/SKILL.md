---
name: skill-audit
description: Audit installed Codex skills using project history, memories, sessions, and current context to plan updates, additions, merges, or disables. Use when a user asks how their installed skills are performing, wants a one-by-one refinement roadmap, wants to improve project-local or global skills, or wants evidence-based recommendations before changing skills.
---

# Skill Audit

## Overview

Audit installed skills before proposing new ones.

Treat the installed skill portfolio as the primary subject. Prefer updating, merging, or disabling existing skills before recommending new skills. Treat project-local specializations as a last resort.

Use repo evidence, Codex memory, past sessions, and current live context when available to judge whether installed skills are pulling their weight.

For broad reusable skills, prefer fixing the shared skill or relying on project docs and memory before proposing a repo-specific variant.

If `skill-audit` itself is part of the installed portfolio, always audit it too and treat its own gaps as first-class findings.

If the user asks for a narrow audit, such as only the skills used in the
current workflow, honor that scope explicitly instead of expanding to the full
installed portfolio.

## Audit Order

1. Map the current repo surface.
   Identify the repo root and read the most relevant project guidance first, such as `AGENTS.md`, `README.md`, roadmap or ledger files, and docs that define workflows or validation expectations.

2. Audit installed project-local skills.
   Check these locations relative to the current repo root:
   - `.agents/skills`
   - `.codex/skills`
   - `skills`
   Read both `SKILL.md` and `agents/openai.yaml` when present.
   - If none of these locations exist or they contain no skills, record that explicitly and move on instead of treating the audit as blocked.

3. Audit relevant global and shared skills.
   Resolve the shared-skill roots in this order:
   - `$CODEX_HOME/skills` when `$CODEX_HOME` is set
   - `~/.codex/skills`
   - `~/.agents/skills`
   Review relevant installed skills under each available root, including:
   - `<root>/*/SKILL.md`
   - `<root>/.system/*/SKILL.md`
   - if a root is a symlink farm, resolve the real target path and audit the underlying skill once rather than double-counting the symlinked view and the source directory
   Only open shared skills that are relevant to the current repo or overlap with the local skill surface.

4. Check cheap maintenance signals before deep history.
   For each skill you are seriously evaluating, inspect lightweight staleness signals before opening raw sessions:
   - `git log` for maintenance recency and whether the skill is actively revised
     - if the skill path is inside the current repo, `git log -- <skill-dir>` is fine
     - if the skill lives outside the current repo, run `git log` from the repo
       that owns the skill path, for example
       `git -C <skills-root> log -- <relative-skill-dir>`
   - repo docs or adjacent docs that may have become the real source of truth
   - whether `SKILL.md` and `agents/openai.yaml` still describe the same owner and trigger

5. Read memory and session evidence.
   Resolve evidence roots in this order:
   - `$CODEX_HOME/...` when `$CODEX_HOME` is set
   - `~/.codex/...`
   - `~/.agents/...`
   Use the first existing path for each category. Missing memory files are not blocking.
   Check these locations:
   - `<root>/memories/MEMORY.md`
   - `<root>/memories/rollout_summaries/`
   - `<root>/sessions/`
   Search the memory index first, then open only the 1-3 most relevant rollout summaries.
   Fall back to raw session JSONL only when the summaries are missing exact evidence you need.

6. Inspect current live context when available.
   If the runtime prompt or current turn already exposes relevant prompt context, inspect:
   - skill mentions already present
   - skill bodies or summaries injected into the current turn
   - project docs and other active context competing for prompt budget
   Treat this evidence as opportunistic. Use only what is visible in the current prompt context. Do not invent hidden telemetry or unsupported internal metrics.
- If the repo has no local skills and the current prompt already exposes relevant shared skill metadata or bodies, use that to narrow which shared skills need deeper review instead of insisting on a local-skill-first deep dive.
- If the user asks for only certain skills, keep the audit output limited to
  those skills and explain any skipped portfolio areas as intentionally out of
  scope.

## What To Evaluate

For each installed skill, evaluate:

- current role in the repo or workflow
- whether it matches recurring work actually seen in history
- whether its triggers are too weak, too broad, or stale
- whether its guardrails, validation steps, or paths are outdated
- whether cheap maintenance signals suggest it is stale, under-maintained, or superseded by repo docs
- whether `SKILL.md` and `agents/openai.yaml` drift from each other
- whether it duplicates or overlaps another installed skill
- whether missing project-specific behavior should live in the shared skill, in project docs or memory, or only as a last-resort project-local specialization
- whether it adds prompt weight without enough value when current context exposes that signal

For `skill-audit` itself, also evaluate:

- whether prior audit findings suggest changes to its own workflow or output shape
- whether it is missing useful self-checks or learning loops
- whether it is too weak or too broad in how it evaluates installed skills

## Evidence Workflow

### 1. Search the memory index first

- Resolve the active evidence root first (`$CODEX_HOME`, then `~/.codex`, then `~/.agents`).
- If no `MEMORY.md` exists in any root, record that explicitly and continue; do not treat the audit as blocked.
- Search `MEMORY.md` with `rg` using:
  - repo name
  - repo basename
  - current `cwd`
  - important modules, scripts, or file names
- Capture:
  - repeated workflows
  - repeated validation commands
  - repeated failure modes
  - ownership confusion
  - moments where the same context had to be rediscovered

### 2. Open targeted rollout summaries

- If no rollout summary directory exists in the resolved roots, record that explicitly and move to raw sessions only if needed.
- Prefer summaries whose filenames, `cwd`, or `rollout_path` match the current project.
- Extract:
  - what the user asked for repeatedly
  - which installed skills would have helped
  - what broke repeatedly
  - what commands proved correctness
  - which skill instructions look stale, weak, or missing in hindsight

### 3. Check git history before raw sessions

- Before reading raw session JSONL, inspect git history for the skills under
  review.
- If the skill is inside the current repo, `git log -- <skill-dir>` is enough.
- If the skill lives outside the current repo, first resolve the repo that owns
  the skill path and run git history from there, for example
  `git -C <skills-root> log -- <relative-skill-dir>`.
- Use this as a cheap signal for:
  - whether the skill is actively maintained
  - whether one skill keeps changing while an overlapping skill stays stale
  - whether repo docs are evolving faster than the skill itself
- If git history already explains the likely staleness or ownership gap, prefer that evidence over a deeper session scan.

### 4. Use raw sessions only as a fallback

- Search the resolved `sessions/` JSONL root only when memory, rollout summaries, and git-history signals still do not contain the concrete detail you need.
- Search by:
  - exact `cwd`
  - repo basename
  - thread ID from a rollout summary
  - specific file paths, commands, or failure text
- Use raw sessions to recover exact prompts, command sequences, injected skill evidence, diffs, or failure text.

## Recommendation Types

- `Update`
  Use when a skill is still the right owner but has stale triggers, weak guardrails, metadata drift, missing validation steps, outdated paths, prompt bloat, or poor specialization.

- `Add`
  Use when repeated work exists and no installed skill is a good owner even after evaluating existing local and global skills. Prefer a shared-skill improvement or better project docs before introducing a project-local skill.

- `Merge`
  Use when two installed skills overlap enough that one should absorb, narrow, or specialize the other.

- `Disable`
  Use when a skill is low-value, duplicate, misleading, or not worth its maintenance cost.

## Output Expectations

Return a compact audit with these sections:

1. `Installed skills`
   List the relevant installed project-local and global skills and the current role each one plays.

2. `Evidence summary`
   Summarize the strongest repo, memory, session, and live-context signals that informed the audit.

3. `Per-skill update roadmap`
   For each audited skill, include:
   - skill name
   - scope: `project-local` or `global`
   - current role
   - observed strengths
   - missing or weak behavior
   - evidence source
   - highest-value next update
   - whether the issue should be solved in the shared skill, in project docs or memory, or only as a last-resort project-local specialization

   If `skill-audit` is installed, include an explicit entry for `skill-audit` in this section.

4. `Add / merge / disable candidates`
   List only the candidates justified by evidence after reviewing the installed portfolio.

5. `Priority order`
   Rank the top recommendations by expected value, starting with the most useful update to make next.

## Decision Rules

- Audit project-local skills before global/shared skills.
- Prefer improving an existing installed skill before adding a new one.
- Prefer improving a shared skill when the problem is broadly reusable across projects.
- Prefer project docs, `AGENTS.md`, repo references, or memory when the missing context is project-specific but does not justify a dedicated local skill.
- Recommend a project-local specialization only when the workflow is highly stable, repeatedly needed, and too project-specific to fit cleanly in the shared skill or repo docs.
- Recommend a new skill only after checking whether an installed skill could own the workflow cleanly.
- Treat live context-window analysis as best-effort only; rely only on evidence exposed in the current runtime prompt.
- If `skill-audit` is installed, do not skip its self-audit just because it is the current skill performing the audit.

## Failure Shields

- Do not invent recurring patterns without repo, memory, or session evidence.
- Do not confuse topic recurrence with skill effectiveness.
- Do not recommend disabling a skill without overlap, low-value, or misleading-behavior evidence.
- Do not claim prompt inefficiency unless the current prompt actually exposes that evidence.
- Do not flatten project-local and global skills into one bucket; keep ownership decisions explicit.
- Do not jump to new-skill recommendations before evaluating installed skills as possible owners.
- Do not propose a project-local specialization when the gap is better solved by improving a shared skill or strengthening project docs and memory.
- Do not exempt `skill-audit` from critique; self-review is required when it is installed.
- Do not bulk-load all rollout summaries or raw sessions; stay targeted.
- Do not skip cheap git-history checks and jump straight to raw sessions when staleness is the main question.

## Follow-up

If the user asks to create, merge, or update one of the recommendations, switch to `$skill-creator` and implement the chosen skill change rather than continuing the audit.

## Examples

- "Audit the installed skills in this repo and tell me which ones should be updated first."
- "Review only the skills involved in the current workflow and suggest the highest-value improvements."
- "Before we add a new skill, check whether an installed skill or repo docs should own this workflow instead."
