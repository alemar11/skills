---
name: skill-cli-creator
description: Build a composable embedded CLI that lives inside a skill. Use when Codex needs to create or refactor a skill-owned command surface under `scripts/`, keep normal runtime usage on that `scripts/...` surface, and optionally maintain one or more larger CLI projects under `projects/`.
---

# Skill CLI Creator

Create a real CLI that future Codex threads run from a skill's `scripts/` directory.

Build for embedded skill use only. Do not use this skill for standalone global CLIs, separate personal CLI repos, or PATH-first packaging.

## Start

Name the hosting skill, the CLI source material, and the first real jobs it should do:

- Host skill: the skill directory that will own the CLI surface.
- Source: API docs, OpenAPI JSON, SDK docs, curl examples, browser app, existing internal script, article, or working shell history.
- Jobs: literal reads/writes such as `list drafts`, `download failed job logs`, `search messages`, `upload media`, `read queue schedule`.
- Artifact path: the shipped runnable artifact path such as `scripts/ci-logs`, `scripts/slack-cli`, or `scripts/buildkite-logs`.

Before scaffolding, check whether the proposed shipped artifact path already exists inside the hosting skill:

```bash
test -e scripts/<tool-name> && echo "exists"
```

If it exists, choose a clearer entry name or evolve the existing command instead of creating a competing surface.

## Embedded Skill Layout

Keep the layout model short and explicit:

- `scripts/` contains the shipped runnable artifacts used during normal skill execution.
- `projects/<tool>/` is the full maintenance/build project behind one shipped CLI.
- `<project-root>/.skills/<hosting-skill>/` is project-local config only.

Keep these invariants explicit in the hosting skill and CLI docs:

- Run the tool from `scripts/...` during normal skill execution.
- Do not inspect `projects/<tool>/` during normal execution.
- Do not require normal skill users to run code directly from `projects/<tool>/`.
- Treat `scripts/<tool>` or `scripts/<tool>.<ext>` as the shipped runnable artifact regardless of language.
- Require `scripts/<tool> --version` as part of the stable runtime surface.
- Open `projects/<tool>/` only when fixing, improving, rebuilding, or extending the implementation behind `scripts/...`.
- Keep script-native runnable artifacts entirely in `scripts/`; introduce `projects/<tool>/` only when the implementation grows enough to justify a real maintenance project.
- For larger multi-file implementations, keep the shipped runnable artifact in `scripts/` and the maintenance-oriented implementation in `projects/<tool>/`.
- Keep the CLI project self-contained inside `projects/<tool>/`. Put manifests, lockfiles, dependency installs, caches, intermediate build outputs, project-local test/build config, and source there unless the user explicitly asks for a different wrapper layout.
- Do not execute compiled CLIs from `target/`, `dist/`, virtualenv paths, or other build directories during normal skill usage.
- If the runtime produces a compiled executable, copy, install, or generate the shipped artifact into `scripts/` before considering the CLI ready.
- If `projects/<tool>/` exists, require `projects/<tool>/AGENTS.md` with build, test, rebuild, runtime prerequisites, safe-maintenance instructions, the version source of truth, the semver bump policy, and rebuild instructions for restoring the shipped artifact in `scripts/...`.
- Treat `<project-root>/.skills/<hosting-skill>/` as config-only, not a place for helper scripts or implementation code.
- If the scaffold introduces project-local generated state that must not be committed, create or update `projects/<tool>/.gitignore` and keep it scoped to that tool's generated paths.
- Do not rely on the repo root `.gitignore` or the hosting skill root `.gitignore` for project-local build, cache, or module directories when those artifacts live inside `projects/<tool>/`.
- Keep a hosting-skill-root `.gitignore` only for generated state that truly lives at the skill root.
- Do not create an empty or no-op `projects/<tool>/.gitignore` when the CLI introduces no project-local generated state.
- Do not introduce alternative generic maintenance folders such as `src/`, `code/`, `impl/`, or `source/` for the full project layout.

For the detailed command-shape, runtime-surface, JSON, and hosting-skill examples, read [references/agent-cli-patterns.md](references/agent-cli-patterns.md).

## Project-Local Ignore Policy

Use a project-local `.gitignore` only when the embedded CLI introduces generated
state inside `projects/<tool>/` that should not be committed.

- Create or update `projects/<tool>/.gitignore` when the scaffold introduces
  project-local build, cache, module, or environment directories.
- Keep the local `.gitignore` scoped to that project's generated state rather
  than duplicating repo-wide ignore rules.
