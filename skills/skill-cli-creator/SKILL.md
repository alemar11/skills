---
name: skill-cli-creator
description: Create or refactor CLIs shipped inside a skill or plugin bundle.
---

# Skill CLI Creator

Resolve the host, command name, shipped artifact path, and requested behavior
from the existing package. Evolve an existing command rather than creating a
duplicate. If the host is missing, use skill-creator or plugin-creator to create
it within the requested scope.

Read only the relevant contracts:

- Host ownership: [states](references/states.md).
- Paths, config, caches, or platform packaging: [layout](references/embedded-cli-layout.md).
- Runtime, build, auth, or validation changes: [implementation](references/implementation-workflow.md).
- Commands, JSON, pagination, files, or writes: [CLI patterns](references/agent-cli-patterns.md).

Keep simple scripts under `scripts/`. Introduce `projects/<tool>/` only for a
multi-file or build-backed implementation; it is maintenance source, never the
normal runtime entrypoint. Keep artifact, config, examples, and docs under one
owner. Reads and diagnostics must not write config.

Verify executable changes through the shipped artifact: affected tests,
`--help`, `--version`, `--json doctor`, and a safe fixture or end-to-end check.
Select the relevant validation lane from the implementation reference. For
prose-only changes, check the changed paths and examples instead.

Synchronize affected runtime docs and version metadata. A maintenance project
needs its own build/rebuild and validation contract in `AGENTS.md`.
