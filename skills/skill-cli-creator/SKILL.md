---
name: skill-cli-creator
description: Build a composable embedded CLI that lives inside a skill or plugin. Use when Codex needs to create or refactor an embedded command surface under `scripts/`, keep normal runtime usage on that `scripts/...` surface, and optionally maintain one or more larger CLI implementations in a maintenance-only project under `projects/`.
---

# Skill CLI Creator

Create a real CLI that future Codex threads run from a shipped artifact inside a skill or plugin bundle.

Build for embedded host use only. Do not use this skill for standalone global CLIs, separate personal CLI repos, or PATH-first packaging.

## Start

Name the host, the CLI source material, and the first real jobs it should do:

- Host mode: `skill` or `plugin`
- Host owner:
  - for `host=skill`: the skill directory that owns the CLI surface
  - for `host=plugin`: the plugin directory, plus whether one skill or multiple bundled skills own the runtime surface
- CLI/tool name: the runtime command name that will own `scripts/<tool>` and, when needed, the maintenance-only build project at `projects/<tool>/`
- Source: API docs, OpenAPI JSON, SDK docs, curl examples, browser app, existing internal script, article, or working shell history
- Jobs: literal reads and writes such as `list drafts`, `download failed job logs`, `search messages`, `upload media`, `read queue schedule`
- Artifact path: the shipped runnable artifact path such as `scripts/ci-logs`, `scripts/slack-cli`, or `skills/example/scripts/buildkite-logs`

Choose the host owner and the CLI/tool name independently by default. Reuse the skill or plugin name only when it is intentionally the clearest runtime command name.

## Path Vocabulary

Resolve these terms before writing commands or examples:

- `owner root`: the directory from which canonical executable examples must run
  - for `host=skill`: `<skill-root>`
  - for `host=plugin` when exactly one bundled skill owns the CLI: `<plugin-root>/skills/<skill>`
  - for `host=plugin` when the CLI is shared: `<plugin-root>`
- `artifact path`: the owner-root-relative path to the shipped runnable artifact, usually `scripts/<tool>` or `scripts/<tool>.<ext>`
- `public runtime noun`: optional shorthand such as `<tool>` only when the host docs explicitly define a wrapper, alias, or PATH setup that makes that form executable

Before scaffolding, resolve the ownership boundary first:

- `host=skill`
- `host=plugin` and used by exactly one bundled skill
- `host=plugin` and intentionally shared by multiple bundled skills

From the `owner root`, check whether the proposed shipped artifact path or maintenance project already exists:

```bash
test -e <artifact-path> && echo "artifact exists"
test -e projects/<tool-name> && echo "project exists"
```

If either exists, choose a clearer entry name or evolve the existing command instead of creating a competing surface.
Also confirm that the proposed CLI/tool name does not already collide with:

- an existing `[tools.<tool>]` config subtree in the same owner namespace
- an already-documented runtime command noun in the same owner docs or help output

## Ownership First

Keep one embedded-CLI doctrine for all hosts:

- `scripts/` contains the shipped runnable artifacts used during normal execution
- `projects/<tool>/` is the optional maintenance-only build project behind one shipped CLI
- persisted working-project config follows the same owner boundary and keeps plugin identity explicit when the host is a plugin
- normal runtime usage never runs from `dist/`, `target/`, virtualenv paths, or similar build outputs

The owner of the shipped artifact also owns:

- the maintenance project
- the persistent working-project config namespace
- the runtime docs and examples

Do not split ownership. In particular:

- do not allow plugin-root `projects/<tool>/` with skill-local `scripts/<tool>`
- do not drop plugin identity or skill scope from the persistent config namespace when the host is a plugin
- do not silently derive ownership from the CLI/tool name later

## Host-Specific Placement Rules

For `host=skill`:

- shipped artifact: `<skill-root>/scripts/<tool>`
- maintenance project: `<skill-root>/projects/<tool>/`
- working-project config: `<project-root>/.skills/<skill>/config.toml`

For `host=plugin` when the CLI is used by exactly one bundled skill:

- shipped artifact: `<plugin-root>/skills/<skill>/scripts/<tool>`
- maintenance project: `<plugin-root>/skills/<skill>/projects/<tool>/`
- working-project config: `<project-root>/.plugins/<plugin>/skills/<skill>/config.toml`

