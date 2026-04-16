# Codex CLI Patterns

Use this reference when designing the command surface for an embedded CLI Codex should run from a skill's `scripts/` directory.

## Mental model

The CLI is Codex's command layer inside a skill. It should turn a service, app, API, log source, or database into shell commands Codex can run repeatedly from the shipped runnable artifact stored in that skill's `scripts/` directory.

Good CLIs for Codex expose composable primitives. Avoid a single command that tries to "do the whole investigation" when smaller discover, read, resolve, download, inspect, draft, and upload commands would compose better.

When the CLI lives inside a skill, keep the shipped runnable artifact in `scripts/` and treat any `projects/<tool>/` directory as the maintenance/build project behind that runtime surface.

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
Future Codex threads should be able to check whether the shipped CLI matches
the latest built implementation without opening `projects/<tool>/`.

## Prefer this command shape

Use product nouns, then verbs:

```bash
scripts/tool-name --version
scripts/tool-name --json doctor
scripts/tool-name --json accounts list
scripts/tool-name --json projects list
scripts/tool-name --json channels resolve --name codex
scripts/tool-name --json messages search "exact phrase"
scripts/tool-name --json messages context <message-id> --before 3 --after 3
scripts/tool-name --json logs download <build-url> --failed --out ./logs
scripts/tool-name --json media upload --file ./image.png
scripts/tool-name --json drafts create --body-file draft.json
```

For APIs whose native noun is already strong, direct verbs can be fine:

```bash
scripts/tool-name --json social-sets
scripts/tool-name --json drafts list --social-set <id>
scripts/tool-name --json request get /v2/me
```

The important rule is consistency. Do not mix many styles unless the product vocabulary demands it.

## Embedded skill runtime surface

When the CLI is embedded inside a skill:

- Run the tool from `scripts/...` during normal skill execution.
- Treat `scripts/<tool>` as the shipped runnable artifact for normal execution.
- Use `scripts/<tool> --version` as the stable version check.
- Do not inspect `projects/<tool>/` during normal execution.
- Open `projects/<tool>/` only when fixing, improving, rebuilding, or extending the implementation behind the `scripts/...` surface.
- Keep the command shape stable even if the implementation language or internal layout changes.
- Do not treat `target/`, `dist/`, virtualenv paths, or other build directories as supported runtime entrypoints.
- Keep manifests, lockfiles, dependency installs, caches, intermediate build outputs, and project-local build/test config inside `projects/<tool>/` when a real maintenance project exists.

Keep one semver source of truth. Use the runtime-native manifest version when
available, otherwise keep one explicit version constant or file and have
`--version` read from it.

If the runtime produces a compiled executable, copy, install, or generate the
shipped artifact into `scripts/`. Script-native runtimes may keep the shipped
script itself in `scripts/` when that script is the real artifact.

When the scaffold also creates project-local generated state, keep that ignore
policy close to `projects/<tool>/`:

- create or update `projects/<tool>/.gitignore` only when the CLI introduces
  build, cache, module, or environment directories inside that project
- keep the local `.gitignore` limited to those project-local generated paths
- do not create a no-op local `.gitignore` when there is nothing project-local
  to ignore

## Useful shapes from mature CLIs

Prefer these patterns over clever agent-only abstractions:

```bash
# Field-selected structured output: make common reads scriptable.
scripts/tool-name issues list --json number,title,url,state
scripts/tool-name issues list --json number,title --jq '.[] | select(.state == "open")'

# Human text by default, full API object when requested.
scripts/tool-name pods get <name>
scripts/tool-name pods get <name> -o json

# Product workflow commands, not just REST nouns.
scripts/tool-name logs tail
scripts/tool-name webhooks listen --forward-to localhost:4242/webhooks
scripts/tool-name webhooks trigger checkout.completed
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

Version reporting stays separate from `--json`: running `scripts/<tool> --version`
should print the current CLI semver cleanly, and `doctor --json` should include
that same version in its structured diagnostics.

For `--json`:

- Emit JSON to stdout only.
- Send progress and diagnostics to stderr.
- Keep success and error shapes documented.
- Redact tokens, cookies, customer secrets, private headers, and unrelated payloads.

For downloads and exports:

- Write files under a user-provided `--out` path when possible.
- In JSON output, return the file path, byte count if cheap, source URL or ID, and follow-up command.

For exit codes:

- Exit zero when the command succeeded, including an empty result.
- Exit nonzero for auth failure, invalid input, network failure, parse failure, API error, or incomplete upload/download.
- Make `doctor --json` usable even when auth is missing. It should report missing auth rather than crashing.

## Pagination and breadth

Start shallow by default. Add explicit knobs for breadth:

```bash
scripts/tool-name --json messages search "topic" --limit 10
scripts/tool-name --json messages search "topic" --limit 50 --all-pages --max-pages 3
scripts/tool-name --json drafts list --limit 20 --offset 40
```

Return the provider's real pagination field names, such as `next_cursor`, `next_url`, `offset`, or `page_count`, and document that shape clearly.

## Raw escape hatch

The raw command is a repair hatch, not the main interface.

Good raw commands still use configured auth, base URL, JSON parsing, redaction, status/error handling, and `--json`.

Make reads easy:

```bash
scripts/tool-name --json request get /v2/me
```

Treat raw writes as live writes. Do not hide POST/PUT/PATCH/DELETE behind a "debug" command.

## Hosting skill pattern

The hosting skill should teach the path through the embedded tool:

```md
Start with:

scripts/tool-name --version
scripts/tool-name --json doctor
scripts/tool-name --json accounts list

For [common job]:

scripts/tool-name --json ...
scripts/tool-name --json ...

Rules:

- Prefer the shipped artifact at `scripts/tool-name`.
- Check `scripts/tool-name --version` when confirming the shipped CLI matches the latest built implementation.
- Use --json when analyzing output.
- Create drafts by default.
- Do not publish/delete/retry/submit unless the user asked.
- Do not inspect `projects/<tool>/` during normal execution.
- Use `request get ...` only when high-level commands are missing.
```

Include JSON shape notes only when Codex needs them to choose the next command.

Add a `CLI Maintenance` section in the hosting skill when the tool has a
maintained implementation behind `scripts/...`. That section should say:

- normal runtime work stays on `scripts/...`
- `projects/<tool>/` is for bug fixes, performance work, rebuilds, and feature additions
- shipped CLI changes must update the implementation, rebuild the shipped
  artifact in `scripts/...`, and re-run `--help`, `--version`, and `--json doctor`
- compiled outputs in `target/`, `dist/`, virtualenvs, or similar paths are
  build intermediates rather than supported runtime entrypoints
- project-local generated state should be ignored through
  `projects/<tool>/.gitignore`, with a hosting-skill-root `.gitignore` reserved
  for generated state that truly lives at the skill root
- the CLI follows semver from one declared version source of truth
