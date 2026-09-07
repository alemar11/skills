# SE

SE supports repository-grounded refinement, feature specifications, actionable
task plans, reviewed PR delivery with workflow retrospectives, and durable project knowledge.

| Skill | Responsibility |
| --- | --- |
| `se:learn` | Maintain explicitly authorized local project knowledge and review rules. |
| `se:grilling-session` | Refine a topic through one focused question and recommendation at a time. |
| `se:study` | Refine a curated handoff, then conduct a read-only investigation. |
| `se:idea` | Save a tentative proposal to GitHub or preview it locally. |
| `se:spec` | Create or revise a coherent spec with an ordered actionable task plan; save to GitHub or one Markdown file. |
| `se:adversarial-review` | Independently pressure-test a fixed software change without editing it. |
| `se:review-pr` | Request or resume a hosted Codex PR review, wait, and report the provider result to the calling task. |
| `se:deliver` | Orchestrate isolated workers for specs, issues or bounded work through validated ready PRs. |
| `se:deliver-features` | Deliver saved specs or selected tasks through reviewed ready PRs from the current task. |
| `se:implement` | Implement selected local work, validate it, and commit scoped files without publication. |
| `se:deslop` | Explicit-only audit and minimal safe cleanup of low-value code across every major directory. |

Learn, Implement and Review PR permit implicit selection within their descriptions. The
other entrypoints require explicit invocation or an authorized composed handoff.
Deslop requires explicit user invocation.

## Feature specifications

One main spec describes a coherent outcome, accepted decisions, acceptance
criteria, and tasks. An outcome may span repositories. Tasks have stable IDs,
scoped outcomes, completion checks, validation, and real prerequisites. Their
recommended sequence does not imply dependencies or Git stacks.

Spec saves new specs to GitHub by default: one parent spec issue plus
associated task issues. An explicit Markdown save writes one complete file
containing the spec and every task. Preview writes neither destination. Existing
specs retain their authority; an explicit export creates a labeled snapshot.
See the canonical [specification contract](skills/spec/references/specification.md)
and [revision and export rules](skills/spec/references/existing-specs.md).

Spec runs in the current session with its configured model and reasoning and
updates the task title to `📚 Plan Feature · <outcome>` when supported. It asks
only material questions through Grilling Session and reviews the complete
spec/task contract before saving. Planning preserves execution progress and
does not start delivery implicitly.

The templates use a compact ordered task list; each task owns its repository
scope, acceptance links, prerequisites, and paired verification checks. GitHub
stores task bodies in child issues; Markdown nests them in the same file.

## Deliver

[`se:deliver`](skills/deliver/SKILL.md) accepts saved specs, selected issues, or
bounded requests. The current task orchestrates workers with isolated worktrees
and branches: visible App tasks or native CLI subagents. Each worker owns
implementation, self-checks, publication and required CI in one assignment.
The orchestrator owns scope, dependencies, optional stacks and assembled outcomes.
Explicit or implicit invocation authorizes the scoped worker tasks without a
separate task-creation permission prompt, subject to explicit user restrictions.

Delivery finishes with all required PRs non-draft, current required CI passing,
and selected outcomes verified. Merge and deployment are separate. There are no
mandatory adversarial/hosted reviews, claims, repair-round ledgers or audits;
repository/user requirements still apply. Source-progress writes are opt-in.
Worker setup/recovery and integration details are loaded only when applicable.
The skill has no automatic cross-session ownership exclusion.

## Deliver Features

Delivery consumes authoritative saved specs from GitHub or Markdown, selects
the whole spec by default or explicit tasks, and maps selected contributions
into repository-bound delivery units. Units choose useful
PR boundaries; they are not required to match task or spec counts. Delivery
verifies prerequisite availability, resolves fan-in integration, and uses
standalone or stacked PRs according to actual Git topology. It does not turn
planning order into artificial dependencies.

