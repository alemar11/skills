---
name: github-releases
description: Plan and create GitHub releases and tags with explicit target resolution and notes strategy through repo-owned `gh` helpers.
---

# GitHub Releases

## Overview

Use this skill for release-backed tags, tag-only flows, target resolution,
release-note generation, and release publication. It keeps release-backed-tag
and tag-only choice in one place so target and notes behavior stay consistent.

Prefer the repo-owned release helpers first. Keep issue work, reactions,
review-thread work, CI debugging, and PR lifecycle mutations out of this
skill.

## Trigger rules

- Use when the user asks to create a GitHub release, publish release notes,
  generate release notes, create a tag only, or confirm the branch/commit for
  a release-backed tag.
- Always decide release-backed tag versus tag-only first.
- Always resolve the target branch and exact target SHA before mutation.
- Always choose a notes strategy before release publication.

## Workflow

1. Resolve repository scope and decide whether the request is release-backed or
   tag-only.
2. Use `scripts/release_plan.sh` to resolve the default branch, target branch,
   target commit, and latest published release tag.
3. If the request is a release and notes should be inferred, use
   `scripts/release_notes_generate.sh` to prepare draft notes first.
4. Use `scripts/release_create.sh` for the release mutation because it
   requires explicit `--target-ref` and explicit `--notes-mode`.
5. For tag-only creation from a local clone, use `git tag` plus
   `git push origin <tag>`. Use `gh api` only when the user explicitly wants
   the API path.
6. Report the chosen notes strategy, resolved target SHA, previous tag used for
   note generation when applicable, and the final release or tag result.

## Guardrails

- Never rely on implicit `gh release create` target selection.
- Do not treat user silence as delegation for the notes strategy.
- Keep the exact three notes choices when the user has not decided:
  infer from the last published release tag, keep blank, or use user-provided
  notes.
- Keep tag-only flows in this skill instead of splitting them away from
  release-backed-tag planning.

## Fast paths

- Use `scripts/release_plan.sh` before any release mutation.
- Use `scripts/release_notes_generate.sh` when inferred notes should be shown
  before publication.
- Use `scripts/release_create.sh` for the mutation step.

## Reference map

- `references/script-summary.md`: release-owned helper catalog and flags.
- `references/workflows.md`: target resolution, notes strategy, tag-only
  guidance, and release publication flow.

## Examples

- "Create a release for this tag, but confirm the target branch and notes strategy first."
- "Generate release notes since the last published release tag."
- "Create a tag only on the default branch head."
