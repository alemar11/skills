# dotagents

Reusable Codex skills, project maintainer skills, optional repo-local plugins, and MCP install helpers.

This repository is organized around reusable installable skills:

- **Reusable skills** under `skills/`, which can be linked locally or installed into Codex.

Project-only maintainer workflows live under `.agents/skills/`, optional repo-local plugin discovery lives under `.agents/plugins/`, and global MCP setup helpers live under `mcps/`.

## Repository Layout

| Path | Purpose |
| --- | --- |
| `skills/` | Reusable skills, each with a `SKILL.md` entrypoint and `agents/openai.yaml` metadata. |
| `plugins/` | Optional repo-local Codex plugins, each with `.codex-plugin/plugin.json` and optional bundled skills. |
| `.agents/skills/` | Project-local maintainer skills for working on this repository. |
| `.agents/plugins/marketplace.json` | Local plugin discovery surface for this checkout. |
| `mcps/` | Helpers for installing global Codex MCP server entries not bundled with Codex itself. |
| `skills-link.sh` | Local development helper that links reusable skills into `~/.agents/skills`. |

## Repo-Local Plugins

G is the repo-local Git and GitHub workflow plugin. Skills use direct `git` and
`gh`; its small shared CLI handles attachments, verified PR publication, review
receipts, guarded stacks, worktree fingerprints, and star-list membership
updates. It has no GitHub connector dependency. It bundles:

| Skill | Purpose |
| --- | --- |
| `g:git-commit` | Create or push explicit regular, fixup, or amend-fixup commits without publishing a PR. |
| `g:github-repository-triage` | Triage issue and pull request queues across one or more repositories read-only. |
| `g:github-issues` | Manage GitHub issues, attachments, relationships, label/type classification, and taxonomy proposals. |
| `g:github-projects` | Manage GitHub Projects, fields, items, repository or team links, templates, and lifecycle. |
| `g:github-investigation` | Investigate issues, pull requests, and proposed fixes using repository evidence. |
| `g:github-actions` | Diagnose or explicitly fix failing GitHub Actions checks. |
| `g:github-delivery-status` | Inspect exact-head pull-request delivery readiness, merge policy, rulesets, checks, queue, and automation state without mutating GitHub. |
| `g:github-review-threads` | Inspect review threads, address selected feedback, and explicitly reply or resolve. |
| `g:github-releases` | Inspect, plan, publish, and validate releases, tags, notes, assets, and packages. |
| `g:github-stars` | Manage the authenticated user's GitHub stars and star lists. |
| `g:send` | Confirm scope and caller-provided resolved issues, commit, push, add automatic issue-closing references, and open or update one pull request. Stack linking and review requests are separate. |
| `g:github-stack` | Manage stacked branches and dependent pull requests through the G stack CLI, including inspection, linking, rebase, sync, navigation, and explicit stack-wide publication or merge. |
| `g:versioning` | Distinguish versions, tags, and GitHub Releases; suggest SemVer and operate approval-gated release-tag workflows. |
| `g:audit` | Monitor active sessions using G skills and return a prioritized read-only report. |

SE is the repository's software-delivery workflow plugin. It refines and
studies ideas, turns them into Feature plans, delivers them through reviewed
pull requests or lightweight local commits, maintains project knowledge, and
includes delivery workflow retrospectives:

| Skill | Purpose |
| --- | --- |
| `se:learn` | Maintain durable project knowledge, decisions, localization guidance, and code review rules. |
| `se:grilling-session` | Refine a topic or handoff through repository-grounded questions with concrete recommended answers. |
| `se:study` | Grill one curated handoff, then run read-only analysis in one App controller or the current CLI session with optional Luna subagents. |
| `se:adversarial-review` | Pressure-test a software change with an independent read-only review and evidence-backed findings. |
| `se:review-pr` | Request or resume a hosted Codex PR review, wait, and report the provider result to the calling task. |
| `se:idea` | Save a concrete proposal for later spec planning, or preview it locally. |
| `se:spec` | Create or revise one coherent feature spec and actionable task plan, saving to GitHub or a single Markdown file. |
| `se:deliver-features` | Deliver saved specs or selected tasks through surface-aware isolated workers, reviewed ready PRs, and verified outcomes from the current task. |
| `se:implement` | Implement selected local work from a spec, ticket, issue, or direct request, validate it, and commit only the required files without orchestration or publication. |

