---
name: github
description: "Route GitHub requests spanning multiple domains to the relevant G skills."
---

# GitHub

Before any shell command that may contact GitHub or a package registry, read
and follow [Network execution](../../references/network-execution.md).

Before the first provider-facing direct `gh` or `<plugin-root>/scripts/g`
operation, load
[`../../references/gh-dependency-preflight.md`](../../references/gh-dependency-preflight.md).
Stack operations additionally require the exact `github/gh-stack` readiness
check owned by that reference.

## Role

Use this plugin-only umbrella when a GitHub request is mixed, ambiguous, or
spans multiple lifecycle stages. Route focused work to the smallest bundled
skill and keep that skill's authority and safety rules intact.

## Transport

Use direct `git` for local repository operations and authenticated `gh`, directly
or through `<plugin-root>/scripts/g`, for GitHub. Resolve the plugin root two
directories above the directory containing this file. For stacks, route to
`g:github-stack`; installation requires explicit authorization.

## Routing

| Request | Bundled skill |
| --- | --- |
| Local staging or commit, optionally push without PR | `$g:git-commit` |
| Send local work as a branch and draft PR | `$g:send` |
| Stacked PR branch/stack lifecycle | `$g:github-stack` |
| Issue and PR queue triage for one or more repositories | `$g:github-repository-triage` |
| Content-based issue classification or explicit read-only taxonomy proposals | `$g:github-issues` |
| GitHub issue lifecycle and relationships | `$g:github-issues` |
| GitHub Projects, fields, items, repository/team links, or templates | `$g:github-projects` |
| Evidence-backed technical review of an issue, PR, or proposed fix | `$g:github-investigation` |
| Actions inspection or explicit CI repair | `$g:github-actions` |
| Exact-head PR delivery readiness, merge policy, rulesets, checks, queue, and automation state | `$g:github-delivery-status` |
| Automated review check/wait, review feedback, implementation, replies, resolution | `$g:github-review-threads` |
| Tags, releases, notes, assets, packages | `$g:github-releases` |
| Stars and star lists | `$g:github-stars` |

Do not load every specialist. Select the smallest owner, then return here only
if the work crosses domains.
