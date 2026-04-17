# GitHub release workflows

Use this reference for release-backed tags, tag-only flows, target resolution,
and release publication.

## release-or-tag-create

Purpose: create a release-backed tag or a tag-only ref without guessing the
target branch or commit.

### Preconditions

- `gh` installed and authenticated.
- Repository scope is known.
- If working from a local clone, run `scripts/ghops --json doctor` first when
  repo context is uncertain.
- For tag-only creation with `git tag`, work from a local clone of the target
  repository.

### Operator policy

- Decide release-backed tag versus tag-only before choosing commands.
- Never assume `main`; resolve the repository default branch explicitly.
- Show the proposed default branch, target branch, target commit short SHA, and
  target commit subject before mutating when the user did not name a target.
- Keep the exact three notes choices for releases:
  infer from the last published release tag, keep blank, or use user-provided
  notes.
- Use `scripts/ghops releases notes` when the user wants inferred notes and
  should see the draft before publishing.
- Use `scripts/ghops releases create` for release publication because it
  requires explicit `--target-ref` and explicit `--notes-mode`.
- For tag-only creation from a local clone, use `git tag` plus
  `git push origin <tag>`.
- Use `gh api` for tag-only creation only when the user explicitly wants the
  API path.

### Preferred command path

```bash
scripts/ghops releases plan [--repo <owner/repo>] [--target-branch <branch>]
scripts/ghops releases notes --tag <tag> --target-ref <branch-or-sha> [--repo <owner/repo>] [--previous-tag <tag>]
scripts/ghops releases create --tag <tag> --target-ref <branch-or-sha> --notes-mode <infer|blank|user> [--repo <owner/repo>]
```

## Retry notes

- Auth/session errors: `gh auth login && scripts/ghops --json doctor`
- Repository mismatch errors: rerun the command from the target repo root or
  pass `--repo owner/repo` explicitly.
- Release notes generation failures: rerun
  `scripts/ghops releases notes --tag <tag> --target-ref <branch-or-sha> [--repo <owner/repo>]`
  after confirming the previous tag and target ref.
