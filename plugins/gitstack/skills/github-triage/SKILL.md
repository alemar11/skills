---
name: github-triage
description: Use the shared `ghops` CLI bundled in the `gitstack` plugin for repository orientation, issues, PR metadata, reactions, stars, and lists.
---

# GitHub Triage

## Overview

Use this bundled skill when the request is clearly about repo orientation,
issues, PR metadata, reactions, or authenticated-user stars and star lists.

The shared runtime lives at `ghops`. Route mixed-domain
or publish-lifecycle work back to the umbrella `github` skill.

## Fast path

- `ghops --json doctor`
- `ghops repos view`
- `ghops issues view --issue <n> --repo <owner/repo>`
- `ghops prs view --pr <n> --repo <owner/repo>`
- `ghops --json reactions list --resource pr --repo <owner/repo> --number <n>`
- `ghops --json stars list`
- `ghops --json lists list`

## Trigger rules

- Use for repository orientation, issues, PR metadata, reactions, stars, and
  lists.
- Keep review follow-up in `github-reviews`.
- Keep CI and Actions work in `github-ci`.
- Keep release creation and planning in `github-releases`.
- Keep publish lifecycle on already-pushed branches in the umbrella `github`.

## References navigation

- Start at `references/script-summary.md` for the triage command map.
- Open `references/workflows.md` for triage-domain runbooks.
- Open `references/issue-workflows.md` when issue copy, move, or close-with-
  evidence behavior matters.
- Open `references/github_workflow_behaviors.md` for GitHub-specific behavior
  notes that affect triage results.