For `host=plugin` when the CLI is intentionally shared by multiple bundled skills:

- shipped artifact: `<plugin-root>/scripts/<tool>`
- maintenance project: `<plugin-root>/projects/<tool>/`
- working-project config: `<project-root>/.plugins/<plugin>/config.toml`

Default to the narrowest owner. Promote from skill-local ownership to plugin-root ownership only when the CLI is intentionally shared by multiple bundled skills.

When a skill-local plugin CLI later becomes shared, move the full ownership set together:

- shipped artifact
- maintenance project
- config namespace

After promotion, document one deterministic read path and do not silently read both:

- `.plugins/<plugin>/skills/<skill>/config.toml`
- `.plugins/<plugin>/config.toml`

Promotion is a storage migration, not a permanent dual-read fallback:

- normal read commands must use only the new config path
- a one-time import from the old config path is allowed only during an explicit mutating flow such as `init`, `login`, `configure`, or `migrate-config`
- only perform that import when the new config path is absent
- preserve only the CLI-owned `[tools.<tool>]` subtree plus any shared section that the CLI explicitly owns
- update ignore rules for the new config path in the same rollout

Treat plugin-root `scripts/` as a repository convention supported by this skill, not as an officially documented Codex plugin manifest component.

## Naming Convention

Treat the host container and the CLI/tool name as different design decisions:

- host name: the skill or plugin package container
- CLI/tool name: the runtime command noun used in `scripts/<tool>` and, when needed, `projects/<tool>/`

Use this naming rule:

- by default, choose the CLI/tool name independently when the runtime command is a narrower operational surface than the host
- reuse the host name only when matching is intentionally justified because it is already the clearest ecosystem-standard runtime noun
- use the chosen CLI/tool name consistently in `scripts/<tool>`, `projects/<tool>/`, runtime examples, and maintenance docs

Naming rubric:

- prefer short, task- or domain-oriented names
- avoid names that imply broader scope than the CLI actually covers
- avoid generic suffix-only names such as `-cli` or `-tool` unless they materially improve clarity
- if the CLI/tool name matches the host name, state the justification explicitly before scaffolding

## Embedded Layout

Keep the layout model short and explicit:

- `scripts/` contains the shipped runnable artifacts used during normal execution
- `projects/<tool>/` is the maintenance-only build project behind one shipped CLI
- `<project-root>/.skills/<skill>/`, `<project-root>/.plugins/<plugin>/`, and `<project-root>/.plugins/<plugin>/skills/<skill>/` are config-only
- separate the shipped artifact path from the public runtime noun:
  `<artifact-path>` is the canonical executable form, while bare `<tool>` is optional shorthand only after the host docs explain how that command becomes executable

Keep these invariants explicit in the host docs and CLI docs:

- run the tool from `<artifact-path>` during normal execution
- do not inspect `projects/<tool>/` during normal execution
- do not require normal users to run code directly from `projects/<tool>/`
- do not treat `projects/<tool>/` as part of the normal runtime surface
- treat `<artifact-path>` as the shipped runnable artifact regardless of language
- require `<artifact-path> --version` as part of the stable runtime surface
- let the chosen CLI/tool name govern both `<artifact-path>` and `projects/<tool>/`
- open `projects/<tool>/` only when fixing, improving, rebuilding, or extending the implementation behind `<artifact-path>`
- keep script-native runnable artifacts entirely in `scripts/`; introduce `projects/<tool>/` only when the implementation grows enough to justify a real maintenance project
- keep the CLI project self-contained inside `projects/<tool>/`; put manifests, lockfiles, dependency installs, caches, intermediate build outputs, project-local test/build config, and source there by default
- do not introduce host-root wrappers unless the user explicitly asks for that non-standard layout
- if `projects/<tool>/` exists, keep CLI-specific tests inside `projects/<tool>/tests/` or an equivalently project-local test directory
- do not execute compiled CLIs from `target/`, `dist/`, virtualenv paths, or other build directories during normal usage
- if the runtime produces a compiled executable, copy, install, or generate the shipped artifact into `scripts/` before considering the CLI ready
- if `projects/<tool>/` exists, require `projects/<tool>/AGENTS.md` with build, test, rebuild, runtime prerequisites, safe-maintenance instructions, the version source of truth, the semver bump policy, and rebuild instructions for restoring the shipped artifact at `<artifact-path>`
- if the scaffold introduces project-local generated state that must not be committed, create or update `projects/<tool>/.gitignore` and keep it scoped to that tool's generated paths
- do not create an empty or no-op `projects/<tool>/.gitignore` when the CLI introduces no project-local generated state
- do not standardize alternative generic maintenance folders such as `src/`, `code/`, `impl/`, or `source/` for the full project layout
- in user-facing skill docs, examples, and runbooks, make executable examples use `<artifact-path> ...` unless the host docs explicitly define a wrapper, alias, or PATH contract for bare `<tool> ...`
- bare `<tool> ...` can appear only as optional shorthand after that executable contract is documented
- do not tell bundled skills to run `scripts/<tool>` unless that path is actually the artifact path from that skill's `owner root`

