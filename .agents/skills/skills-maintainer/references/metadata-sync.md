# Metadata Sync Playbook

Use this playbook to keep one or more targeted skills' `SKILL.md`, `agents/openai.yaml`, and top-level docs aligned.

## Task Boundary (Sync Only)
- `sync` aligns metadata and docs only.
- Do not run structure/policy compliance checks here (those belong to `audit`).
- Do not run upstream comparison here (that belongs to `benchmark`).
- Do not run Postgres best-practices refresh here (that belongs to `refresh`).

## Canonical Source Order
When fields drift, resolve in this order:
1. `SKILL.md` frontmatter (`name`, `description`) is canonical for skill identity/purpose.
2. `agents/openai.yaml` should stay semantically aligned for UI text (`display_name`, `short_description`, `default_prompt`).
3. `README.md` one-liners should mirror the same user-facing purpose as metadata.

## What to Align
- Skill identity and purpose (`name`, `description`, display labels)
- Trigger intent in `SKILL.md` vs UI-facing `short_description`
- README skill list and one-line descriptions
- Any install prompts or usage snippets that list skill names

## Workflow
1. Enumerate skill manifests:
   - `find . -type f -name 'SKILL.md' -not -path '*/.git/*' -not -path '*/.cache/*' | sort`
   - `find . -type f -path '*/agents/openai.yaml' -not -path '*/.git/*' -not -path '*/.cache/*' | sort`
2. For each targeted skill, compare:
   - `SKILL.md` frontmatter `name` and `description`
   - `agents/openai.yaml` interface fields (`display_name`, `short_description`, `default_prompt`)
   - README entry wording for that skill
3. Update mismatches with minimal wording drift.
4. Reconcile README lists so added, removed, or renamed skills are reflected.
5. Confirm descriptions remain one-line and user-facing in README/openai metadata.

## Parallel Subagent Pattern
- Use this only when subagent tools are available and the user explicitly asked for delegation or parallel agent work.
- After manifest enumeration, spawn multiple explorer subagents for independent inspection slices:
  - one for `SKILL.md` frontmatter and trigger wording
  - one for `agents/openai.yaml` display text and prompt alignment
  - one for `README.md` entries and install-prompt references
- Integrate findings and apply wording updates in one local pass so the final language stays coherent.
- Do not split overlapping edits in the same paragraph or list across multiple worker subagents.

## Quality Gates
- Every listed skill has both `SKILL.md` and `agents/openai.yaml`.
- No stale skill names remain in README/install prompts.
- Description changes preserve original intent while improving consistency.
- `PASS`: no metadata/doc drift remains.
- `FAIL`: unresolved drift in any of `SKILL.md`, `agents/openai.yaml`, or README mapping.
