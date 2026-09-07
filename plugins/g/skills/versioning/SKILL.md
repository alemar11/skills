---
name: versioning
description: "Select SemVer versions and tags, migrate legacy tags, or author guarded release-tag workflows."
---

# Versioning

Use this skill for release versions, Git tags, stabilization branches, tag
suggestions, stable legacy-tag migration, and guarded GitHub Actions that apply
this convention without touching application code.

This skill owns the convention, read-only calculation, and explicit migration
of stable legacy tags. It never moves or deletes a tag. Its helper only creates
previews; applying any tag is a separate mutation that requires explicit
confirmation of the exact proposal. Creating a canonical alias is subject to
the same gate and requires source and target verification before and after the
write.

## Terms and routing

Keep these objects distinct:

- a **version** is a SemVer value such as `2.4.0` or `2.4.0-rc.1`;
- a **Git tag** is the repository ref for that version, such as `v2.4.0`;
- a **GitHub Release** is provider metadata attached to one existing Git tag.

A release candidate is a prerelease version and tag, not a GitHub Release.
Route by the user's requested outcome and read only the references selected by
that branch:

| Request | Required reference |
| --- | --- |
| Interpret or validate a version, tag, or release branch | [SemVer and tag format](references/semver.md) |
| Calculate patch, minor, major, candidate, or final proposals | [Suggestion workflow](references/suggestions.md) and [suggestion states](references/states.md) |
| Inspect or migrate stable legacy tags | [Legacy-tag migration](references/migration.md) and [suggestion states](references/states.md) |
| Apply a confirmed tag through an existing compatible controller | [Existing release-controller dispatch](references/controller-dispatch.md) |
| Select an existing tag for a GitHub Release | [GitHub Release tag selection](references/release-selection.md), then the [$g:github-releases workflow](../github-releases/references/workflows.md) |
| Create, review, or upgrade release Actions | [GitHub Actions configuration preflight](../github-actions/references/configuration.md), then [release workflow authoring](references/github-actions.md) |

An explicit increment, candidate, final tag, or release branch selects the
version-and-tag path. An explicit existing tag, GitHub Release, description,
notes, or assets selects the GitHub Release path. If the word “release” does
not distinguish them, ask whether the user wants a new version/tag or a GitHub
Release for an existing tag before proposing or mutating anything.

## Canonical gate

New G tags are exactly `vX.Y.Z` or `vX.Y.Z-rc.N`; stabilization branches are
`release/vX.Y.Z`. Read [the canonical convention](references/semver.md) before
interpreting or validating a requested tag.

Before any tag enters confirmation or mutation, validate its exact spelling:

```bash
scripts/version-suggestions --mode validate --application-tag <tag> --json
```

Only `canonical-format` may proceed. `blocked-noncanonical` is terminal even
when the user confirms or asks to preserve a project convention. Explain the
mismatch, but never silently normalize it or reuse authority for the rejected
tag. A canonical replacement is a new proposal requiring its own confirmation.
Legacy tags without `v` remain read-only calculation or migration sources.

## Runtime workflow

1. Inspect the current branch, `HEAD`, working tree, local and remote tag view,
   relevant provider state, and the user's explicit version or release intent.
   Refresh stale remote state; the helper never fetches or writes implicitly.
2. Select the route above and read only its required references.
3. Run `scripts/version-suggestions` in the relevant mode. Interpret every
   returned status through [the canonical state registry](references/states.md).
4. For a read-only request, report the resolved context, exact proposals, and
   blocking state without entering a mutation path.
5. For tag application, validate the exact tag and show a preview containing
   the tag, operation, target commit, selected branch or ref, and relevant
   source ref. Ask for explicit confirmation of that exact proposal.
6. Immediately before a confirmed write, refresh the authoritative refs and
   re-run exact-tag validation. Stop on drift, ambiguity, an existing tag at a
   different commit, a finalized release line, or any noncanonical result.
7. Prefer a compatible installed approval-gated release controller and read
   [its dispatch contract](references/controller-dispatch.md) before starting
   it. When none exists, use the direct tag workflow owned by
   `$g:github-releases`. Verify the resulting ref and commit independently.

If the current branch is neither the provider's default branch nor an exact
`release/vX.Y.Z` branch and the user supplied no clear version or migration
intent, show the read-only context and ask which release line to use.

Controller dispatch authorizes only the confirmed run. It never authorizes
approving the protected environment, bypassing reviewers, publishing a GitHub
Release, or manually starting a recovery-only publisher. A final tag and its
GitHub Release are separate operations and must each remain within the user's
confirmed scope.

## GitHub Actions authoring boundary

Create or upgrade release Actions only when explicitly requested. The
[authoring reference](references/github-actions.md) owns the portable topology,
interfaces, resolver lifecycle, application-code boundary, validation, and
recovery behavior. Run its linked read-only permissions preflight first and
report local implementation separately from remote operational readiness.

## Result contract

Report the selected version, exact tag, branch or ref, commit SHA, derived
state, and whether the result is only a proposal or an independently verified
mutation. Keep user intent, immediate provider receipts, and verified final
state distinct. For GitHub Releases, also report the selected existing tag and
comparison start before handing off to `$g:github-releases`.
