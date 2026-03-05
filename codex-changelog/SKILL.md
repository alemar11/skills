---
name: codex-changelog
description: Check the installed Codex CLI version and fetch/print the matching GitHub Releases changelog from https://github.com/openai/codex/releases. Use when users ask for their Codex version, release notes, or changelog for the installed CLI.
---

# Codex Changelog

## Goal

Resolve the installed Codex CLI version and return the matching GitHub release changelog so the user gets version-accurate notes.

## Trigger rules

- Use when the user asks for Codex CLI version, release notes, or changelog details.
- Prefer this skill for installed-version changelog lookups instead of ad-hoc GitHub browsing.
- If no installed version can be resolved, report the failure and provide nearest fallback tags.

## Workflow

1. Run `python3 scripts/print_codex_changelog.py`.
2. Share the printed changelog with the user.
3. If no matching release tag is found, report the tags that were attempted and offer to list recent releases.

## Script

- `scripts/print_codex_changelog.py`: Resolves the local Codex CLI version via `codex --version`, fetches the matching GitHub release, and prints its changelog body.