- Verify that shipped artifacts in `scripts/` remain tracked when appropriate,
  while uncommitted intermediates are ignored close to `projects/<tool>/`.
- Typical examples include `node_modules/`, `dist/`, `target/`, `.venv/`,
  `.uv-cache/`, `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, and similar
  tool-specific local directories when they live inside `projects/<tool>/`.

## CLI Versioning

Versioning is required for every embedded CLI produced through this skill, even
when the implementation is small.

- Support `scripts/<tool> --version` on the public runtime surface.
- Keep one semver source of truth for the CLI version.
- Use the artifact stored in `scripts/` as the only supported normal-execution surface.
- Use the runtime-native manifest version when one exists, such as
  `Cargo.toml`, `package.json`, or `pyproject.toml`.
- When no native manifest exists, keep the version in one explicit code
  constant or a dedicated version file rather than scattering literals.
- Treat doc-only updates as no-version-bump changes unless they accompany
  shipped CLI behavior changes.

## Choose the Runtime

Before choosing, inspect the user's machine and source material:

```bash
command -v cargo rustc node pnpm npm python3 uv || true
```

Then choose the least surprising toolchain:

- Default to **Rust** when the embedded CLI needs a larger maintained implementation and benefits from a real project under `projects/<tool>/`.
- Use **TypeScript/Node** when the official SDK, auth helper, browser automation library, or existing repo tooling is the reason the embedded CLI can be better.
- Use **Python** when the source is data science, local file transforms, notebooks, SQLite/CSV/JSON analysis, or Python-heavy admin tooling.
- Use **shell** for thin orchestration surfaces whose shipped runnable script can live entirely in `scripts/`.

Do not pick a language that adds setup friction unless it materially improves the CLI. If the best language is not installed, either install the missing toolchain with the user's approval or choose the next-best installed option.

State the choice in one sentence before scaffolding, including the reason and the installed toolchain you found.

## Command Contract

Sketch the command surface in chat before coding. Include the `scripts/...` artifact path, discovery commands, resolve or ID-lookup commands, read commands, write commands, raw escape hatch, auth/config choice, and any rebuild behavior needed to restore the shipped artifact in `scripts/`.

Use [references/agent-cli-patterns.md](references/agent-cli-patterns.md) for the expected composable CLI shape, command ordering, JSON conventions, pagination patterns, and hosting-skill examples.

Build toward a surface where:

- `scripts/<tool> --help` exposes the major capabilities.
- `scripts/<tool> --version` reports the current CLI semver from the single
  source of truth.
- `scripts/<tool> --json doctor` verifies config, auth, version, endpoint reachability, and missing setup.
- `scripts/<tool> init ...` stores local config when env-only auth is painful.
- Discovery commands find accounts, projects, workspaces, teams, queues, channels, repos, dashboards, or other top-level containers.
- Resolve commands turn names, URLs, slugs, permalinks, customer input, or build links into stable IDs so future commands do not repeat broad searches.
- Read commands fetch exact objects and list/search collections. Paginated lists support a bounded `--limit`, cursor, offset, or clearly documented default.
- Write commands do one named action each: create, update, delete, upload, schedule, retry, comment, or draft. They accept the narrowest stable resource ID, support `--dry-run`, `draft`, or `preview` first when the service allows it, and do not hide writes inside broad commands such as `fix`, `debug`, or `auto`.
- `--json` returns stable machine-readable output.
- Repeated jobs get high-level verbs rather than only a generic `request` command.
- The raw escape hatch exists, but it stays secondary to the high-level commands.

Document the JSON policy in the hosting skill's `SKILL.md` or reference files: whether commands return raw API-shaped responses or a CLI-specific envelope, plus the success shape, error shape, and one example for each command family. Under `--json`, errors must be machine-readable and must not contain credentials.

## Auth and Config

Support the boring paths first, in this precedence order:

1. Environment variable using the service's standard name, such as `GITHUB_TOKEN`.
2. Project-local config under `<project-root>/.skills/<hosting-skill>/<hosting-skill>.toml` when env-only auth is painful.
3. `--api-key` or a tool-specific token flag only for explicit one-off tests. Prefer env/config for normal use because flags can leak into shell history or process listings.

Keep config placement explicit:

- `<project-root>/.skills/<hosting-skill>/` is config-only, not a place for helper scripts or implementation code.
- Prefer skill-local persisted config over any external config path.
- Only use an external config path if the user explicitly asks for it.
- For one-off runs, prefer environment variables over writing config.

Never print full tokens. `doctor --json` should say whether a token is available, the auth source category (`flag`, `env`, `config`, provider default, or missing), and what setup step is missing.

If the CLI can run without network or auth, make that explicit in `doctor --json`: report fixture/offline mode, whether fixture data was found, and whether auth is not required for that mode.

For internal web apps sourced from DevTools curls, create sanitized endpoint notes before implementing: resource name, method/path, required headers, auth mechanism, CSRF behavior, request body, response ID fields, pagination, errors, and one redacted sample response. Never commit copied cookies, bearer tokens, customer secrets, or full production payloads.

Use screenshots to infer workflow, UI vocabulary, fields, and confirmation points. Do not treat screenshots as API evidence unless they are paired with a network request, export, docs page, or fixture.

## Build Workflow

1. Read the source just enough to inventory resources, auth, pagination, IDs, media/file flows, rate limits, and dangerous write actions. If the docs expose OpenAPI, download or inspect it before naming commands.
2. Sketch the command list in chat. Keep names short and shell-friendly.
3. Scaffold the CLI inside the hosting skill using the two-surface layout: `scripts/` for runtime, optional `projects/<tool>/` for maintenance.
   - Add or wire the single semver source of truth before the CLI contract is considered complete.
   - Ensure the shipped runnable artifact lives in `scripts/`; treat build outputs elsewhere as intermediates only.
   - If the runtime produces a compiled executable, copy, install, or generate that executable into `scripts/`.
   - Inspect which project-local generated directories the chosen runtime will create and create or update `projects/<tool>/.gitignore` only when those directories should remain uncommitted.
   - If `projects/<tool>/` is introduced, create `projects/<tool>/AGENTS.md` with build, test, rebuild, runtime prerequisites, safe-maintenance instructions, the version source of truth, the semver bump policy, and exact steps to restore the shipped artifact in `scripts/...`.
4. Implement `doctor`, discovery, resolve, read commands, one narrow draft or dry-run write path if requested, and the raw escape hatch.
5. Expose the shipped runnable artifact under `scripts/` and treat outputs in `target/`, `dist/`, virtualenvs, or similar locations as build intermediates rather than supported runtime entrypoints.
6. Verify the ignore policy before finalizing the scaffold: confirm intended project-local generated paths are ignored and the shipped artifact in `scripts/` remains tracked when appropriate.
7. Smoke test against the artifact stored in `scripts/...`. Run `scripts/<tool> --help`, `scripts/<tool> --version`, and `scripts/<tool> --json doctor`, and confirm the task can be completed without opening `projects/<tool>/`.
8. Run format, typecheck/build, unit tests for request builders, pagination/request-body builders, no-auth `doctor`, help output, and at least one fixture, dry-run, or live read-only API call.

If a live write is needed for confidence, ask first and make it reversible or draft-only.

When the source is an existing script or shell history, split the working invocation into real phases: setup, discovery, download/export, transform/index, draft, upload, poll, live write. Preserve the flags, paths, and environment variables the user already relies on, then wrap the repeatable phases with stable IDs, bounded JSON, and file outputs.

For raw escape hatches, support read-only calls first. Do not run raw non-GET/HEAD requests against a live service unless the user asked for that specific write.

For media, artifact, or presigned upload flows, test each phase separately: create upload, transfer bytes, poll/read processing status, then attach or reference the resulting ID.

For fixture-backed prototypes, keep fixtures in a predictable skill-owned path and make the `scripts/...` surface locate them without requiring direct use of `projects/<tool>/`.

For log-oriented CLIs, keep deterministic snippet extraction separate from model interpretation. Prefer a command that emits filenames, line numbers or byte ranges, matched rules, and short excerpts.

## Rust Defaults

When building in Rust, use established crates instead of custom parsers:

- `clap` for commands and help
- `reqwest` for HTTP
- `serde` / `serde_json` for payloads
- `toml` for small config files
- `anyhow` for CLI-shaped error context

Keep the shipped compiled executable in `scripts/`. Use `projects/<tool>/` when the Rust implementation is large enough to benefit from a conventional project layout, and keep normal skill usage on the artifact in `scripts/...` rather than `target/`.
Use `Cargo.toml` as the default semver source of truth and wire `--version` to
that version.
Keep `Cargo.toml`, `Cargo.lock`, local caches, and build outputs inside
`projects/<tool>/`.
If Rust build outputs or local caches live inside `projects/<tool>/`, create or
update `projects/<tool>/.gitignore` for entries such as `target/` while keeping
the shipped artifact in `scripts/` tracked when appropriate.
If `projects/<tool>/` exists, document the Rust build/test workflow, version
source of truth, semver bump policy, and the rebuild step that restores the
shipped artifact in `scripts/` in `projects/<tool>/AGENTS.md`.

## TypeScript/Node Defaults

When building in TypeScript/Node:

- `commander` or `cac` for commands and help
- native `fetch`, the official SDK, or the user's existing HTTP helper for API calls
- `zod` only where external payload validation prevents real breakage
- `tsup`, `tsx`, or `tsc` using the hosting skill's convention

Keep the shipped runnable artifact in `scripts/` and use `projects/<tool>/` for the full Node maintenance project when the tool becomes multi-file. If the Node tool is bundled or compiled, do not run it from `dist/` during normal execution.
Use `package.json` as the default semver source of truth and wire `--version`
to that version.
Keep `package.json`, lockfiles, dependency installs, local caches, and build
outputs inside `projects/<tool>/`.
If Node tooling creates project-local generated state, create or update
`projects/<tool>/.gitignore` for entries such as `node_modules/`, `dist/`,
`.tsbuildinfo`, and runtime-specific cache directories that should remain
uncommitted.
If `projects/<tool>/` exists, document the Node build/test workflow, version
source of truth, semver bump policy, and the rebuild step that restores the
shipped artifact in `scripts/` in `projects/<tool>/AGENTS.md`.

## Python Defaults

When building in Python, prefer boring standard-library pieces unless the workflow needs more:

- `argparse` for commands and help, or `typer` when subcommands would otherwise get messy
- `urllib.request` / `urllib.parse`, `requests`, or `httpx` for HTTP, matching what is already installed or already used nearby
- `json`, `csv`, `sqlite3`, `pathlib`, and `subprocess` for local files, exports, databases, and existing scripts
- `uv` or a virtualenv only when dependencies are actually needed

For embedded skill CLIs, keep small Python runnable artifacts directly in `scripts/`. Introduce `projects/<tool>/` when the implementation grows beyond a simple script or small module. Do not treat virtualenv paths or external build directories as supported runtime entrypoints.
When the Python project has packaging metadata, use that manifest as the semver
source of truth; otherwise keep one explicit version constant or file and wire
`--version` to it.
Keep packaging metadata, lockfiles, virtualenvs, local caches, and build/test
artifacts inside `projects/<tool>/`.
If Python tooling creates project-local generated state, create or update
`projects/<tool>/.gitignore` for entries such as `.venv/`, `.uv-cache/`,
`__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, and similar local tooling
directories that should remain uncommitted.
If `projects/<tool>/` exists, document the Python build/test workflow, version
source of truth, semver bump policy, and the rebuild step that restores the
shipped artifact in `scripts/` in `projects/<tool>/AGENTS.md`.

