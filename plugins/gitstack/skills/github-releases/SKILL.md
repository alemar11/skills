---
name: github-releases
description: Use the shared `ghops` CLI bundled in the `gitstack` plugin for release planning, notes generation, and release publication.
---

# GitHub Releases

## Overview

Use this bundled skill when the request is about release-backed tags, notes
generation, release planning, or release publication.

The shared runtime lives at `ghops`. Keep tag-only or
local publish orchestration decisions aligned with the umbrella `github` skill
and `yeet`.

## Fast path

- `ghops --json doctor`
- `ghops releases plan --repo <owner/repo>`
- `ghops releases notes --tag <tag> --target-ref <branch-or-sha> --repo <owner/repo>`
- `ghops releases create --tag <tag> --target-ref <branch-or-sha> --notes-mode <infer|blank|user> --repo <owner/repo>`

## Trigger rules

- Use for release planning, notes generation, and release publication.
- Resolve target refs explicitly; do not guess `main`.
- Keep generic GitHub routing in the umbrella `github`.

## References navigation

- Start at `references/script-summary.md` for the releases command map.
- Open `references/workflows.md` for release-backed tag and notes flows.
