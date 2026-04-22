# GitHub script summary

Use this as the top-level runtime and command-map index referenced by the
bundled `github` skill.

## Public runtime

- Start with `ghflow --version`.
- Treat `ghflow` as a narrow shared-helper surface, not as a replacement for
  `gh` or `git`.
- Prefer plain `gh` and `git` for routine repository, issue, PR, CI, and
  release work.

## Shared `ghflow` helpers

- Failing-PR CI inspection: `ghflow ci inspect`
- Review-thread triage and reply routing: `ghflow reviews address`
- Authenticated-user stars and star lists:
  `ghflow stars <list|add|remove>`,
  `ghflow stars lists <list|items|delete|assign|unassign>`
- Already-pushed current-branch PR context and open-or-reuse:
  `ghflow publish context`, `ghflow publish open`

## Domain catalogs

- Core setup, auth, and retry helpers: `references/core/installation.md`
- Triage helpers: `references/triage/script-summary.md`
- Review helpers: `references/reviews/script-summary.md`
- CI guidance: `references/ci/script-summary.md`
- Release guidance: `references/releases/script-summary.md`
- Publish helpers: `references/publish/script-summary.md`
