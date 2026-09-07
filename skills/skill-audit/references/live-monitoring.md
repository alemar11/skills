# Live Skill and Plugin Monitoring

Use this branch only when the user asks to observe active Codex App tasks and
evaluate repository-owned skills or plugins while they run. This is a read-only
monitor, not an implementation controller or a session-archive scan.

## Required Runtime

Live monitoring requires Codex App task discovery and authoritative task reads.
Bounded waits are optional accelerators. If discovery or reads are unavailable,
report `evidence_state=current-evidence-unavailable` and stop the live claim.
Do not replace current evidence with memory, session JSONL, task age, or silence.

Use [states.md](states.md) for canonical annotation status, severity, target
kind, fix-surface, evidence, and transition values. App task lifecycle state is
external and must be reported exactly as authoritatively observed.

## Select Tasks

1. Prefer task IDs or titles explicitly named by the user.
2. For an unnamed request to monitor current active tasks, discover recent App
   tasks and keep only tasks that are currently active and contain direct
   evidence of using a skill or plugin owned by the current repository.
3. Exclude the current audit task, other monitoring tasks, unrelated hosts or
   repositories, and tasks that only expose the skill catalog.
4. If more than eight tasks qualify, monitor explicit targets first and process
   the remaining tasks in declared batches.

Task status and repository path are selection evidence, not proof of skill or
plugin use.

## Attribute Runtime Use

Confirm use from one or more of these task-visible signals:

- an explicit user invocation or linked `SKILL.md` path
- an agent statement that it is using the surface plus a corresponding contract
  read or workflow action
- a call to a target-owned shipped script
- a bundled-skill or plugin-owned tool call that maps to the owning manifest

Catalog injection, tool discovery, a passing mention, cached installation, or a
repository path alone is not runtime use. Resolve plugin-owned behavior through
the workspace manifest and bundled-skill paths; use installed cache copies only
to explain packaging drift.

## Establish the Contract Baseline

Before judging behavior:

1. Resolve the repository-owned target and its kind.
2. Read the target entrypoint, directly required references, metadata, and
   owning plugin manifest when applicable.
3. Record the runtime path visible in the task and the repository source path.
4. Record a content fingerprint for every contract file used in the judgment.
5. If runtime and repository copies differ, evaluate the task against the
   runtime copy and annotate the drift separately. Do not blame behavior on a
   contract the task did not receive.

## Observe Without Interference

1. Perform an initial authoritative task read. Read enough earlier turns to
   establish invocation, scope, and the first relevant action.
2. Track each task by stable identity, host, status, and the last observed
   evidence.
3. When bounded waits are available, use supported batches and bounded intervals. Treat compact wait summaries as advisory.
4. Perform a fresh authoritative task read after a material transition, before
   creating or changing a defect annotation, after a cursor or evidence gap,
   and before a terminal judgment.
5. If bounded waits are unavailable, use bounded task reads. If reads fail,
   time out, or are truncated across the relevant evidence, report the gap; do
   not infer progress or defects.
6. Treat a request for user attention as a material nonterminal transition. Report it and
   continue after the task resumes. Stop only after every selected task has an
   authoritative terminal result or the user stops the monitor.

Emit updates only for material transitions, new or changed annotations. Silence and elapsed time are not performance evidence.

## Evaluate Behavior

Compare observed behavior with the exact active contract. Keep these lanes
separate:

- selection and trigger correctness
- workflow order and required contract loading
- scope, authority, and mutation safety
- tool and plugin routing
- evidence and validation quality
- recovery and terminal behavior
- instruction clarity or avoidable prompt/runtime cost

Do not classify App/tool availability, model behavior, user input, repository
state, or another surface's failure as a target defect unless the target owns
the missing guardrail or recovery behavior. Record strong behavior as well as
failures so the result measures performance rather than only incident count.

## Defect Annotations

Assign stable IDs in first-seen order: `LIVE-001`, `LIVE-002`, and so on. Keep
one annotation per root cause and update it instead of duplicating it.

Each annotation contains:

- `id`
- canonical `status` and `severity` from `states.md`
- canonical `evidence_state` from `states.md`
- target name and kind
- canonical target kind and owning fix surface from `states.md`
- concise defect statement and impact
- expected contract file, fingerprint, and relevant section
- observed task identity, evidence location, and summary
- first-seen and last-seen task frontier
- confidence and the smallest useful remediation

Apply the meanings and only the transitions defined in `states.md`. Evidence
unavailability is a monitor limitation, not a defect.

After every material annotation change and before terminal assessment, emit the
complete canonical annotation registry in the audit task. Do not persist it to
the repository, user-state files, monitored tasks, or external systems.

## Mutation Boundary

Do not call task messaging, task creation, title, pin, archive, Goal, Git,
GitHub, or repository-write tools from this branch. If the user wants a defect
fixed or posted elsewhere, finish or stop the monitor and switch to the owning
implementation or publication workflow with explicit authority.
