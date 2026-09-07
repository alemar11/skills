# G Plugin Maintenance

G owns Git/GitHub provider primitives and explicit read-only task monitoring.
Composing workflows own product planning, delivery policy, and orchestration.

## Ownership

- `.codex-plugin/plugin.json` owns identity, exposure, and version.
- `scripts/g` is the shared artifact; `projects/g/AGENTS.md` owns its source,
  build, tests, and version alignment. Keep executable helpers for fragile
  mutation and receipt protocols; direct reads and simple operations belong in
  skills using `git`/`gh`. Do not add a wrapper solely to reshape provider output.
- `references/options.md` owns invocation fields;
  `references/network-execution.md` owns shell network/auth handling.
- Each skill owns its narrow runtime contract and state registry. Keep package
  maintenance out of runtime entrypoints.
- `github-issues` owns issue mutation/readback, attachment placement, metadata
  classification, and read-only taxonomy proposals. Keep selection separate
  from exact operations within that skill; shared `attachment upload` remains
  the only binary upload transport.
- `github-projects` uses direct authenticated `gh`, not new shared CLI commands.
- `audit` observes active G tasks and adds no Git/GitHub transport.

Keep provider access independent of app connectors. Skills use authenticated
`gh` directly or through the shared artifact; the manifest declares no GitHub
app dependency. Preserve file-backed provider text, exact identities, and
independent mutation readback. Provider projections do not become planning
policy.

## Stack compatibility

The stack wrapper owns compatibility with official `github/gh-stack`. Upstream
`v0.0.9` is the current validation baseline, not an installation pin; explicit
installation currently selects latest upstream.

For an upstream change, verify typed commands, noninteractive behavior, JSON,
version/repository detection, and affected stack workflows. Missing, unversioned,
or wrong-repository extensions must fail closed. Never install during tests.

## Validation

Validate changed skill metadata, reference routing, and affected contracts.
Do not test Markdown wording or moved prose. Executable changes use the
project-scoped tests and rebuilt-artifact checks. Keep manifest, package
version, version assertions, and shipped artifact aligned for each versioned
commit. Installed caches are verification surfaces, not source.