## Hosting Skill Integration

After the embedded CLI works, update the hosting skill so future Codex threads:

- execute from `scripts/...` during normal runtime usage
- expose and trust `scripts/<tool> --version` as the runtime version check
- treat `scripts/<tool>` as the shipped runnable artifact rather than a pointer to `target/`, `dist/`, or other build directories
- treat `projects/<tool>/` as the maintenance/build project when one exists
- know the safe read path, intended draft/write path, and raw escape hatch
- have copy-pasteable examples that stay on the `scripts/...` surface

Add a `CLI Maintenance` section to the hosting skill. Require that section to:

- keep normal execution on `scripts/...`
- tell future threads to open `projects/<tool>/` only when fixing bugs, improving
  performance, rebuilding, or extending the CLI
- direct maintenance changes into `projects/<tool>/` when it exists, then rebuild the
  shipped artifact in `scripts/...` and re-verify through that artifact
- mention the version source of truth and the expectation that shipped CLI
  changes follow semver
- state that compiled outputs in `target/`, `dist/`, virtualenvs, or similar
  build locations are intermediates, not supported runtime entrypoints
- keep project-local ignore rules in `projects/<tool>/.gitignore`, and update a
  hosting-skill-root `.gitignore` only when new generated state is introduced at
  the skill root itself
- define the bump policy explicitly:
  major for breaking CLI contract changes,
  minor for backward-compatible new features or meaningful capability
  additions,
  and patch for backward-compatible bug fixes and corrections

Keep API reference details in the CLI docs or a skill reference file. Keep the skill focused on ordering, safety, and examples future Codex threads should actually run. For embedded skill CLIs, keep normal runtime examples on the `scripts/...` surface and reserve `projects/<tool>/` for maintenance-oriented examples only.
