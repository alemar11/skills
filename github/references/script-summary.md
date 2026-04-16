# GitHub script summary

Use this as the top-level runtime and command-map index referenced by
`github/SKILL.md`.

## Public runtime

- `scripts/ghops` is the only supported runtime entrypoint.
- If the current checkout does not ship `scripts/ghops`, resolve the installed
  `github` skill root and run `<skill-root>/scripts/ghops`.
- Start with `scripts/ghops --version` and
  `scripts/ghops --json doctor`.
- Treat the domain catalogs below as `ghops` command maps and runbooks, not as
  separate runtime entrypoints.

## Domain catalogs

- Core setup, auth, and retry helpers:
  `references/core/installation.md`
- Triage helpers for repos, issues, PR metadata, patches, reactions, and
  issue-link wording, plus authenticated-user stars and star lists:
  `references/triage/script-summary.md`
- Review helpers for actionable review threads, replies, and review
  submission:
  `references/reviews/script-summary.md`
- CI helpers for PR checks and generic GitHub Actions investigation:
  `references/ci/script-summary.md`
- Release helpers for planning, notes generation, and release publication:
  `references/releases/script-summary.md`
- Publish helpers for current-branch PR open or reuse and PR lifecycle
  mutations:
  `references/publish/script-summary.md`

## Fast picks

- Runtime readiness: `scripts/ghops --json doctor`
- Routine triage: `scripts/ghops repos view`,
  `scripts/ghops issues view --issue <n>`,
  `scripts/ghops prs view --pr <n>`
- Personal stars and star lists: `scripts/ghops --json stars list`,
  `scripts/ghops --json lists list`
- Actionable review feedback: `scripts/ghops reviews address --pr <n>`
- PR checks and Actions: `scripts/ghops --json checks pr --pr <n>`,
  `scripts/ghops --json actions list`
- Release planning: `scripts/ghops releases plan`
- Already-pushed branch to PR: `scripts/ghops --json publish context`,
  `scripts/ghops publish open`
