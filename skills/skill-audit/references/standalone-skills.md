# Standalone Skill Audits

Use this workflow for standalone skills under project-local, shared, or global
skill roots.

## Resolution

- Check project-local roots first:
  - `.agents/skills`
  - `.codex/skills`
  - `skills`
- Widen to shared/global roots only when needed:
  - `$CODEX_HOME/skills` when `$CODEX_HOME` is set
  - `~/.codex/skills`
  - `~/.agents/skills`
- If a root is a symlink farm, resolve the underlying skill once rather than
  double-counting both the symlinked view and the source.

## What To Inspect

- `SKILL.md`
- `agents/openai.yaml` when present
- directly coupled `references/*`, `scripts/*`, or `assets/*` only when needed
  to answer the audit question
- repo docs or adjacent docs that may have become the real source of truth

## What To Evaluate

- current role in the repo or workflow
- whether it matches recurring work actually seen in history
- whether its triggers are too weak, too broad, or stale
- whether its guardrails, validation steps, or paths are outdated
- whether `SKILL.md` and `agents/openai.yaml` drift from each other
- whether it duplicates or overlaps another installed or shared skill
- whether missing project-specific behavior should live in the reusable skill,
  in project docs or memory, or only as a last-resort project-maintained
  specialization
- whether it adds prompt weight without enough value when current context
  exposes that signal

## Evidence Workflow

1. Search the memory index first.
   - Search `MEMORY.md` with `rg` using repo name, repo basename, current
     `cwd`, skill names, and important files.
2. Open targeted rollout summaries.
   - Prefer summaries whose filenames, `cwd`, or `rollout_path` match the
     project or skill name.
3. Check cheap maintenance signals before raw sessions.
   - Use `git log -- <skill-dir>` for local skills.
   - If the skill lives outside the current repo, use `git -C <skills-root> log
     -- <relative-skill-dir>` when the owning repo is available.
4. Use raw sessions when behavior is in question, and as a fallback otherwise.
   - Search by skill name, `SKILL.md` path, `agents/openai.yaml` path, prompt
     text such as `Use $skill-name`, exact `cwd`, repo basename, thread ID from
     a rollout summary, or specific failure text.

## Ownership Guidance

- Put findings on `skill` when the problem is in the skill contract,
  references, scripts, or metadata.
- Put findings on `docs` when the missing context is project-specific but does
  not justify a skill change.
- If overlap exists with a bundled plugin skill or plugin package, call that
  out explicitly instead of forcing a skill-only conclusion.
