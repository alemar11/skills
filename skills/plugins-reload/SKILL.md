---
name: plugins-reload
description: Reload this repository’s G, SE, and Xcode plugin installations when explicitly requested.
---

# Plugins Reload

A reload request authorizes refreshing installed copies from this repository,
not source edits or publication. Establish the configured local marketplace
and source paths before replacing an installation.

Refresh G, SE, and Xcode through the current Codex plugin installation
capability. Verify each installed version against its source manifest and
report failures separately. Use a fresh task afterward to load updated skills.
Do not manually edit installed cache files or rebuild source as an incidental
part of reloading.
