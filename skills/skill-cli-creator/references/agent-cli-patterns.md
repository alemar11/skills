# Codex CLI Patterns

Use this reference when designing the command surface for an embedded CLI Codex should run from a shipped artifact inside a skill or plugin bundle.

## Mental model

The CLI is Codex's command layer inside its owning host. It should turn a service, app, API, log source, or database into shell commands Codex can run repeatedly from the shipped runnable artifact stored in that owner's `scripts/` directory.

Good CLIs for Codex expose composable primitives. Avoid a single command that tries to "do the whole investigation" when smaller discover, read, resolve, download, inspect, draft, and upload commands would compose better.

Keep one shared owner model:

- shipped runtime artifact in `scripts/`
- optional maintenance project in `projects/<tool>/`
- persisted working-project config under the matching owner namespace

## Path vocabulary

- `owner root`: the directory from which canonical executable examples run
- `project root`: the root of the consuming workspace or repository where local operator config is stored; this is distinct from the `owner root`
- `artifact path`: the owner-root-relative shipped runnable artifact, usually `scripts/<tool>` or `scripts/<tool>.<ext>`
- `public runtime noun`: optional shorthand such as `<tool>` only when the owning docs explicitly define how that command becomes executable

Use `/` separators for repository-relative template paths such as
`scripts/<tool>` and `projects/<tool>/`. For real per-user filesystem paths,
write concrete OS examples with the right home-directory notation:

- macOS / Linux: `$HOME/...`
- Windows CMD-style: `%USERPROFILE%\...` or `%HOMEDRIVE%%HOMEPATH%\...`
- Windows PowerShell: `$env:USERPROFILE\...`

Do not use `%HOMEPATH%` alone because it omits the drive.

## Owner boundary

Resolve the owner before designing the command surface.

For skill-owned CLIs:

- runtime artifact: `<skill-root>/scripts/<tool>`
- maintenance project: `<skill-root>/projects/<tool>/`
- working-project config: `<project-root>/.skills/<skill>/config.toml`

For plugin-owned CLIs used by exactly one bundled skill:

- runtime artifact: `<plugin-root>/skills/<skill>/scripts/<tool>`
- maintenance project: `<plugin-root>/skills/<skill>/projects/<tool>/`
- working-project config: `<project-root>/.plugins/<plugin>/skills/<skill>/config.toml`

For plugin-owned CLIs shared by multiple bundled skills:

- runtime artifact: `<plugin-root>/scripts/<tool>`
- maintenance project: `<plugin-root>/projects/<tool>/`
- working-project config: `<project-root>/.plugins/<plugin>/config.toml`

Do not split ownership. `artifact path`, `projects/<tool>/`, and the persistent config namespace must stay under the same resolved owner model.

Treat plugin-root `scripts/` as a repo convention, not as an official Codex plugin manifest component.

## Naming the host vs the CLI

Treat these as separate names:

- host name: the skill or plugin guidance/package container
- CLI/tool name: the runtime command noun used in `scripts/<tool>` and `projects/<tool>/`

Default to different names when the runtime command is narrower than the host. Only reuse the host name when it is intentionally the clearest standard runtime noun.

Good divergent examples:

- `postgres` skill -> `scripts/pgops` with `projects/pgops/`
- `github` skill -> `scripts/ghtriage` with `projects/ghtriage/` when the embedded CLI focuses on repo triage, reviews, and CI
- `ops-toolkit` plugin -> `scripts/logs` with `projects/logs/` when multiple bundled skills share the same log-reading surface

Allowed matching-name exception:

- reuse the host name when the runtime noun is already the clearest standard surface and inventing a different command would be more awkward or more misleading than helpful

## Help is interface

Write `--help` for a future Codex thread that only has the shipped artifact in `scripts/...` and a vague task. Each command should have a short description and flags with literal names from the product or API.

Good top-level help should answer:

- What containers can I discover?
- What exact objects can I read?
- What stable IDs can I resolve?
- What files can I download or upload?
- Which write actions exist?
- What is the raw escape hatch?

Treat `--version` as part of that top-level interface, not an afterthought.

## Prefer this command shape

Use product nouns, then verbs:

```bash
<artifact-path> --version
<artifact-path> --json doctor
<artifact-path> --json accounts list
<artifact-path> --json projects list
<artifact-path> --json channels resolve --name codex
<artifact-path> --json messages search "exact phrase"
<artifact-path> --json messages context <message-id> --before 3 --after 3
<artifact-path> --json logs download <build-url> --failed --out ./logs
<artifact-path> --json media upload --file ./image.png
<artifact-path> --json drafts create --body-file draft.json
```

