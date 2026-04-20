---
name: skill-audit
description: Audit repo-maintained or user-specified Codex skills using repo evidence, memory, sessions, and current context to plan updates, additions, merges, or disables. Use when a user asks how the skills maintained in this repo are performing, wants a one-by-one refinement roadmap, asks to audit one or more named skills, or wants evidence-based recommendations before changing skills.
---

# Skill Audit

## Overview

Audit repo-maintained skills before proposing new ones.

Treat the skills maintained in this repository as the primary subject. Prefer
updating, merging, or disabling existing repo-owned skills before recommending
new skills. Treat project-maintained specializations as a last resort.

Default full-scope audits should focus on the skills relevant to the current
workflow in this repo, not arbitrary global installs. Start from current prompt
signals, repo docs, named tasks, and repo-owned skill surfaces.

This skill is Codex-dependent. It may use Codex prompt context, Codex memory
artifacts, rollout summaries, and session JSONL when those are available. Treat
those surfaces as evidence only; the editable source of truth for repo-owned
skills lives in this checkout.

For broad reusable skills, prefer fixing the shared repo skill or relying on
project docs and memory before proposing a project-local variant.

In full-portfolio audits, exclude `skill-audit` from the audited set by
default even if it is relevant to the current workflow. After presenting the
suggestions for the other audited skills, explicitly ask the user whether they
want a follow-up audit of `skill-audit` too.

If the user asks for a narrow audit, such as only the skills used in the
current workflow, honor that scope explicitly instead of expanding to all
repo-owned skills.

If the user explicitly names one or more skills, such as `audit skill $xxx` or
`audit only $foo and $bar`, treat those named skills as the required audit
scope and resolve them before any broader portfolio discovery. In that targeted
mode, audit only the explicitly requested skills and do not add `skill-audit`
unless the user named `skill-audit` too.

## Scope Resolution

- Resolve user-provided scope first.
  - If the user names one or more skills explicitly, those names define the
    primary audit target set.
  - Accept singular or plural phrasing such as `audit skill $foo`, `audit
    skills $foo and $bar`, or `review only $foo`.
- Default full-scope mode is workflow-first and repo-owned.
  - Start from the current workflow in this repo: prompt context, repo docs,
    touched areas, named tasks, and closely related repo-owned skills.
  - Prefer reusable repo skills under `skills/*`.
- Offer project-maintained scope explicitly.
  - Include project-maintained skills under `.agents/skills/*` only when the
    user explicitly asks for them or they are clearly part of the active
    workflow.
  - Treat `.agents/skills/*` as opt-in or workflow-driven, not as a default
    portfolio scan.
- Keep targeted audits targeted.
  - If the user names specific skills, do not expand to a wider repo scan.
  - In that mode, do not auto-include `skill-audit` unless it was explicitly
    requested.
  - Only bring in non-requested skills when needed to explain overlap, merge
    candidates, or ownership conflicts.
- Keep full-portfolio audits scoped too.
  - When auditing the repo-owned portfolio, do not auto-include `skill-audit`
    in the findings.
  - After presenting the non-`skill-audit` recommendations, ask the user
    whether they want to audit `skill-audit` too.
- Be explicit about misses.
  - If a named skill cannot be resolved, say so clearly.
  - Do not silently substitute a near match or widen the audit scope.

## Audit Order

1. Resolve scope and map the current repo surface.
   Identify whether the user named specific skills. If yes, treat them as the
   required audit targets and resolve those names first. In that targeted mode,
   do not add `skill-audit` unless it was explicitly named. If the user asked
   for a full audit, keep `skill-audit` out of the audited set by default and
   plan to ask about it only after presenting the other recommendations. Then
   identify the repo root and read the most relevant project guidance first,
   such as `AGENTS.md`, `README.md`, roadmap or ledger files, and docs that
   define workflow or validation expectations.

2. Audit repo-owned reusable skills first.
   Check reusable skills under `skills/*`. Read both `SKILL.md` and
   `agents/openai.yaml` when present.
   - In default full-scope mode, prioritize only the skills relevant to the
     current workflow instead of auditing every reusable skill mechanically.
   - If the user named specific skills, inspect only the requested skills found
     in `skills/*` instead of broadening the scan.

3. Audit project-maintained skills only when in scope.
   Check `.agents/skills/*` only when the user explicitly asks for
   project-maintained skills or when those skills are clearly involved in the
   current workflow.
   - Read both `SKILL.md` and `agents/openai.yaml` when present.
   - If no project-maintained skills are in scope, record that intentionally
     and move on instead of treating the audit as blocked.

4. Resolve out-of-repo skills only for explicit named targets.
   Do not scan `$CODEX_HOME/skills`, `~/.codex/skills`, or `~/.agents/skills`
   by default.
   - Only resolve a skill outside the repo if the user clearly asks for that
     specific external skill by name.
   - If a resolved root is a symlink farm, audit the underlying skill once
     rather than double-counting both the symlinked view and the source.

