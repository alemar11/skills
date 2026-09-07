---
name: codex-cli
description: Launch one complete prompt in an isolated Codex CLI run when explicitly requested.
---

# Codex CLI

Use `<skill-root>/scripts/codex-cli` for one ephemeral delegated execution.
Requires Python 3.10+, a local authenticated Codex CLI, engine access, and a
usable working directory. A read-only sandbox does not make the run offline.

Pass the caller's complete prompt unchanged through `--prompt`, `--prompt-file`,
or stdin. Do not add a hidden review or implementation template. The caller
owns task semantics and success criteria.

Before launch, read [model policy](references/model-policy.md) and
[states](references/states.md) to resolve model and reasoning. Preserve explicit
selections; omission uses the documented defaults. Choose a different profile
only when the caller authorizes that choice. Resolve it before execution,
not by asking the delegated process to choose its own settings.

Default to a read-only sandbox and no interactive approvals. Select file-write
access only for an authorized editing task; unrestricted access needs explicit
authorization and a concrete reason. Delegation does not expand Git,
publication, deployment, or external-account authority.

For options, output handling, or custom review use, read
[invocation](references/invocation.md). Use `--dry-run` to inspect resolution
without launching, and `--json doctor` for availability problems. Do not claim
remote model availability from a dry run.

Return the delegated result and relevant execution failures. The launcher does
not retry failed tasks. Reconcile possible effects before any caller-directed
retry. Persistent App tasks require a different workflow.
