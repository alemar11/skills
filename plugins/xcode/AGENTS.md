# Xcode Plugin Maintenance

This package owns the bundled Xcode skills and their release contract.

- Keep normal What's New runtime execution on
  `skills/whats-new/scripts/print_xcode_changelog.py`; there is no separate
  build project or generated runtime artifact.
- Treat `.codex-plugin/plugin.json` as the semantic-version source of truth;
  the root `plugin.json` mirrors that version for Agent Plugins clients.
  The What's New helper's existing `--version` option selects an Xcode release
  and must not become a helper-version flag without a breaking interface
  change.
- Use a major plugin bump for breaking helper contracts, a minor bump for
  backward-compatible capabilities, and a patch bump for compatible fixes.
- After changing the What's New helper, run its unit tests, `--help`, `--list`,
  an explicit stable lookup, an explicit beta lookup, and the default
  active-Xcode report.
