# Study App Runtime

Read this reference only when `study_surface=app-task`. It owns App-specific
controller placement, task verification, and parent monitoring. Study creates
no additional visible worker tasks.

## Saved-project preflight

Resolve the invoking task's exact saved local project and owning host from
authoritative App state before requesting any Study task:

- Match the project by stable identity, exact local path, and host rather than
  by display label alone.
- Require the Study controller to run directly in that saved project on the
  same host, without an isolated checkout or worktree.
- If the invoking task is not attached to one exact saved local project, or
  the match is missing or ambiguous, stop before creation. Do not guess a
  project, create a projectless task, or switch to the CLI workflow.

## Separate Study controller

Create exactly one visible App task as the Study controller:

- Request `gpt-5.6-sol` with `medium` reasoning explicitly.
- Use the canonical requested title
  `🕵️ Study: <short title>` so the detective emoji is the first title element.
- Place it directly in the resolved project and local environment.
- Supply the complete curated handoff, the read-only boundary, the recursion
  prohibition, and the applicable Study protocol.
- Require its first substantive action to compose `$se:grilling-session` and ask the
  first interview question. Do not insert a setup-only turn before Grilling Session.

Treat an immediate creation response as a receipt, not proof of final task
state. Bind the controller only to a stable task identity. When the result is
uncertain, perform bounded authoritative reconciliation before any retry;
reuse an observed task and never infer identity from title, prompt preview, or
timing. A provisional setup identity is not a stable task identity and never
authorizes a duplicate.

After stable identity exists, independently establish the task's project,
host, direct local environment, operational state, and requested profile.
Observed profile drift is `settings-drift`; unavailable independent profile
evidence is `settings-unavailable`. Either fails App controller setup before
worker creation. Preserve a real task on failure and never replace it.

## Title handling

Task titles are visible metadata, never identity:

1. Request the canonical title at creation when supported.
2. Observe the stable task independently.
3. If the title is missing or different, make at most one title-correction
   request when that capability exists, then observe it once more.
4. Record `title-verified`, `title-unverified`, or `title-drift` with the
   evidence source.

A title warning does not block an otherwise verified controller unless the
user explicitly required an exact visible title. Never recreate a task or
perform repeated renames to repair title drift.

## Parent monitoring and Grilling Session

Keep the invoking parent active after controller creation and monitor the exact
controller through bounded observations. When its Grilling Session state is
`awaiting-answer`, point the user to the separate visible Study task. Do not
copy the question into the parent or relay interview answers turn by turn.

The controller must remain in Grilling Session until the handoff is `refined`, the
user stops with `user-stopped`, or the interview is `blocked`. It creates no
workers while awaiting an answer. Relay only meaningful milestones: the first
question is ready, Grilling Session finished or stopped, scope and worker count were
fixed, a material blocker appeared, the first worker finished, and synthesis
finished.

Do not interpret an idle task as terminal while it is waiting for the user's
next interview answer. The parent returns Study's final Markdown report in the
invoking session only after the separate controller produces a terminal
result.

## Subagent context

After Grilling Session is refined or stopped, apply the shared native-subagent contract
in [orchestration.md](orchestration.md). Every subagent remains under the stable
App controller lineage and uses its working-directory context. Subagents have
no App task title, saved-project placement, or archival fields. Keep the Study
controller unarchived as the one visible summary task.
