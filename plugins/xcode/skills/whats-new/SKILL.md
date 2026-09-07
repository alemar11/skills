---
name: whats-new
description: "Read official release notes for the active, latest, or requested stable or beta Xcode."
---

# Xcode What's New

Resolve the active Xcode version, a user-requested stable or beta version, or
list the available Apple Xcode Release Notes entries. For active local Xcode
reports, include the installed version's release notes plus the latest stable
and latest beta notes when they are distinct from the installed entry.

## Runtime

Use the shipped `scripts/print_xcode_changelog.py` helper. Resolve the installed
skill root when invoking it from another repository. Before selecting a lookup
path, read the canonical [state model](references/states.md).

## Workflow

1. For the active local Xcode, run:
   `python3 <xcode-whats-new-skill-root>/scripts/print_xcode_changelog.py`.
   It includes distinct latest stable and beta entries when available.
2. For a requested version, run
   `python3 <xcode-whats-new-skill-root>/scripts/print_xcode_changelog.py --version "<version label>"`.
   Preserve the requested channel. A numbered beta must match exactly.
3. To list available versions, run
   `python3 <xcode-whats-new-skill-root>/scripts/print_xcode_changelog.py --list`.
4. Share the script's single `Xcode` section, including every `Source:` URL and
   any normalization or fallback explanation.

This skill requires macOS, `python3`, `xcodebuild`, `xcode-select`, `plutil`,
and network access to Apple's documentation.