For detailed command-shape, runtime-surface, JSON, and host-owned examples, read [references/agent-cli-patterns.md](references/agent-cli-patterns.md).

## Config Rules

Persist config only when the user explicitly chooses a write path such as:

- `<artifact-path> init ...`
- `<artifact-path> login ...`
- `<artifact-path> configure ...`

Never create config implicitly on install or on first read.

Use one owner-aligned `config.toml` namespace, not one file per tool:

- skill-owned: `<project-root>/.skills/<skill>/config.toml`
- plugin-owned shared: `<project-root>/.plugins/<plugin>/config.toml`
- plugin-owned but local to one skill: `<project-root>/.plugins/<plugin>/skills/<skill>/config.toml`

Keep config-only directories explicit:

- `<project-root>/.skills/<skill>/`
- `<project-root>/.plugins/<plugin>/`
- `<project-root>/.plugins/<plugin>/skills/<skill>/`

Do not place helper scripts or implementation code there.

Treat owner-level `config.toml` as local persisted operator config:

- consuming repos should gitignore `<project-root>/.skills/<skill>/config.toml`
- consuming repos should gitignore `<project-root>/.plugins/<plugin>/config.toml`
- consuming repos should gitignore `<project-root>/.plugins/<plugin>/skills/<skill>/config.toml`
- when a skill or plugin migrates from a legacy config filename to
  `config.toml`, update the consuming repo ignore rules in the same rollout
- do not treat owner-level `config.toml` as normal repo content unless the user
  explicitly wants a tracked example or fixture elsewhere

The normative config format uses:

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

- `schema_version` is the config format version and the only required version field
- owner-wide settings live only in explicitly documented shared sections such as `[defaults]`, `[auth]`, or `[profiles]`
- `[tools.<tool>]` stores tool-specific persisted settings
- when multiple CLIs share one `config.toml`, each CLI may write only its own `[tools.<tool>]` subtree plus any shared section it explicitly owns
- `[meta]` is optional provenance only and must not drive runtime behavior
- do not require top-level `version`
- do not require `tools.<tool>.version`
- create parent directories only when the user actually persists config

## Config Migrations

Promotion from plugin single-skill ownership to plugin-shared ownership is a storage migration:

- normal read commands must use only the new config path under `.plugins/<plugin>/config.toml`
- a one-time import from `.plugins/<plugin>/skills/<skill>/config.toml` is allowed only during an explicit mutating flow such as `init`, `login`, `configure`, or `migrate-config`
- only import when the new config file is absent
- preserve the CLI-owned `[tools.<tool>]` subtree plus any shared section that the CLI explicitly owns
- keep ignore rules aligned with the new canonical path in the same rollout

## CLI Versioning

Versioning is required for every embedded CLI produced through this skill, even when the implementation is small.

- support `<artifact-path> --version` on the public runtime surface
- keep one semver source of truth for the CLI version
- use the artifact stored at `<artifact-path>` as the only supported normal-execution surface
- use the runtime-native manifest version when one exists, such as `Cargo.toml`, `package.json`, or `pyproject.toml`
- when no native manifest exists, keep the version in one explicit code constant or a dedicated version file rather than scattering literals
- treat doc-only updates as no-version-bump changes unless they accompany shipped CLI behavior changes