5. Check cheap maintenance signals before deep history.
   For each skill you are seriously evaluating, inspect lightweight staleness
   signals before opening raw sessions:
   - `git log` for maintenance recency and whether the skill is actively
     revised
     - if the skill path is inside the current repo, `git log -- <skill-dir>`
       is fine
     - if the skill lives outside the current repo and was explicitly named,
       run `git log` from the repo that owns the skill path, for example
       `git -C <skills-root> log -- <relative-skill-dir>`
   - repo docs or adjacent docs that may have become the real source of truth
   - whether `SKILL.md` and `agents/openai.yaml` still describe the same owner
     and trigger

6. Read memory and session evidence.
   Resolve evidence roots in this order:
   - `$CODEX_HOME/...` when `$CODEX_HOME` is set
   - `~/.codex/...`
   - `~/.agents/...`
   Use the first existing path for each category. Missing memory files are not
   blocking.
   Check these locations:
   - `<root>/memories/MEMORY.md`
   - `<root>/memories/rollout_summaries/`
   - `<root>/sessions/`
   Search the memory index first, then open only the 1-3 most relevant rollout
   summaries. Fall back to raw session JSONL only when the summaries are
   missing exact evidence you need.

7. Inspect current live context when available.
   If the runtime prompt or current turn already exposes relevant prompt
   context, inspect:
   - skill mentions already present
   - skill bodies or summaries injected into the current turn
   - project docs and other active context competing for prompt budget
   Treat this evidence as opportunistic. Use only what is visible in the
   current prompt context. Do not invent hidden telemetry or unsupported
   internal metrics.
   - If the user asks for only certain skills, keep the audit output limited to
     those skills and explain any skipped portfolio areas as intentionally out
     of scope.

## What To Evaluate

For each audited skill, evaluate:

- current role in the repo or workflow
- whether it matches recurring work actually seen in history
- whether its triggers are too weak, too broad, or stale
- whether its guardrails, validation steps, or paths are outdated
- whether cheap maintenance signals suggest it is stale, under-maintained, or
  superseded by repo docs
- whether `SKILL.md` and `agents/openai.yaml` drift from each other
- whether it duplicates or overlaps another repo-owned skill
- whether missing project-specific behavior should live in the reusable skill,
  in project docs or memory, or only as a last-resort project-maintained
  specialization
- whether it adds prompt weight without enough value when current context
  exposes that signal

When `skill-audit` is part of the audited scope, also evaluate:

- whether prior audit findings suggest changes to its own workflow or output
  shape
- whether it is missing useful self-checks or learning loops
- whether it is too weak or too broad in how it evaluates repo-owned skills

## Evidence Workflow

### 1. Search the memory index first

- Resolve the active evidence root first (`$CODEX_HOME`, then `~/.codex`, then
  `~/.agents`).
- If no `MEMORY.md` exists in any root, record that explicitly and continue; do
  not treat the audit as blocked.
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

- If no rollout summary directory exists in the resolved roots, record that
  explicitly and move to raw sessions only if needed.
- Prefer summaries whose filenames, `cwd`, or `rollout_path` match the current
  project.
- Extract:
  - what the user asked for repeatedly
  - which repo-owned skills would have helped
  - what broke repeatedly
  - what commands proved correctness
  - which skill instructions look stale, weak, or missing in hindsight

### 3. Check git history before raw sessions

- Before reading raw session JSONL, inspect git history for the skills under
  review.
- If the skill is inside the current repo, `git log -- <skill-dir>` is enough.
- If the skill lives outside the current repo and was explicitly named, first
  resolve the repo that owns the skill path and run git history from there, for
  example `git -C <skills-root> log -- <relative-skill-dir>`.
- Use this as a cheap signal for:
  - whether the skill is actively maintained
  - whether one skill keeps changing while an overlapping skill stays stale
  - whether repo docs are evolving faster than the skill itself
- If git history already explains the likely staleness or ownership gap, prefer
  that evidence over a deeper session scan.

### 4. Use raw sessions only as a fallback

- Search the resolved `sessions/` JSONL root only when memory, rollout
  summaries, and git-history signals still do not contain the concrete detail
  you need.
- Search by:
  - exact `cwd`
  - repo basename
  - thread ID from a rollout summary
  - specific file paths, commands, or failure text
- Use raw sessions to recover exact prompts, command sequences, injected skill
  evidence, diffs, or failure text.

## Recommendation Types

- `Update`
  Use when a skill is still the right owner but has stale triggers, weak
  guardrails, metadata drift, missing validation steps, outdated paths, prompt
  bloat, or poor specialization.