The intended coordinator is the current Astra task with caller-configured
reasoning; the skill preserves task settings and explicit profile overrides.
In the Codex App it creates run-scoped visible developer tasks in exact saved
repository projects and isolated worktrees; in the CLI developers remain native
subagents. App workers may be reused within that delivery run, remain visible
after completion, and are never adopted by later runs. The user communicates
only with the coordinator. Research and review roles remain native subagents.
It composes Implement for initial work and repairs, Adversarial
Review for local critique, and Review PR for hosted monitoring. Implementation
lanes have isolated worktrees; the coordinator
alone holds repository claims. Each committed candidate passes independent local
review before publication, then a ready PR receives an explicit `@codex review`
request, including its first review. Both gates and required CI must pass for
the current HEAD. Two repair rounds apply per PR across local and hosted review.
Completion verifies selected task checks, assembled outcomes, PR linkage, progress
updates and exact whole-group release. Safe pauses also release once every actor
is stopped and work preserved; resume reacquires and reconciles existing work.
See [task delivery](skills/deliver-features/references/task-delivery.md) and
[completion](skills/deliver-features/references/completion.md).

Local review has a [bounded attempt deadline](skills/deliver-features/references/candidate-review.md#attempt-deadline).
Before dependent work, Delivery checks supported managed PR topology; rebasing
keeps changed candidates local until validation and independent review pass.
Compound stack synchronization cannot bypass that publication boundary.

Every run ends with a [closeout](skills/deliver-features/references/closeout.md),
including blocked or stopped work. It reports delivered outcomes, duration and
available token usage with explicit coverage, then audits what worked, failed,
or could improve in Delivery and its invoked skills. Recommendations must
generalize across projects and remain proposals. The coordinator may use one
bounded research helper when useful; safe claim release precedes analysis.

PR delivery, merge, and issue closure are separate facts. A partial task PR
cannot close its parent spec. G receives exact justified closing references;
closure that needs multiple unmerged contributions remains an explicit
post-merge action. Delivery never merges, deploys, releases, or directly closes
implementation issues without separate authorization.

## Standalone PR review

Review PR obtains the hosted Codex review result for a ready PR's exact HEAD:
reuse a completed result, resume a matching pending request, or request and wait
when review is missing. It preserves the original 30-minute deadline and returns
pending on timeout. Explicit audit-only inspection remains read-only. Standalone
and composed calls have the same scope and run in the calling task with no
subagents, spec or local checkout. Clean and findings both complete monitoring;
the caller decides any repair, rebuttal or acceptance. G owns request transport,
lineage, bounded waits and terminal evidence.

## Shared boundaries

- [Execution scope](references/execution-scope.md) preserves the same subagent
  policy standalone and composed. Implement and Adversarial Review execute work;
  an orchestrator may assign them to agents but they never launch their own.

- [Execution roles](references/subagents.md) own reusable research, development and review
  definitions. Study, Spec and Delivery select them while retaining their own delegation,
  lifecycle, fallback, and final decisions.
- [Repair budget](references/review-repair-budget.md) is shared by Delivery and
  Implement. Delivery owns [candidate review](skills/deliver-features/references/candidate-review.md),
  review evidence admissibility and hosted finding adjudication.
- G owns GitHub transport, issue lifecycle, review lineage, CI, and stack
  operations. SE runs its dependency preflight before the required handoff;
  it never installs or substitutes G. Local-source Spec Markdown work has
  no G dependency.
- The [hosted-content contract](references/hosted-content-safety.md) owns portable
  paths, titles, and bounded readback repair. SE owns semantic projection;
  G owns transport and provider readback.
- [Workflow graphs](references/workflow-graph.md) and each skill's state reference
  distinguish transient workflow position from saved content and external facts.
- [Delivery progress](skills/deliver-features/references/progress.md) updates task
  status and PR links in the original destination without changing semantic
  requirements. Markdown progress remains local and uncommitted by default.
- Repository claims store ownership only. No spec/task progress, worker state,
  Git/PR state, review evidence, or workflow node belongs in that registry.
- Study keeps its separate App controller or current CLI session and optional
  bounded native subagents. Delivery alone selects App-visible or CLI-native
  developer transport under its runtime contract. Learn remains local-only.

This source tree is the maintained SE design surface; installed caches are
verification surfaces, not editable source.