## Choose the Runtime

Before choosing, inspect the user's machine and source material:

```bash
command -v cargo rustc node pnpm npm python3 uv || true
```

Then choose the least surprising toolchain:

- default to **Rust** when the embedded CLI needs a larger maintained implementation and benefits from a real project under `projects/<tool>/`
- use **TypeScript/Node** when the official SDK, auth helper, browser automation library, or existing repo tooling is the reason the embedded CLI can be better
- use **Python** when the source is data science, local file transforms, notebooks, SQLite/CSV/JSON analysis, or Python-heavy admin tooling
- use **shell** for thin orchestration surfaces whose shipped runnable script can live entirely in `scripts/`

Do not pick a language that adds setup friction unless it materially improves the CLI. If the best language is not installed, either install the missing toolchain with the user's approval or choose the next-best installed option.

State the choice in one sentence before scaffolding, including the reason and the installed toolchain you found.

## Command Contract

Sketch the command surface in chat before coding. Include the shipped artifact path, discovery commands, resolve or ID-lookup commands, read commands, write commands, raw escape hatch, auth/config choice, and any rebuild behavior needed to restore the shipped artifact in `scripts/`.

Before finalizing the command contract, confirm that the CLI/tool name is the best runtime noun for the planned jobs rather than defaulting to the host name out of symmetry.
Keep the distinction explicit in examples: document `<artifact-path>` as the
canonical executable form, and use bare `<tool> ...` only when the host docs
also define the wrapper, alias, or PATH setup that makes that shorthand valid.

Use [references/agent-cli-patterns.md](references/agent-cli-patterns.md) for the expected composable CLI shape, command ordering, JSON conventions, pagination patterns, and host-owned examples.

Build toward a surface where:

- `<artifact-path> --help` exposes the major capabilities
- `<artifact-path> --version` reports the current CLI semver from the single source of truth
- `<artifact-path> --json doctor` verifies config, auth, version, and missing setup; API-backed CLIs should also report endpoint reachability, while local/offline CLIs should report fixture or tool readiness instead
- `<artifact-path> init ...` stores local config when env-only auth is painful
- discovery commands find accounts, projects, workspaces, teams, queues, channels, repos, dashboards, or other top-level containers
- resolve commands turn names, URLs, slugs, permalinks, customer input, or build links into stable IDs so future commands do not repeat broad searches
- read commands fetch exact objects and list/search collections
- write commands do one named action each and accept the narrowest stable resource ID
- `--json` returns stable machine-readable output
- repeated jobs get high-level verbs rather than only a generic `request` command
- the raw escape hatch exists, but stays secondary to the high-level commands

Document the JSON policy in the owning skill docs, plugin docs, or reference files: whether commands return raw API-shaped responses or a CLI-specific envelope, plus the success shape, error shape, and one example for each command family. Under `--json`, errors must be machine-readable and must not contain credentials.

## Auth and Config

Support the boring paths first, in this precedence order:

1. environment variable using the service's standard name, such as `GITHUB_TOKEN`
2. project-local config under the owner-specific `config.toml` when env-only auth is painful
3. `--api-key` or a tool-specific token flag only for explicit one-off tests

Never print full tokens. `doctor --json` should say whether a token is available, the auth source category (`flag`, `env`, `config`, provider default, or missing), and what setup step is missing.

If the CLI can run without network or auth, make that explicit in `doctor --json`: report fixture/offline mode, whether fixture data was found, and whether auth is not required for that mode.

For internal web apps sourced from DevTools curls, create sanitized endpoint notes before implementing: resource name, method/path, required headers, auth mechanism, CSRF behavior, request body, response ID fields, pagination, errors, and one redacted sample response. Never commit copied cookies, bearer tokens, customer secrets, or full production payloads.

Use screenshots to infer workflow, UI vocabulary, fields, and confirmation points. Do not treat screenshots as API evidence unless they are paired with a network request, export, docs page, or fixture.

## Build Workflow

1. Read the source just enough to inventory resources, auth, pagination, IDs, media/file flows, rate limits, and dangerous write actions. If the docs expose OpenAPI, download or inspect it before naming commands.
   For local/offline CLIs, inventory file formats, local tools, path handling, destructive operations, and no-network behavior instead of forcing an API-shaped model.
