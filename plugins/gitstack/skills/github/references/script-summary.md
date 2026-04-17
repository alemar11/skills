# GitHub script summary

Use this as the top-level runtime and command-map index referenced by the
bundled `github` skill.

## Public runtime

- `ghops` is the only supported runtime entrypoint.
- If the current checkout does not ship `ghops`, resolve the installed
  plugin root and run `ghops`.
- Start with `ghops --version` and
  `ghops --json doctor`.
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

- Runtime readiness: `ghops --json doctor`
- Routine triage: `ghops repos view`,
  `ghops issues view --issue <n>`,
  `ghops prs view --pr <n>`
- Personal stars and star lists: `ghops --json stars list`,
  `ghops --json lists list`
- Actionable review feedback: `ghops reviews address --pr <n>`
- PR checks and Actions: `ghops --json checks pr --pr <n>`,
  `ghops --json actions list`
- Release planning: `ghops releases plan`
- Already-pushed branch to PR: `ghops --json publish context`,
  `ghops publish open`
