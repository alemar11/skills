# Network Execution

Read this reference before running a shell command that may contact GitHub or a
package registry. It is the canonical G contract for shell network
permission; bundled skills should link here instead of restating it.

## Choose the execution path

| Operation | Execution rule |
| --- | --- |
| Local-only command | Keep it sandboxed. This includes local `git` status, diff, log, staging, commit, repository snapshots, help, and version checks. |
| Network-bearing shell command | Use the runtime's narrowest network-enabled execution context from the outset for the exact command family. This includes `gh`; remote `git` operations such as fetch, pull, push, and `ls-remote`; registry checks or publication; and any `scripts/g` subcommand that invokes `gh`. |

Keep the network scope to the smallest useful command family; never request
blanket unrestricted access to `github.com`. The shipped G CLI does not and
cannot grant itself network access.

Network permission changes where the command executes, not what the user has
authorized. Read-only permission does not authorize a write. Pushes, comments,
issue changes, releases, reruns, review mutations, and other remote writes still
require the authority defined by the owning skill.

## Interpret failures safely

- Do not use a sandboxed remote command as an authentication preflight when the
  command is known to need network access.
- Treat DNS, connection, provider, and authentication-looking failures from a
  restricted execution environment as inconclusive. Do not conclude that a
  token is invalid from that result.
- Prefer structured provider output and stable fields. Do not classify failures
  from ad hoc stderr substring lists.
- Establish authentication through the shared
  [GitHub CLI preflight](gh-dependency-preflight.md) from the network-enabled
  execution context. Inconclusive evidence is not proof of invalid credentials.
- After an ambiguous remote write failure, read back the exact target and
  reconcile current provider state before deciding whether a retry is safe.