2. Sketch the command list in chat. Keep names short and shell-friendly.
3. Scaffold the CLI inside the resolved owner using the two-surface layout:
   - `scripts/` for runtime
   - optional `projects/<tool>/` for the maintenance-only build project
4. Add or wire the single semver source of truth before the CLI contract is considered complete.
5. Expose the shipped runnable artifact under `scripts/` and treat outputs in `target/`, `dist/`, virtualenvs, or similar locations as build intermediates rather than supported runtime entrypoints.
6. If `projects/<tool>/` exists, put the CLI's maintained unit and integration tests under that project rather than at the owner root.
7. If the runtime produces a compiled executable, copy, install, or generate that executable into `scripts/`.
8. Inspect which project-local generated directories the chosen runtime will create and create or update `projects/<tool>/.gitignore` only when those directories should remain uncommitted.
9. Create config only through explicit init/login/configure flows. Do not write config during reads or health checks.
10. Smoke test against `<artifact-path>`. Run `<artifact-path> --help`, `<artifact-path> --version`, and `<artifact-path> --json doctor`, and confirm the task can be completed without opening `projects/<tool>/`.
11. Run the shared validation core:
    - format, typecheck, or build as appropriate for the chosen runtime
    - help output, version output, artifact-path execution, exit codes, and no-auth or no-config `doctor`
    - at least one safe fixture, dry-run, or read-only end-to-end check that matches the CLI type

If a live write is needed for confidence, ask first and make it reversible or draft-only.

When the source is an existing script or shell history, split the working invocation into real phases: setup, discovery, download/export, transform/index, draft, upload, poll, live write. Preserve the flags, paths, and environment variables the user already relies on, then wrap the repeatable phases with stable IDs, bounded JSON, and file outputs.

For raw escape hatches, support read-only calls first. Do not run raw non-GET/HEAD requests against a live service unless the user asked for that specific write.

For media, artifact, or presigned upload flows, test each phase separately: create upload, transfer bytes, poll/read processing status, then attach or reference the resulting ID.

For fixture-backed prototypes, keep fixtures in a predictable owner-owned path and make the `scripts/...` surface locate them without requiring direct use of `projects/<tool>/`.

For log-oriented CLIs, keep deterministic snippet extraction separate from model interpretation. Prefer a command that emits filenames, line numbers or byte ranges, matched rules, and short excerpts.

### Validation by Runtime Type

Always run the shared validation core from the shipped artifact path. Then add the lane that matches the CLI:

- API-backed CLIs:
  - request builders, pagination or cursor handling when applicable, error mapping, and at least one live or fixture-backed read-only API call
  - `doctor --json` should include endpoint reachability when the CLI expects network access
- local/offline or shell CLIs:
  - shell syntax or interpreter startup checks, quoted-path handling, deterministic fixture runs, missing-tool diagnostics, destructive-path guard checks, and no-network execution
  - `doctor --json` should report local tool readiness, fixture availability, or offline mode rather than inventing API reachability checks
- hybrid CLIs:
  - combine the relevant API-backed and local/offline checks without forcing irrelevant test placeholders

## Rust Defaults

When building in Rust, use established crates instead of custom parsers:

- `clap` for commands and help
- `reqwest` for HTTP
- `serde` / `serde_json` for payloads
- `toml` for small config files
- `anyhow` for CLI-shaped error context

Keep the shipped compiled executable in `scripts/`. Use `projects/<tool>/` when the Rust implementation is large enough to benefit from a conventional project layout, and keep normal usage on the artifact in `scripts/...` rather than `target/`.
Use `Cargo.toml` as the default semver source of truth and wire `--version` to that version.
Keep `Cargo.toml`, `Cargo.lock`, local caches, and build outputs inside `projects/<tool>/`.
If Rust build outputs or local caches live inside `projects/<tool>/`, create or update `projects/<tool>/.gitignore` for entries such as `target/` while keeping the shipped artifact in `scripts/` tracked when appropriate.
If `projects/<tool>/` exists, document the Rust build/test workflow, version source of truth, semver bump policy, and the rebuild step that restores the shipped artifact in `scripts/` in `projects/<tool>/AGENTS.md`.

## TypeScript/Node Defaults

