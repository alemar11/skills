# Codex Model and Reasoning Index

This is the repository-wide inventory of skill-level Codex execution profiles.
Keep it synchronized with the linked runtime contracts; it is an index, not a
runtime policy source. Skills that only run in the current task without
selecting or delegating another Codex execution are omitted unless an explicit
composition boundary defines profile inheritance. A
`configured/default` value records intentional inheritance from the caller or
active runtime.

| skill | model | reason | description |
| --- | --- | --- | --- |
| [`$focus`](../skills/focus/SKILL.md) | `configured/default` | `configured/default` | Creates one focused Codex App task and intentionally omits `model` and `thinking`, so the caller's configured defaults apply. |
| [`$se:study`](../plugins/se/skills/study/SKILL.md) | `gpt-5.6-sol` | `medium` | Separate visible read-only Study controller on the App surface in the exact saved local project. |
| [`$se:study`](../plugins/se/skills/study/SKILL.md) | `configured/default` | `configured/default` | Current CLI session acting as the read-only Study controller; its active model and reasoning are intentionally retained. |
| [`$se:study`](../plugins/se/skills/study/SKILL.md), [`$se:spec`](../plugins/se/skills/spec/SKILL.md), [`$se:deliver-features`](../plugins/se/skills/deliver-features/SKILL.md) | `gpt-5.6-luna` | `max` | Shared [`evidence-researcher`](../plugins/se/references/subagents.md#evidence-researcher) role. Delivery also uses it for optional bounded [closeout analysis](../plugins/se/skills/deliver-features/references/closeout.md). Calling skills own selection, concurrency, lifecycle, and fallback. |
| [`$se:spec`](../plugins/se/skills/spec/SKILL.md) | Inherit | Inherit | The invoking session owns drafting and review with its configured model and reasoning; no separate planner. Optional helpers use the shared roles below. |
| [`$se:spec`](../plugins/se/skills/spec/SKILL.md) | `gpt-5.6-sol` | `xhigh` | Optional shared [`spec-reviewer`](../plugins/se/references/subagents.md#spec-reviewer) role for the complete draft and task plan; Spec owns review criteria and disposition. |
| [`$se:adversarial-review`](../plugins/se/skills/adversarial-review/SKILL.md) | `configured/default` | `configured/default` | Independent read-only reviewer profile supplied by the caller or composed workflow; the skill does not select a model or reasoning value. |
| [`$se:deliver`](../plugins/se/skills/deliver/SKILL.md) | `configured/default` | `configured/default` | Current-task orchestrator intentionally retains caller settings under its entrypoint. |
| [`$se:deliver`](../plugins/se/skills/deliver/SKILL.md) | `gpt-5.6-luna` | `max` | Local [worker contract](../plugins/se/skills/deliver/references/workers.md) owns App tasks and CLI subagents through publication and CI; explicit user overrides win. |
| [`$se:deliver-features`](../plugins/se/skills/deliver-features/SKILL.md) | `gpt-6-astra` | `configured/default` | Intended current-task coordinator, with caller-configured reasoning and explicit profile overrides under the skill's scope policy. The skill does not change task settings or create a replacement coordinator. |
| [`$se:deliver-features`](../plugins/se/skills/deliver-features/SKILL.md) | `gpt-5.6-luna` | `max` | Shared [`developer`](../plugins/se/references/subagents.md#developer) role: a run-scoped visible task in an isolated saved-project worktree on the App surface, or a native subagent in an isolated worktree on the CLI surface. The coordinator owns selection, publication phases and recovery. |
| [`$se:deliver-features`](../plugins/se/skills/deliver-features/SKILL.md) | `gpt-6-astra` | `medium` | Shared [`code-reviewer`](../plugins/se/references/subagents.md#code-reviewer) native subagent for an immutable candidate; the composing coordinator owns snapshot/receipt validation and the shared per-PR repair budget. |
| [`$se:implement`](../plugins/se/skills/implement/SKILL.md) | `configured/default` | `configured/default` | Executes in the current task or caller-selected developer subagent; does not select or change its profile. |

Remote Codex review requests or skills that merely execute in the current task
without owning a model/reasoning profile are not separate rows unless they gain
skill-level selection or delegation behavior.
