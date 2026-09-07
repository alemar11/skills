# Codex CLI Invocation

Run from the skill root or use the resolved absolute artifact path:

```sh
scripts/codex-cli --help
scripts/codex-cli --model sol --task-profile standard --prompt-file /path/task.md
```

Model aliases, task profiles, reasoning compatibility, and defaults belong to
[model policy](model-policy.md). Pass the resolved selection to the launcher.
An explicit reasoning override without a task profile reports a null profile;
do not label it as a model-default classification.

| Option | Purpose |
| --- | --- |
| `--prompt`, `--prompt-file`, stdin | Complete caller-owned prompt. |
| `--cd` | Working directory; defaults to the current directory. |
| `--sandbox` | Delegated access boundary; see [states](states.md). |
| `--output-schema` | JSON Schema for the delegated final answer. |
| `--output` | Explicit launcher-owned destination for a successful nonempty answer. |
| `--dry-run` | Resolve invocation without launching. |
| `--json` | Machine-readable result; progress stays on stderr. |

For custom reviews, supply the complete review prompt, target evidence, and any
output schema. The launcher owns transport, not finding semantics or a fix loop.

Doctor is intended to be read-only, but underlying Codex startup can attempt
host-level maintenance. Inspect reported stderr when availability is unclear.
Successful runs report model selection, effective reasoning, task profile,
sandbox, prompt size, exit status, and final answer. Remote model availability
is established by execution, not local resolution.