Xcode is the repository's Apple developer-tools plugin. It preserves the
official stable and beta release-note resolver and adds safe launch guidance
for Apple's native headless MCP server:

| Skill | Purpose |
| --- | --- |
| `xcode:whats-new` | Resolve release notes for the active Xcode plus the latest stable and beta versions, or for one requested version. |
| `xcode:mcp` | Safely launch and verify the Xcode-provided headless MCP server on attended Macs, unattended hosts, or explicitly isolated CI machines. |

## Reusable Skills

| Skill | Purpose |
| --- | --- |
| `codex-cli` | Launch one complete prompt in an isolated Codex CLI run when explicitly requested. |
| `crusty` | Skeptical, evidence-backed critique of work decisions and implementations. Use only when explicitly asked for Crusty. |
| `ms-roberts` | Silently track substantive grammar errors in medium or complex user-authored English; report on request or session close. |
| `socrates` | Offer opt-in exercises about meaningful recent engineering work, or quiz the user when explicitly requested. |
| `okf` | Write, scaffold, inspect, and validate Open Knowledge Format Markdown bundles with the shipped CLI. |
| `skill-cli-creator` | Create or refactor CLIs shipped inside a skill or plugin bundle. |
| `tanstack` | Build, debug, review, or migrate applications using TanStack packages. |
| `focus` | Create one new Codex task with a compact handoff of the current discussion. Use only when explicitly invoked. |
| `postgres` | Inspect Postgres databases, design or run SQL, and manage migrations through the shipped Postgres CLI. |
| `plugins-reload` | Reload this repository’s G, SE, and Xcode plugin installations when explicitly requested. |
| `skill-audit` | Audit skill or plugin instructions and usage evidence read-only. Use only when explicitly invoked as $skill-audit. |
| `swift-api-design` | Design, rename, or review Swift API surfaces using the bundled official API Design Guidelines. |
| `swift-docc` | Author, review, preview, or publish Swift-DocC symbol documentation, articles, and tutorials. |
| `youtube` | Search YouTube videos and playlists or answer from timestamped transcripts. Use for YouTube links and spoken-content research. |
| `ghostty` | Inspect or arrange Ghostty terminals and edit configuration or keybindings when explicitly requested. |
| `herdr` | Inspect or control Herdr terminal workspaces, panes, and agents when the user explicitly asks to use Herdr. |

### TanStack References

The reusable `tanstack` skill covers TanStack AI, Charts, CLI, Config, DB, Devtools, Form, Highlight, Hotkeys, Markdown, Pacer, Query, Ranger, Router, Start, Store, Table, Virtual, and cross-stack integration from one `$tanstack` invocation surface.

- Product references live under `skills/tanstack/references/`: `ai.md`, `charts.md`, `cli.md`, `config.md`, `db.md`, `devtools.md`, `form.md`, `highlight.md`, `hotkeys.md`, `integration.md`, `markdown.md`, `pacer.md`, `query.md`, `ranger.md`, `router.md`, `start.md`, `store.md`, `table.md`, `virtual.md`.
- Router references include `router-routing-structure.md`, `router-navigation-and-search.md`, `router-data-loading-and-ssr.md`, `router-auth-and-failures.md`, and `router-plugin-and-splitting.md`.
- Start references include `start-framework-and-execution.md`, `start-server-functions-and-routes.md`, `start-middlewares-and-server-core.md`, `start-server-components-and-migrations.md`, and `start-deployments.md`.
- CLI references include `cli-scaffolding.md`, `cli-addons-existing-app.md`, `cli-ecosystem-integrations.md`, `cli-custom-addons-dev-watch.md`, and `cli-docs-and-library-metadata.md`.

This repository ships one broad reusable `tanstack` skill rather than separate upstream-style product plugins, narrow focused skills, or bundle aliases such as `tanstack-all`. For TanStack application work, install the reusable TanStack skill instead of copying advice from mixed community sources.

