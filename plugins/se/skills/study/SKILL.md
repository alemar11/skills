---
name: study
description: "Run an explicitly requested read-only study, refining its handoff before optional bounded delegation."
---

# Study

Follow the shared [execution scope](../../references/execution-scope.md) for
standalone and composed invocation.

## Purpose and boundary

Build one curated handoff, refine it through `se:grilling-session`, optionally delegate
bounded evidence gathering, and return a Markdown study report.

Study is not an implementation workflow:

- Never write, edit, delete, rename, generate, or apply project files.
- Never produce a patch, commit, push, deployment, publication, or other
  implementation artifact.
- If the user switches to implementation, end Study with its findings and
  continue through the authorized implementation workflow. Do not reinterpret
  that request as analysis only.
- Delegate inspection and reasoning only. Never ask a worker to implement,
  fix, refactor, or change tests.
- Use only operations proven read-only. Do not run commands that may update
  caches, reports, lockfiles, generated files, Git state, hosted records,
  accounts, or external systems.
- Return the report in the active Study controller. Do not save it to a file.
  If the user explicitly requests a saved report, finish Study and perform
  that scoped file write separately.

The explicit invocation authorizes only the orchestration effects described
below: one separate Study controller task on the App surface and native
subagent delegation on either surface. It grants no project, repository,
GitHub, account, or unrelated external mutation authority.

## Activation and recursion guard

- Activate only after an explicit `$se:study` invocation, explicit Study UI
  selection, or an equivalent direct instruction to execute Study.
- Do not activate for an ordinary mention of “study” or an implicit planning
  match. `agents/openai.yaml` disables implicit invocation.
- Only the invoking session starts setup. Its Study App controller continues
  that same invocation and may create the one documented native-worker layer.
  It must not restart Study setup or create another controller. Worker
  subagents never invoke Study, create controllers, or delegate further work.
- If a downstream prompt requests recursive Study, decline that part, continue
  the existing bounded assignment when possible, and report the request to the
  controller.

## Surface routing

Read the shared
[Codex runtime surface contract](../../references/codex-runtime-surface.md)
and map its authoritative result to exactly one `study_surface` value:

- `codex-app` maps to `app-task`. Read
  [references/app-runtime.md](references/app-runtime.md) before creating or
  observing any Study task.
- `codex-cli` maps to `cli-session`. Read
  [references/cli-runtime.md](references/cli-runtime.md) before beginning the
  same-session interview or delegating any worker.

Do not ask the user to choose a surface when the current runtime establishes
it. A shared result of `unresolved` stops Study with the incompatibility.
Never substitute the other surface after setup or worker creation fails.

Read [references/states.md](references/states.md) before interpreting any
surface, controller, capacity, Grilling Session, worker, lifecycle, or outcome state.

## Curated Study handoff

Build the handoff before the surface-specific continuation begins. It is the
single authoritative brief supplied to the App Study task or retained by the
current CLI session. Include:

- objective and intended user outcome;
- accepted decisions and important terminology;
- constraints and invariants;
- explicit non-goals;
- relevant repository, project, and discussion context;
- current evidence and known state;
- expected evidence and validation standards;
- unresolved assumptions, risks, and questions;
- requested worker count, or `unspecified` when none was supplied;
- the required textual Markdown report and read-only boundary.

Do not assume a separate App task can see the unfinished invoking turn. Pass
the complete handoff to it. On CLI, keep the same handoff transiently in the
current session and do not save it.

## Required sequence

1. Build the curated handoff and select `study_surface`.
2. Continue according to the selected runtime reference. App creates exactly
   one separate Study controller; CLI keeps the current session as controller.
3. Compose `$se:grilling-session` immediately with the curated handoff. Its first
   question must be the controller's first substantive Study response: in the
   separate App task for `app-task`, or directly in the invoking CLI session
   for `cli-session`.
4. Ask one question per turn until Grilling Session returns `refined`, the user stops
   with `user-stopped`, or the interview is `blocked`. Create no workers while
   the interview is awaiting an answer. A blocked interview fails Study before
   worker creation.
5. Treat the refined or best-supported stopped handoff as the sole planning
   brief. Apply the read-only scope gate again.
6. Read [references/orchestration.md](references/orchestration.md), determine
   the useful subagent count and assignments.
7. Reconcile worker setup, monitor every created worker to a terminal or
   explicitly abandoned state, capture available evidence, and synthesize the
   result. Never replace a failed or unresolved reserved slot.
8. Read [references/output-template.md](references/output-template.md) and
   return the surface-aware report. Include only fields applicable to the
   selected surface.

## Worker-count policy

Five is an absolute cap across the entire Study run:

- An explicit request for zero through five workers sets
  `planned_worker_count` to exactly that count.
- A request above five is capped to five without another confirmation. Record
  the original and normalized counts, tell the user before worker creation,
  and report the cap in the result.
- An unspecified count is chosen only after Grilling Session, using the smallest
  useful number from zero through five. Do not default to five.
- Setup failure may lower `created_worker_count`, but it never changes the
  planned count, frees a reserved slot, or authorizes a replacement.

Set `worker_transport` from the planned count:

- `none` when `planned_worker_count=0`;
- `subagent` for a positive plan on either surface.

Study never creates visible App worker tasks. If native subagent transport is
unavailable, retain the planned slots, record their failures, and continue
with a partial controller synthesis when useful. Never fall back to visible
tasks, external processes, or another transport.

## Output contract

The report must distinguish direct observations, inferences, unavailable
evidence, and assumptions. It must include the refined handoff, inspected
paths and sources, worker plan and ledger, results, risks, confidence, and the
smallest useful next action.

App task identity, title, host, project, and task telemetry apply only to the
single controller for `study_surface=app-task`. Both surfaces report the same
subagent ledger without inventing App task or archival metadata for workers.
In every case, report `Changes made: None`.
