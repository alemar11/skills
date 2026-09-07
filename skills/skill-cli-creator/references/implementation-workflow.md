# Embedded CLI Implementation

Use for executable, build, auth, or validation changes after resolving the owner
and shipped artifact path.

## Runtime and layout

Inspect the existing implementation and installed toolchains. Keep its language
unless a change materially improves SDK support, portability, or maintenance.
A small Python or shell command can ship directly under `scripts/`. Use
`projects/<tool>/` for multi-file or compiled implementations, with build outputs
copied to the shipped artifact. Follow [layout](embedded-cli-layout.md) for
platform binaries and config ownership.

Choose standard-library or established project dependencies before adding new
ones. Install a missing toolchain only within the user's authorization; an
installed alternative may be sufficient.

## Command contract

Define only relevant jobs: discovery, identity resolution, reads, writes, file
transport, pagination, authentication, and error handling. Preserve relied-on
flags and environment variables when wrapping an existing script. Use named
operations for repeated jobs; add a raw escape hatch only for a concrete need.

The shipped artifact must expose `--help`, `--version`, and `--json doctor`.
Version output comes from one semantic-version source. JSON results and errors
must be machine-readable and omit credentials. `doctor` reports missing setup
without changing config; test reachability only when the CLI needs a network.
See [CLI patterns](agent-cli-patterns.md) for examples.

## Auth and source evidence

Prefer provider-native authentication or environment variables. Add project
config only when repeated use warrants it, through an explicit config-write
command. Avoid credential flags when they would expose secrets in process
arguments or shell history.

When deriving a CLI from an internal API, keep sanitized endpoint evidence:
method/path, auth and CSRF mechanism, request shape, response identities,
pagination, and errors. UI screenshots explain workflow, not API behavior.
Never retain copied credentials or private production payloads as fixtures.

## Build and verification

Keep tests beside maintained source, generated-file ignores beside the build
project, and runtime examples pointed at the shipped artifact. Verify the
rebuilt artifact rather than an intermediate executable.

For new CLIs, check discovery commands, exit codes, missing setup, and one safe
representative operation. For changes, run affected checks and artifact smoke
checks; add only the relevant lane:

- API-backed: request construction, pagination, error mapping, and a fixture or
  authorized read against the service.
- Local: quoted paths, deterministic fixtures, missing tools, and destructive
  path guards where those behaviors exist.
- Hybrid: combine affected API and local checks.

Do not require a live write when a fixture proves the behavior. If one is
necessary, use an authorized disposable target and verify its cleanup.
For multi-stage uploads, distinguish creation, transfer, processing, and
attachment results.

## Integration

Synchronize runtime command examples, config paths, and output contracts.
Put build/rebuild instructions and semver policy in the nearest maintenance
`AGENTS.md`, not the runtime skill. Use major for breaking contracts, minor
for compatible capabilities, and patch for fixes.