## Skill Dependencies

- `se:study` builds one curated handoff, starts Grilling Session immediately, and then
  runs a strictly read-only investigation on the active Codex surface. In the
  App it creates one separate visible Sol/medium controller in the exact saved
  local project without a worktree. In the CLI the current session and its
  current profile remain the controller. On either surface, substantial
  independent evidence work may use native Luna/max subagents in the
  controller's working-directory context; Study never creates additional
  visible App worker tasks.
  Five is an absolute worker cap; larger requests are capped and reported
  automatically. Stable controller task and subagent identities are the only
  identity and recovery keys. App-only controller title, task telemetry, and
  parent monitoring do not apply to CLI runs. Neither a controller nor a
  subagent may invoke Study recursively or create another worker layer. When
  no worker count is specified, focused analysis uses no subagent, one is
  reserved for a large or noisy evidence surface, and multiple subagents
  require genuinely independent tracks; five is a cap, not the default.
- `se:study`, `$se:grilling-session`, and `$se:learn` ship together in the SE plugin.
  Study invokes its sibling Grilling Session workflow directly, which uses Learn for a
  read-only Project Context pass. The separate App Study task or current CLI
  session asks the user one question with a recommended answer per turn and
  cannot plan workers until the handoff is confirmed or the user stops
  grilling.
- `maintainer` uses `$skill-audit` conditionally when health diagnosis or workflow hardening needs portfolio, prompt-quality, overlap, or session evidence; requires `$skill-creator` or `$plugin-creator` for substantial package reshapes; and requires native `codex review` for non-trivial implementation closeout.
- The G-dependent SE skills run a read-only Codex plugin preflight before their first required G handoff and fail closed when G is unavailable; Feature publication requires `$g:github-issues`; its optional classification branch never gates semantic publication, while no SE skill installs G automatically.
- `se:idea` traverses a graph-first in-memory capture workflow and publishes to GitHub by default; an explicitly requested preview stays entirely local. Its durable output is the hosted issue, not project memory, and its optional idea-source handoff remains transient.
- `se:learn` runs in the invoking task and performs only authorized local-repository context changes; it has no external dependency preflight, task profile, GitHub transport, publication, or worker delegation contract.
- `se:grilling-session` is read-only and explicit or parent-composed. It depends on
  `$se:learn` for context inspection, returns a transient refined handoff, and
  never creates tasks or captures durable knowledge automatically.
- `se:spec` saves one coherent spec with stable task identities, recommended
  order, real prerequisites, and completion checks. GitHub is the default;
  explicit Markdown saves contain the entire spec and task plan in one file.
  A local-source Markdown save or preview requires no G workflow. Existing
  artifacts retain their authority; exports are explicit snapshots.
- SE skills retain the same delegation policy standalone and composed. Implement
  implements, validates and commits; independent review is a separate caller-owned
  gate, with no reviewer delegation inside Implement.
- `se:review-pr` reuses a completed current-target review, resumes a pending
  request, or requests and waits when needed. It returns the provider result to
  the calling task, standalone or composed, with no subagents, repairs, CI or
  acceptance decisions. Explicit inspect-only scope remains read-only.
- `se:deliver-features` accepts saved GitHub/Markdown specs or explicitly selected
  tasks and derives repository-bound delivery units from those contributions. Task
  dependencies do not mandate Git stacks. The current coordinator verifies actual
  prerequisites, useful PR boundaries, complete task coverage, and assembled
  feature outcomes at the exact repository HEAD vector. It preserves isolated
  subagent worktrees, repository claims, independent candidate review, explicitly
  requested `@codex review` for each ready PR HEAD, required validation/CI, and
  two repair rounds per PR. It composes Implement for local work and Review PR
  for hosted review monitoring. Safe pauses preserve work and release claims after
  quiescence; resume reacquires and reconciles evidence. Task progress is updated
  in the original planning destination. It supplies
  exact justified closing references to G; partial work never closes a complete
  spec. Every invocation closes with delivery results, available duration/token
  usage, and a workflow audit proposing improvements reusable across projects.
  Merge, deploy, and direct issue closure remain separately authorized.