For APIs whose native noun is already strong, direct verbs can be fine:

```bash
<artifact-path> --json social-sets
<artifact-path> --json drafts list --social-set <id>
<artifact-path> --json request get /v2/me
```

The important rule is consistency. Do not mix many styles unless the product vocabulary demands it.

## Runtime surface

When the CLI is embedded inside a host:

- run the tool from `<artifact-path>` during normal execution
- treat `<artifact-path>` as the shipped runnable artifact for normal execution
- use `<artifact-path> --version` as the stable version check
- choose the CLI/tool name intentionally; do not assume it must match the host name
- use the same CLI/tool name consistently for `<artifact-path>` and `projects/<tool>/`
- do not inspect `projects/<tool>/` during normal execution
- open `projects/<tool>/` only when fixing, improving, rebuilding, or extending the implementation behind the `<artifact-path>` surface
- keep the command shape stable even if the implementation language or internal layout changes
- do not treat `target/`, `dist/`, virtualenv paths, or other build directories as supported runtime entrypoints
- keep manifests, lockfiles, dependency installs, caches, intermediate build outputs, and project-local build/test config inside `projects/<tool>/` when a real maintenance project exists

Keep one semver source of truth. Use the runtime-native manifest version when available, otherwise keep one explicit version constant or file and have `--version` read from it.

If the runtime produces a compiled executable, copy, install, or generate the shipped artifact into `scripts/`. Script-native runtimes may keep the shipped script itself in `scripts/` when that script is the real artifact.

If the scaffold also creates project-local generated state, keep that ignore policy close to `projects/<tool>/`:

- create or update `projects/<tool>/.gitignore` only when the CLI introduces build, cache, module, or environment directories inside that project
- keep the local `.gitignore` limited to those project-local generated paths
- do not create a no-op local `.gitignore` when there is nothing project-local to ignore

## Working-project config

Use one owner-aligned `config.toml` namespace, not one TOML file per tool.

Normative shape:

```toml
schema_version = "1.0.0"

[defaults]
profile = "staging"

[auth]
source = "env"

[tools.logs]
workspace = "mobile"

[tools.deploys]
confirm = "interactive"

[meta]
written_by = "logs"
written_by_version = "0.9.0"
```

Rules:

- `schema_version` is the config format version
- owner-wide settings live only in explicitly documented shared sections such as `[defaults]`, `[auth]`, or `[profiles]`
- `[tools.<tool>]` stores tool-specific persisted settings
- when multiple CLIs share one `config.toml`, each CLI may write only its own `[tools.<tool>]` subtree plus any shared section it uniquely owns as the documented single writer
- `[meta]` is optional provenance only
- do not use top-level `version` as normative config state
- do not require per-tool version fields
- write config only through explicit init/login/configure flows
- never create config implicitly during reads or health checks

## Runtime cache paths

Use a per-user runtime cache only for reusable downloaded or generated runtime
artifacts that should survive across consuming repos. Keep operator config in
the owner-aligned `config.toml`, and keep build outputs or dependency caches
inside `projects/<tool>/`.

When a cache is needed, scope it by owner:

- skill-owned: `~/.cache/dotagents/skills/<skill-name>/...`
- plugin-owned shared: `~/.cache/dotagents/plugins/<plugin-name>/...`
- plugin-owned but local to one skill: `~/.cache/dotagents/plugins/<plugin-name>/skills/<skill-name>/...`

Equivalent concrete forms:

- macOS / Linux: `$HOME/.cache/dotagents/...`
- Windows CMD-style: `%USERPROFILE%\.cache\dotagents\...` or `%HOMEDRIVE%%HOMEPATH%\.cache\dotagents\...`
- Windows PowerShell: `$env:USERPROFILE\.cache\dotagents\...`

Treat cache contents as disposable and rebuildable; never use the runtime cache
as the sole source of truth for user state.

## Useful shapes from mature CLIs

Prefer these patterns over clever agent-only abstractions:

```bash
# Field-selected structured output: make common reads scriptable.
<artifact-path> issues list --json number,title,url,state
<artifact-path> issues list --json number,title --jq '.[] | select(.state == "open")'

# Human text by default, full API object when requested.
<artifact-path> pods get <name>
<artifact-path> pods get <name> -o json

# Product workflow commands, not just REST nouns.
<artifact-path> logs tail
<artifact-path> webhooks listen --forward-to localhost:4242/webhooks
<artifact-path> webhooks trigger checkout.completed
```

