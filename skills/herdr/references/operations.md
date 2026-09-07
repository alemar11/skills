# Herdr Operations

Check installed help for the relevant `pane`, `agent`, `workspace`, or `tab`
group. Bare groups print usage; nested creation commands can mutate with defaults.

## Targeting and layout

Inspect `herdr pane current --current`, `herdr pane list`, and
`herdr agent list`. Workspace/tab/pane IDs are opaque; capture them from JSON.
A moved pane receives a new workspace-qualified ID. The inherited old caller
context may still resolve inside that process, but is not a general target.
Agent names follow the current occupant and disappear when it exits or is
replaced. Names match `[a-z][a-z0-9_-]{0,31}` and must be unique among live agents.
Agent commands accept that name or its pane ID, not a terminal ID or agent kind.

Inspect `herdr pane layout --pane "$HERDR_PANE_ID"`. Split wide panes right and
tall panes down, unless requested otherwise:

```sh
herdr pane split --current --direction right --cwd "$PWD" --no-focus
```

Read the new ID from `.result.pane.pane_id`. Workspace and tab creation return
`.result.root_pane`; a move returns `.result.move_result.pane.pane_id`.

## Agents

Start only in a shell pane at its prompt, without a foreground process:

```sh
herdr agent start reviewer --kind codex --pane <returned-pane-id>
herdr agent prompt reviewer "Review the current diff." --wait --timeout 45000
herdr agent read reviewer --source recent-unwrapped --lines 120
```

Use the requested agent kind. Native arguments go after `--` in `agent start`.
Startup normally waits up to 30 seconds for readiness. If startup reports
`agent_not_ready`, inspect the retained agent name and wait for readiness before
prompting. Read [states](states.md) for lifecycle and prompt errors.

`prompt --wait` and standalone `agent wait` settle on idle, done, or blocked.
Use `--until` only to request another condition. A working agent's current turn
can satisfy the wait: inspect its answer to establish which work completed.
A timeout does not establish failure or justify resending a prompt.

Read `agent get` and `agent read` before responding to blocked UI. Logical keys
use `agent send-keys`, such as `esc` or `ctrl+c`; interruption needs task scope.

## Ordinary processes

Use pane commands for shells, tests, and servers:

```sh
herdr pane run <pane-id> "just test"
herdr pane wait-output <pane-id> --match "test result" --timeout 45000
herdr pane read <pane-id> --source recent-unwrapped --lines 120
```

`pane run` sends text and Enter. Output matching includes existing scrollback,
so a match alone may precede the current run. Use a bounded timeout; omission
can wait indefinitely. `--match` is literal and `--regex` uses Rust regex syntax.

Read sources: `visible` is the viewport, `recent` retains wraps,
`recent-unwrapped` joins soft wraps, and `detection` is the agent detector's
bottom-buffer snapshot. Use ANSI output only when styling is evidence.

Alternate-screen output may not enter host scrollback. If a larger read still
misses a response, ask the agent to write the complete result to a temporary
Markdown file and return its path, then read that file. Do not require file
output on every initial prompt.

Server errors use JSON on stderr with exit code 1; syntax errors use code 2.
