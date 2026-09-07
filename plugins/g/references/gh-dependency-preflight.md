# G to gh Runtime Preflight

This reference owns the scoped, fail-closed readiness gate for G operations
that use the GitHub CLI. It must not install, update, or replace `gh` or an
extension without explicit authorization.

## Load condition

Load this reference:

- before the first provider-facing operation through direct `gh` or
  `<plugin-root>/scripts/g` in any focused G skill;
- before any stack command, in addition to the host and authentication checks;
- before any GitHub Projects operation, in addition to the host,
  authentication, capability, and scope checks below.

The gate must finish before the dependent command, GitHub mutation, push,
stack operation, or extension installation.

## Host CLI checks

From the same host that will run the G operation, verify that the GitHub CLI is
available and runnable:

```sh
command -v gh
gh --version
```

Require an executable path and a successful, usable version result. Record the
resolved path and version as diagnostic evidence only. Do not infer CLI
availability from a plugin cache or an installed extension.

If the executable is missing, cannot run, or returns unusable version output,
stop with a CLI-missing or CLI-runtime blocker. No alternative GitHub provider
transport is defined by this plugin; do not install or update the CLI
automatically.

## Authentication checks

For authenticated provider work, inspect the active account from the same
network-enabled execution context as the operation:

```sh
gh auth status --active --hostname github.com --json hosts \
  --jq '.hosts["github.com"] | map(select(.active == true) | {state, scopes})'
```

Require exactly one active account with `state=success`. A failed command,
unusable response, or other state leaves authentication unverified; never
change credentials from an inconclusive network result. Do not print tokens.

The shared `g --json doctor` may supply equivalent authentication evidence when
already needed to diagnose a retained helper. Direct `gh` workflows do not
require the G artifact or Python. Authentication proof never grants mutation
authority.

## GitHub Projects checks

Before a Projects operation, verify that the installed CLI exposes the required
Projects command instead of inferring support from its version number:

```sh
gh project --help
gh project <required-command> --help
```

For the active `github.com` account, inspect authentication without displaying
the token:

```sh
gh auth status --active --hostname github.com --json hosts \
  --jq '.hosts["github.com"][] | select(.active == true) | {state, scopes}'
```

Require exactly one active successful account. A pure Projects read requires
`read:project` or `project`; a Projects mutation requires `project`. If the
required scope or command is unavailable, stop before the requested Projects
read or mutation and report the missing capability. Suggest
`gh auth refresh -s project` as manual remediation for a missing write scope,
but never run it without explicit authorization because it changes the local
authentication grant.

## gh-stack checks

Before any stack command, run:

```sh
<plugin-root>/scripts/g --json stack ensure
```

Require a successful result whose data reports:

- `status` is `ready`;
- `repository` is exactly `github/gh-stack`;
- `version` is present;
- `publisher_verification` is reported as `not-verified`.

The wrapper owns the read-only `gh extension list` check. A missing extension,
conflicting repository, missing version, malformed output, or failed listing is
a blocker. Run `stack ensure --install` only after the user explicitly
authorizes installing `github/gh-stack`; never fall back silently to an
ordinary PR workflow.

## Failure reporting

Report the exact failed layer and observed evidence. Preserve G's typed error
codes when the shared artifact returns them, including `gh_missing`,
`process_spawn_failed`, `extension_missing`, `extension_conflict`, and
`extension_unverified`. Do not classify provider failures from ad hoc stderr
text or claim that credentials are invalid from an inconclusive network result.
For Projects, distinguish a missing command or scope from a provider rejection
after an operation was attempted.
