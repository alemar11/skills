---
name: github-releases
description: "Inspect, draft, publish, or update GitHub Releases, notes, assets, and package availability."
---

# GitHub Releases

Before any shell command that may contact GitHub or a package registry, read
and follow [Network execution](../../references/network-execution.md).

## Transport

Use authenticated `gh` for every GitHub provider read and write. Use file-backed
`gh api --input` requests whenever a mutation includes a curated title, body,
or other free-form provider text.

Before the first provider-facing direct `gh` or shared CLI operation, load
[`../../references/gh-dependency-preflight.md`](../../references/gh-dependency-preflight.md)
and require its host and authentication checks.

## Role

Handle release work with direct `git`, `gh release`, and registry/package
commands. This skill is scriptless by design.

Use this skill for release readiness, tag checks, generated or curated notes,
release-description improvements, release asset inspection, draft or published
GitHub Releases, and package availability confirmation.

## Workflow

1. Confirm the repository and default branch.
2. Inspect tags and existing releases before creating anything.
3. Accept an exact tag from the caller. When `$g:versioning` selected it, retain
   that skill's verified target and comparison range; do not recalculate its
   SemVer policy inside this provider-primitive skill.
4. Compare the intended version against package manifests or changelog files
   only when that repository maintains them and the operation is not the
   application-code-blind versioning controller.
5. Treat release creation, tag creation, description updates, asset upload,
   publishing, and deletion
   as mutations that require explicit user authorization. For a requested
   write without that authorization, resolve `mutation_mode=dry-run` and return
   the proposed command or draft release notes only.
6. Resolve the requested action to
   `release_operation=inspect|create-tag|draft|publish|update-notes|upload-asset|delete`.
   Omit `mutation_mode` for `inspect`; for a write-shaped operation, resolve
   `mutation_mode=apply|dry-run` before using `gh release create
   --generate-notes` or another mutating command.
7. Apply these creation defaults:
   - `create a release` prepares the exact notes and creates a draft with
     `release_operation=draft`; ask only when a material choice is unresolved;
   - an explicit `create and publish` request resolves directly to
     `release_operation=publish` and `mutation_mode=apply`; it skips the notes
     preview and draft stage without skipping readiness or verification;
   - a preview-only request creates no draft; draft creation is a mutation.
8. For `release_operation=update-notes`, inspect the existing title and body,
   prepare the exact replacement or diff, honor authorization for the
   requested update, change only those text fields, and verify exact readback. Direct create-and-publish
   authority does not carry over to a later notes update.
9. After a mutation, verify the resulting tag, GitHub Release, notes, asset
   state, and any package registry availability requested by the user.

## References

- `references/workflows.md`: release, tag, notes, and asset workflows.
- `references/states.md`: release lifecycle and transient planning states.
- `references/package-checks.md`: registry availability checks.
- `../../references/options.md`: shared canonical G options.
