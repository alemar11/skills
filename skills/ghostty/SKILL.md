---
name: ghostty
description: Inspect or arrange Ghostty terminals and edit configuration or keybindings when explicitly requested.
---

# Ghostty

For live macOS layout work, read [AppleScript operations](references/applescript.md).
For persistent defaults, read [configuration](references/configuration.md).
Without native scripting, use available keybindings and disclose unverified
layout details.

Inspect the target layout, preserve unrelated surfaces, and create only missing
windows, tabs, or splits. Retain returned object identities for subsequent
operations; do not identify a terminal by title alone. Verify the requested
layout and focus after changes.

Run only commands within the user's request, preserving quoting and newlines.
Closing or replacing existing surfaces requires clear target authorization;
do not ask again when it is already supplied.
