# Metadata Sync Playbook

Use this playbook to keep each skill's `SKILL.md`, `agents/openai.yaml`, and top-level docs aligned.

## What to Align
- Skill identity and purpose (`name`, `description`, display labels)
- Trigger intent in `SKILL.md` vs UI-facing `short_description`
- README skill list and one-line descriptions
- Any install prompts or usage snippets that list skill names

## Workflow
1. Enumerate skill manifests:
   - `find . -type f -name 'SKILL.md' -not -path '*/.git/*' | sort`
   - `find . -type f -path '*/agents/openai.yaml' -not -path '*/.git/*' | sort`
2. For each skill, compare:
   - `SKILL.md` frontmatter `name` and `description`
   - `agents/openai.yaml` interface fields (`display_name`, `short_description`, `default_prompt`)
3. Update mismatches with minimal wording drift.
4. Reconcile README lists so added/removed skills are reflected.
5. Confirm descriptions remain one-line and user-facing in README/openai metadata.

## Quality Gates
- Every listed skill has both `SKILL.md` and `agents/openai.yaml`.
- No stale skill names remain in README/install prompts.
- Description changes preserve original intent while improving consistency.