When building in TypeScript/Node:

- `commander` or `cac` for commands and help
- native `fetch`, the official SDK, or the user's existing HTTP helper for API calls
- `zod` only where external payload validation prevents real breakage
- `tsup`, `tsx`, or `tsc` using the owner's convention

Keep the shipped runnable artifact in `scripts/` and use `projects/<tool>/` for the full Node maintenance project when the tool becomes multi-file. If the Node tool is bundled or compiled, do not run it from `dist/` during normal execution.
Use `package.json` as the default semver source of truth and wire `--version` to that version.
Keep `package.json`, lockfiles, dependency installs, local caches, and build outputs inside `projects/<tool>/`.
If Node tooling creates project-local generated state, create or update `projects/<tool>/.gitignore` for entries such as `node_modules/`, `dist/`, `.tsbuildinfo`, and runtime-specific cache directories that should remain uncommitted.
If `projects/<tool>/` exists, document the Node build/test workflow, version source of truth, semver bump policy, and the rebuild step that restores the shipped artifact in `scripts/` in `projects/<tool>/AGENTS.md`.

## Python Defaults

When building in Python, prefer boring standard-library pieces unless the workflow needs more:

- `argparse` for commands and help, or `typer` when subcommands would otherwise get messy
- `urllib.request` / `urllib.parse`, `requests`, or `httpx` for HTTP, matching what is already installed or already used nearby
- `json`, `csv`, `sqlite3`, `pathlib`, and `subprocess` for local files, exports, databases, and existing scripts
- `uv` or a virtualenv only when dependencies are actually needed

Keep small Python runnable artifacts directly in `scripts/`. Introduce `projects/<tool>/` when the implementation grows beyond a simple script or small module. Do not treat virtualenv paths or external build directories as supported runtime entrypoints.
When the Python project has packaging metadata, use that manifest as the semver source of truth; otherwise keep one explicit version constant or file and wire `--version` to it.
Keep packaging metadata, lockfiles, virtualenvs, local caches, and build/test artifacts inside `projects/<tool>/`.
If `projects/<tool>/` exists, keep Python test modules under `projects/<tool>/tests/` by default instead of a host root or repo root test directory.
If Python tooling creates project-local generated state, create or update `projects/<tool>/.gitignore` for entries such as `.venv/`, `.uv-cache/`, `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, and similar local tooling directories that should remain uncommitted.
If `projects/<tool>/` exists, document the Python build/test workflow, version source of truth, semver bump policy, and the rebuild step that restores the shipped artifact in `scripts/` in `projects/<tool>/AGENTS.md`.

## Host Integration

After the embedded CLI works, update the owning skill docs or plugin docs so future Codex threads:

- execute from `<artifact-path>` during normal runtime usage
- expose and trust `<artifact-path> --version` as the runtime version check
- treat `<artifact-path>` as the shipped runnable artifact rather than a pointer to `target/`, `dist/`, or other build directories
- treat `projects/<tool>/` as the maintenance-only build project when one exists, not part of the normal runtime surface
- know the safe read path, intended draft/write path, and raw escape hatch
- have copy-pasteable executable examples that stay on the `<artifact-path>` surface
- use bare `<tool> ...` only as optional shorthand after the docs explicitly define how that command becomes executable

Add a `CLI Maintenance` section to the owning runtime docs. Require that section to:

- keep normal execution on `<artifact-path>`
- tell future threads to open `projects/<tool>/` only when fixing bugs, improving performance, rebuilding, or extending the CLI
- direct maintenance changes into `projects/<tool>/` when it exists, then rebuild the shipped artifact at `<artifact-path>` and re-verify through that artifact
- mention the version source of truth and the expectation that shipped CLI changes follow semver
- state that compiled outputs in `target/`, `dist/`, virtualenvs, or similar build locations are intermediates, not supported runtime entrypoints
- keep project-local ignore rules in `projects/<tool>/.gitignore`
- define the bump policy explicitly:
  - major for breaking CLI contract changes
  - minor for backward-compatible new features or meaningful capability additions
  - patch for backward-compatible bug fixes and corrections

Keep API reference details in the CLI docs or a host reference file. Keep the skill focused on ordering, safety, and examples future Codex threads should actually run.
