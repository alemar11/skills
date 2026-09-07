# Herdr States

Herdr owns these external lifecycle labels; the skill does not persist them.
Read command output and agent text together before claiming completion.

| State | Meaning |
| --- | --- |
| `idle` | Ready for input; the tab has been seen. |
| `done` | Idle after unseen background work finishes. |
| `working` | Herdr detects active agent work. |
| `blocked` | Herdr detects an approval or question UI. |
| `unknown` | An agent is present but cannot be classified confidently. |

Focusing marks a tab seen; CLI reads do not. Lifecycle waits track the current
agent state, not a specific prompt's completion.

`agent_not_ready` retains the agent name after blocked startup;
`agent_blocked` rejects a prompt before input is sent;
`agent_prompt_stalled` means no lifecycle change was observed within five
seconds. These are external command errors, not task outcomes.
