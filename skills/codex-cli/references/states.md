# Codex CLI States

The launcher persists no task ledger. Model aliases, reasoning values, task
profiles, and adjustment meanings are owned by [model policy](model-policy.md).
They are per-run selections or derived results, not saved configuration.

| Execution selection | Meaning |
| --- | --- |
| `read-only` | Delegated process cannot edit project files. |
| `workspace-write` | Delegated process may edit its permitted workspace. |
| `danger-full-access` | Delegated execution lacks sandbox restrictions. |
| `auto` | Resolve reasoning from the model and task profile. |

Sandbox values are external Codex syntax. An explicit launcher `--output` write
is independent of the delegated sandbox. Successful nonempty results may be
written there; failed or empty runs leave it unchanged. The launcher pins the
canonical destination directory, rejects a final symlink, and fails if the
parent is replaced. A dry run resolves invocation without launching; doctor
reports local availability, not successful remote execution.
