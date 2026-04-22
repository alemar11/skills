---
name: learn
description: Capture durable corrections or preferences and write confirmed learnings only to AGENTS.md. Use when the user sets lasting guidance.
---

# Learn From Mistakes

## Runtime surface

- The only helper-script entrypoint is the shipped
  `scripts/extract_recent_transcript.py` artifact inside this skill package.
- If your current working directory is the skill root, run it as
  `scripts/extract_recent_transcript.py`.
- If you are invoking the skill from another repo, resolve the installed skill
  root first and run
  `<learn-skill-root>/scripts/extract_recent_transcript.py`.

## Trigger rules
- Use when the user states a durable correction, preference, or policy that should persist across future work.
- Do not use for one-off instructions limited to the current task or files.
- This skill only writes to `AGENTS.md`; never write or update `MEMORY.md`, `memory_summary.md`, or other memory files.
- Always confirm the target AGENTS.md and intended wording before writing durable guidance.

## Quick flow
- Find the most recent **durable** correction/avoidance/preference in the current conversation.
- Determine scope before proposing a target:
  - If the rule is clearly **project-specific** (e.g., tied to repo structure, tooling, or workflows), suggest **project** AGENTS.md first.
  - Otherwise, default to **global** unless the user explicitly says "project", "project-root", or "workspace".
  - Do not pick local just because it exists.
- If the learning is new (not already in AGENTS.md), propose:
  - Short summary (1 line)
  - Detailed instruction (1–3 bullets)
- Confirmation should be lightweight: state what you will write and where.
- Assume it is durable and that global is OK unless the user says otherwise. User can reply "no", "stop", "project", or similar to change/cancel.
- If nothing new is found in context (or it already exists), run the shipped
  helper script from this skill package, scan the JSONL from the last user
  message backward to find the most recent **durable** correction, then repeat
  the steps above.
- After this flow finishes, do not continue writing durable changes into AGENTS.md without following the steps above.
- Always confirm before writing into AGENTS.md when triggered by a durable preference.

## Durability filter
- Keep long-lived preferences and permanent mistake corrections.
- Exclude one-off or context-specific instructions tied only to the current task/files.
- Examples:
  - Project-specific: “Use `pnpm` in this repo,” “Update `docs/ARCHITECTURE.md` when changing auth.”
  - Global: “Always use `rg` for file search,” “Ask before writing to AGENTS.md.”

## Docs vs AGENTS
- Before proposing an `AGENTS.md` write, check whether the guidance is better owned elsewhere.
- Prefer repo docs when the guidance should be visible to humans, is tightly coupled to current tooling/workflows, or is likely to change with the codebase.
- Use `AGENTS.md` only when the rule is both durable and agent-facing for that scope.
- If repo docs are the better owner, recommend that path instead of writing `AGENTS.md`.

## AGENTS.md write
- Prefer the most appropriate existing section for the rule's topic or scope.
- If no appropriate section exists, create a concise section that matches the topic or scope.
- Use section `## Codex Learnings` only as a fallback when no better section fits.
- Bullets should be concise and specific ("Avoid X" / "Do Y instead of Z").
- Append ` (Codex learning)` to every bullet inserted by this skill.
- Skip duplicates. If a conflict exists, ask how to resolve before writing.

## Target labels
- **global** (default): `~/.codex/AGENTS.md`
- **project**: `AGENTS.md` at repo root (or cwd if no repo)
- If both repo root and cwd have AGENTS.md, label them **project-root** and **workspace**.
- If multiple AGENTS.md exist in subfolders, consider whether the rule is better scoped to a sub-area:
  - If the rule is likely relevant to the current project but scoped to a specific subfolder, suggest the closest existing sub-AGENTS.md first.
  - If no sub-AGENTS.md exists, propose the repo AGENTS.md first.
  - Always show the full path when suggesting a sub-AGENTS.md so the user can evaluate the scope.
  - Always leave the final choice to the user.
- If the chosen target does not exist, ask to create it (still default to global unless user says otherwise).

## Script output
`scripts/extract_recent_transcript.py` returns JSON with `session_id`,
`rollout_path`, `cwd`, and AGENTS.md candidates/suggestions.