## Project-Local Skills

| Skill | Path | Purpose |
| --- | --- | --- |
| maintainer | `.agents/skills/maintainer/` | Manually audit, maintain, and re-engineer repo skills and plugins through health, lifecycle, validation, metadata, and explicit refresh workflows. |

Project-local skills are repository-specific and are not included in reusable install commands.

## Installation

### Use Repo-Local Plugins

Repo-local plugins are exposed through `.agents/plugins/marketplace.json`; they are not installed by `skills-link.sh`.

Register the `alemar11` marketplace from GitHub, then install the required plugins:

```sh
codex plugin marketplace add alemar11/dotagents --ref main
codex plugin add g@alemar11
codex plugin add se@alemar11
codex plugin add xcode@alemar11
```

If the `alemar11` marketplace is already registered, install the plugins directly:

```sh
codex plugin add g@alemar11
codex plugin add se@alemar11
codex plugin add xcode@alemar11
```

For local development from a dotagents checkout, register the checkout instead
of the GitHub source, then install the same plugin:

```sh
codex plugin marketplace add /path/to/dotagents
codex plugin add g@alemar11
codex plugin add se@alemar11
codex plugin add xcode@alemar11
```

During local development, validate each changed plugin and reinstall it from
the repository source. G has a dedicated helper; SE and Xcode are reinstalled
directly:

```sh
plugins/g/projects/g/scripts/reinstall-local
codex plugin add se@alemar11 --json
codex plugin add xcode@alemar11 --json
```

For a Git-backed marketplace checkout, refresh the marketplace before reinstalling:

```sh
codex plugin marketplace upgrade alemar11
codex plugin remove g@alemar11
codex plugin add g@alemar11
codex plugin remove se@alemar11
codex plugin add se@alemar11
codex plugin remove xcode@alemar11
codex plugin add xcode@alemar11
```

When migrating from the retired Feature Flow plugin identity, remove the old
installation before installing SE:

```sh
codex plugin remove feature-flow@alemar11
codex plugin add se@alemar11
```

Restart Codex or open a fresh task after installation so the bundled skills and
connectors are discovered. Do not edit installed cache copies under
`~/.codex/plugins/cache/`.

### Link Reusable Skills For Local Development

Run this from the repository root to link `skills/` into `~/.agents/skills`:

```sh
./skills-link.sh
```

This helper only links reusable skills. It does not install, mirror, or rewrite plugin marketplace entries.

### Install Reusable Skills With `skill-installer` (Codex-only)

Inside Codex, install all reusable skills with:

```text
Use $skill-installer to install skills from alemar11/dotagents --path skills/codex-cli skills/crusty skills/ms-roberts skills/socrates skills/okf skills/skill-cli-creator skills/tanstack skills/focus skills/postgres skills/plugins-reload skills/skill-audit skills/swift-api-design skills/swift-docc skills/youtube
```

Install one reusable skill by passing only its path:

```text
Use $skill-installer to install skills from alemar11/dotagents --path skills/codex-cli
```

Replace `skills/codex-cli` with any path listed in the reusable skills table.

### Install Reusable Skills With `npx skills`

These commands use the [`vercel-labs/skills`](https://github.com/vercel-labs/skills) CLI and target Codex directly.

List the skills available in this repository:

```sh
npx skills add alemar11/dotagents --list
```

Install all reusable skills globally for Codex:

```sh
npx skills add alemar11/dotagents -a codex -g -y \
  --skill codex-cli \
  --skill crusty \
  --skill ms-roberts \
  --skill socrates \
  --skill okf \
  --skill skill-cli-creator \
  --skill tanstack \
  --skill focus \
  --skill study \
  --skill postgres \
  --skill plugins-reload \
  --skill skill-audit \
  --skill swift-api-design \
  --skill swift-docc \
  --skill youtube
```

Install one reusable skill globally for Codex:

```sh
npx skills add alemar11/dotagents -a codex -g -y --skill codex-cli
```

Replace `codex-cli` with any skill name from the reusable skills table. Omit `-g` to install into the current project's `.agents/skills/` instead of your global `~/.codex/skills/`.

Restart Codex after installing or updating skills.