Only implement filtering or templating if the user will actually need it. Stable JSON plus narrow read commands are the baseline.

## Discovery, resolve, read, context

Design first-pass commands in this order:

1. **Discover** broad containers: workspaces, accounts, social sets, repos, projects, channels, queues.
2. **Resolve** human input into IDs: user names, channel names, permalinks, PR URLs, build URLs, customer slugs.
3. **Read** an exact object: issue, event, thread, draft, customer, job, run, media item.
4. **Context** around an anchor when useful: nearby messages, parent thread, surrounding logs, audit history.

Do not force Codex to repeatedly search when it already has a stable ID.

## Text, JSON, files, exit codes

Support human text by default if it helps. Support `--json` everywhere Codex will parse or pipe results.

Version reporting stays separate from `--json`: running `<artifact-path> --version` should print the current CLI semver cleanly, and `doctor --json` should include that same version in its structured diagnostics.

For `--json`:

- emit JSON to stdout only
- send progress and diagnostics to stderr
- keep success and error shapes documented
- redact tokens, cookies, customer secrets, private headers, and unrelated payloads

For downloads and exports:

- write files under a user-provided `--out` path when possible
- in JSON output, return the file path, byte count if cheap, source URL or ID, and follow-up command

For exit codes:

- exit zero when the command succeeded, including an empty result
- exit nonzero for auth failure, invalid input, network failure, parse failure, API error, or incomplete upload/download
- make `doctor --json` usable even when auth is missing; it should report missing auth rather than crashing

## Validation profiles

Always validate the shared core from `<artifact-path>`:

- `--help`
- `--version`
- `--json doctor`
- executable invocation from the resolved `owner root`
- exit codes and at least one safe fixture, dry-run, or read-only end-to-end check

Then add the lane that matches the CLI:

- API-backed: auth handling, request builders, pagination or cursor handling when applicable, and at least one live or fixture-backed read-only API call
- local/offline or shell: syntax or interpreter startup checks, quoted-path handling, deterministic fixture runs, missing-tool diagnostics, destructive-path guards, and no-network execution
- hybrid: combine the relevant API-backed and local/offline checks without inventing irrelevant placeholders

## Pagination and breadth

Start shallow by default. Add explicit knobs for breadth:

```bash
<artifact-path> --json messages search "topic" --limit 10
<artifact-path> --json messages search "topic" --limit 50 --all-pages --max-pages 3
<artifact-path> --json drafts list --limit 20 --offset 40
```

Return the provider's real pagination field names, such as `next_cursor`, `next_url`, `offset`, or `page_count`, and document that shape clearly.

## Raw escape hatch

The raw command is a repair hatch, not the main interface.

Good raw commands still use configured auth, base URL, JSON parsing, redaction, status/error handling, and `--json`.

Make reads easy:

```bash
<artifact-path> --json request get /v2/me
```

Treat raw writes as live writes. Do not hide POST/PUT/PATCH/DELETE behind a "debug" command.

## Host pattern

The owning skill docs or plugin docs should teach the path through the embedded tool:

```md
Start with:

<artifact-path> --version
<artifact-path> --json doctor
<artifact-path> --json accounts list

For [common job]:

<artifact-path> --json ...
<artifact-path> --json ...

Rules:

- Prefer the shipped artifact at `<artifact-path>`.
- Check `<artifact-path> --version` when confirming the shipped CLI matches the latest built implementation.
- Use --json when analyzing output.
- Create drafts by default.
- Do not publish/delete/retry/submit unless the user asked.
- Do not inspect `projects/<tool>/` during normal execution.
- Use `request get ...` only when high-level commands are missing.
- Use bare `<tool> ...` only if the docs also define the wrapper, alias, or PATH setup that makes that shorthand executable.
```

Include JSON shape notes only when Codex needs them to choose the next command.

Add a `CLI Maintenance` section in the owning runtime docs for every embedded CLI. That section should say:

- normal runtime work stays on `<artifact-path>`
- `projects/<tool>/` is for bug fixes, performance work, rebuilds, and feature additions
- shipped CLI changes must update the implementation, rebuild the shipped artifact at `<artifact-path>`, and re-run `--help`, `--version`, and `--json doctor`
- compiled outputs in `target/`, `dist/`, virtualenvs, or similar paths are build intermediates rather than supported runtime entrypoints
- project-local generated state should be ignored through `projects/<tool>/.gitignore`
- the CLI follows semver from one declared version source of truth
- when a bundled skill points to a plugin-shared CLI, introduce the execution context explicitly before the command, such as `From the plugin root, run ...`
