---
name: herdr
description: Inspect or control Herdr terminal workspaces, panes, and agents when the user explicitly asks to use Herdr.
---

# Herdr

Use the installed `herdr` CLI for the current session. Start with `herdr --help`,
then the relevant command group. Do not run bare `herdr` for discovery: it opens
the TUI. Do not probe mutating subcommands with omitted arguments; some execute
with defaults.

Use explicit returned IDs or unique live agent names. Prefer `--current` for
the caller pane; an omitted target may select another client's focused pane.
After moving a pane, use its returned new ID or live agent name.

For layout, command, or agent operations, read
[operations](references/operations.md). For lifecycle interpretation, read
[states](references/states.md). Pane commands operate terminals; agent commands
validate a recognized agent and its lifecycle. An agent start needs an available
shell pane and does not create layout.

Default background work to a sibling pane at the caller's cwd with `--no-focus`;
honor requested topology. Inspect geometry before choosing a split direction.
Do not close unrelated surfaces or stop the session server without explicit
authorization. Use an isolated named session for server experiments.

Inspect blocked agent UI before supplying input. Answer routine questions from
existing task context; leave approvals requiring the user's decision to them.
Verify task completion from the result, not lifecycle labels alone.
