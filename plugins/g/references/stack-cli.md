# Stack CLI Contract

The plugin-shared artifact at `<plugin-root>/scripts/g` exposes a thin
boundary around the official `github/gh-stack` GitHub CLI extension. It does
not reimplement stack state, branch ordering, PR linking, rebasing, or merge
logic; those remain owned by `gh-stack`.

## Readiness and installation

The scoped host, authentication, and extension gate is owned by
[`gh-dependency-preflight.md`](gh-dependency-preflight.md). Load it before
stack-dependent operations; this reference owns the typed wrapper surface and
the explicit installation boundary.

```bash
<plugin-root>/scripts/g --json doctor
<plugin-root>/scripts/g --json stack ensure
<plugin-root>/scripts/g --json stack ensure --install
```

`stack ensure` is read-only. Only `stack ensure --install` may run:

```bash
gh extension install github/gh-stack
```

The wrapper checks `gh extension list` first and accepts only an extension entry
whose repository is exactly `github/gh-stack`. An installed entry reports
`publisher_verification: "not-verified"`: GitHub CLI extensions are executable
code from the publisher and are not a GitHub endorsement. The wrapper does not
upgrade an existing installation, replace a conflicting extension, create
G configuration, or install an agent skill. Installation uses the latest
upstream version and is subject to the network and authorization rules in
[`network-execution.md`](network-execution.md).

## Stack commands

The typed command surface is:

```text
init add checkout link push submit sync rebase view merge unstack
up down top bottom trunk
```

Arguments and flags after the typed command are forwarded to `gh stack`. The
wrapper sets `GH_PAGER=cat`, `GIT_PAGER=cat`, `PAGER=cat`, and
`GIT_TERMINAL_PROMPT=0`, closes stdin, and rejects interactive paths:

- `modify`, `switch`, `alias`, and `feedback`;
- branch, stack, PR, or URL prompts with missing positional input;
- `submit` without `--auto`;
- `merge` without an explicit target and `--yes`;
- remote `unstack` without an explicit target. Use `unstack --local` to remove
  the active local tracking entry without a remote operation.

The raw escape hatch is available for non-interactive upstream commands:

```bash
<plugin-root>/scripts/g --json stack raw -- view
```

Put the wrapper's `--json` before the raw `--` separator. Arguments after the
separator are forwarded verbatim to the upstream command. Raw is a repair path,
not a second primary API. Raw writes remain live writes and still require
caller authorization.

## JSON and errors

Use `--json` before or after the command. Successful output uses the normal
G envelope:

```json
{
  "ok": true,
  "version": "2.3.0",
  "command": ["stack", "view"],
  "data": {}
}
```

`stack view` inspects the current locally tracked stack; it takes no positional
stack number. It asks upstream for JSON and returns the parsed object. An explicit
`--help` or `-h` instead returns help text in the usual `stdout`/`stderr` envelope,
without adding the upstream JSON flag or parsing help as stack data.
Other successful commands return `{ "stdout": "...", "stderr": "..." }`.
`stack ensure` reports the detected repository, version, and publisher
verification state. Wrapper failures use stable G error codes; upstream
command failures preserve the upstream exit code and expose only safe command,
exit-code, and reason details in the JSON error envelope.

JSON failures intentionally omit free-form provider diagnostics. For a failed
read, the same noninteractive raw read without the outer G `--json` can expose
the sanitized diagnostic, for example `g stack raw -- view --json`. Do not
repeat a mutation just to obtain its diagnostic; reconcile its effect first.

## Maintenance

Normal execution uses `<plugin-root>/scripts/g`. The implementation and
tests live under `projects/g/`; rebuild the shipped artifact with
`projects/g/scripts/build-artifact`, then re-run `--help`, `--version`,
`--json doctor`, and `--json stack ensure`. Do not run maintenance modules as
the normal runtime and do not install `github/gh-stack` during builds or tests.
