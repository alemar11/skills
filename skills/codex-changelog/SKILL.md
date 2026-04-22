---
name: codex-changelog
description: Check the installed Codex CLI and Codex App versions, then print separate changelog sections for the CLI from GitHub Releases and the app from the OpenAI Codex changelog page.
---

# Codex Changelog

## Goal

Resolve the installed Codex CLI and Codex App versions and return two sections:
- `Codex CLI`: the matching GitHub release changelog from `openai/codex/releases`
- `Codex App`: the matching desktop-app changelog from `https://developers.openai.com/codex/changelog`

## Runtime surface

- The supported runtime entrypoint is the shipped
  `scripts/print_codex_changelog.py` helper inside this skill package.
- If your current working directory is the skill root, run it as
  `python3 scripts/print_codex_changelog.py`.
- If you are invoking the skill from another repo, resolve the installed skill
  root first and run
  `python3 <codex-changelog-skill-root>/scripts/print_codex_changelog.py`.

## Trigger rules

- Use when the user asks for Codex version, release notes, or changelog details for the CLI, app, or both.
- Prefer this skill for installed-version changelog lookups instead of ad-hoc browsing.
- Always fetch Codex CLI notes from GitHub Releases, even though the OpenAI changelog page also lists CLI entries.
- If no installed CLI or app version can be resolved, report the failure and provide the nearest fallback tags or app versions.

## Workflow

1. Run the shipped helper from this skill package:
   `python3 <codex-changelog-skill-root>/scripts/print_codex_changelog.py`.
2. Share the printed changelog with the user in two sections: `Codex CLI` and `Codex App`.
3. For `Codex CLI`, use the current GitHub-release lookup flow against `openai/codex/releases`.
4. For `Codex App`, fetch desktop-app entries from `https://developers.openai.com/codex/changelog` and match the installed app version when possible.
5. If no exact CLI tag or app version is found, report the attempted tags or versions and include the latest relevant fallback entry.

## Script

- `scripts/print_codex_changelog.py`: the shipped skill helper that resolves the
  local Codex CLI version via `codex --version`, resolves the installed Codex
  App version from the local macOS app bundle, fetches CLI notes from GitHub
  Releases, fetches app notes from the OpenAI Codex changelog page, and prints
  both sections.