- `Add`
  Use when repeated work exists and no audited repo-owned skill is a good owner
  even after evaluating existing repo-maintained skills. Prefer a reusable
  skill improvement or better project docs before introducing a
  project-maintained skill.

- `Merge`
  Use when two repo-owned skills overlap enough that one should absorb, narrow,
  or specialize the other.

- `Disable`
  Use when a skill is low-value, duplicate, misleading, or not worth its
  maintenance cost.

## Output Expectations

Return a compact audit with these sections:

1. `Audited repo-owned skills`
   List the audited reusable and project-maintained skills and the current role
   each one plays. If the user named skills explicitly, list only the resolved
   requested skills plus any directly relevant overlap needed to explain the
   recommendation.

2. `Evidence summary`
   Summarize the strongest repo, memory, session, and live-context signals that
   informed the audit.

3. `Per-skill update roadmap`
   For each audited skill, include:
   - skill name
   - scope: `reusable`, `project-maintained`, or `external`
   - current role
   - observed strengths
   - missing or weak behavior
   - evidence source
   - highest-value next update
   - whether the issue should be solved in the reusable skill, in project docs
     or memory, or only as a last-resort project-maintained specialization

   In full-portfolio audits, do not include `skill-audit` in this section
   unless the user explicitly asked to audit it. In user-targeted audits,
   include `skill-audit` only when it was explicitly requested.

4. `Add / merge / disable candidates`
   List only the candidates justified by evidence after reviewing the audited
   scope. For user-targeted audits, do not introduce unrelated portfolio
   candidates.

5. `Priority order`
   Rank the top recommendations by expected value, starting with the most
   useful update to make next.

6. `Follow-up question`
   In full-portfolio audits where `skill-audit` was not explicitly requested,
   end by asking the user whether they want a follow-up audit of `skill-audit`
   too.

## Decision Rules

- Audit repo-owned reusable skills before project-maintained skills.
- When the user names specific skills, treat those named skills as the primary
  and usually exclusive audit scope.
- Resolve user-named skills before broader workflow discovery.
- In full-portfolio audits, exclude `skill-audit` from the audited set unless
  the user explicitly asks for it.
- Prefer improving an existing repo-owned skill before adding a new one.
- Prefer improving a reusable skill when the problem is broadly reusable across
  projects.
- Prefer project docs, `AGENTS.md`, repo references, or memory when the missing
  context is project-specific but does not justify a dedicated skill.
- Recommend a project-maintained specialization only when the workflow is
  highly stable, repeatedly needed, and too project-specific to fit cleanly in
  the reusable skill or repo docs.
- Recommend a new skill only after checking whether an audited repo-owned skill
  could own the workflow cleanly.
- Treat live context-window analysis as best-effort only; rely only on evidence
  exposed in the current runtime prompt.
- Do not substitute a near-match for a user-named skill without saying so
  explicitly.
- Only widen beyond the user-passed skills when overlap, merge, or ownership
  evidence requires it.
- In user-targeted audits, do not auto-append `skill-audit` unless it was
  explicitly requested.
- In full-portfolio audits, after presenting the non-`skill-audit` findings,
  explicitly ask whether the user wants to audit `skill-audit` too.

## Failure Shields

- Do not invent recurring patterns without repo, memory, or session evidence.
- Do not confuse topic recurrence with skill effectiveness.
- Do not recommend disabling a skill without overlap, low-value, or
  misleading-behavior evidence.
- Do not claim prompt inefficiency unless the current prompt actually exposes
  that evidence.
- Do not flatten reusable, project-maintained, and explicitly named external
  skills into one bucket; keep ownership decisions explicit.
- Do not jump to new-skill recommendations before evaluating existing
  repo-owned skills as possible owners.
- Do not propose a project-maintained specialization when the gap is better
  solved by improving a reusable skill or strengthening project docs and
  memory.
- When `skill-audit` is in scope, do not exempt it from critique.
- Do not bulk-load all rollout summaries or raw sessions; stay targeted.
- Do not skip cheap git-history checks and jump straight to raw sessions when
  staleness is the main question.
- Do not silently expand a user-targeted audit into a wider workflow or
  portfolio review.
- Do not auto-append `skill-audit` to a user-targeted audit.
- Do not silently include `skill-audit` findings in a full-portfolio audit.

## Follow-up

If the user asks to create, merge, or update one of the recommendations, switch
to `$skill-creator` and implement the chosen skill change rather than
continuing the audit.

## Examples

- "Audit the repo-maintained skills used in this workflow and tell me which
  ones should be updated first."
- "Review only the skills involved in the current workflow and suggest the
  highest-value improvements."
- "Before we add a new skill, check whether a repo-owned skill or repo docs
  should own this workflow instead."
- "Audit skill $postgres and tell me whether its triggers or references are
  stale."
- "Audit only $Maintainer and $skill-audit and call out any overlap or weak
  guardrails."
