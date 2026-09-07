# SE

SE supports repository-grounded refinement, feature specifications, actionable
task plans, reviewed PR delivery, durable project knowledge, and read-only audits.

| Skill | Responsibility |
| --- | --- |
| `se:learn` | Maintain explicitly authorized local project knowledge and review rules. |
| `se:grilling` | Refine a topic through one focused question and recommendation at a time. |
| `se:study` | Refine a curated handoff, then conduct a read-only investigation. |
| `se:idea` | Save a tentative proposal to GitHub or preview it locally. |
| `se:spec` | Create or revise a coherent spec with an ordered actionable task plan; save to GitHub or one Markdown file. |
| `se:adversarial-review` | Independently pressure-test a fixed software change without editing it. |
| `se:deliver-features` | Deliver saved specs or selected tasks through reviewed ready PRs from the current task. |
| `se:implement` | Implement selected local work, validate it, and commit scoped files without publication. |
| `se:audit` | Observe an attributable frozen cohort of active SE work without changing it. |

Learn and Implement permit implicit selection within their descriptions. The
other entrypoints require explicit invocation or an authorized composed handoff.

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
and [revision/migration rules](skills/spec/references/existing-specs.md).

Spec uses one directly placed planner with its existing explicit profile and
stable-receipt startup. It asks only material questions through Grilling,
retains accepted technical decisions, distinguishes them from suggestions, and
reviews the whole spec/task bundle before saving. Its `steps/` own workflow
nodes; templates are output resources. Planning never writes implementation
progress or starts delivery implicitly.

## Delivery

Delivery consumes authoritative saved specs from GitHub or Markdown, selects
the whole spec by default or explicit tasks, and maps selected contributions
into repository-bound delivery units. Units choose useful
PR boundaries; they are not required to match task or spec counts. Delivery
verifies prerequisite availability, resolves fan-in integration, and uses
standalone or stacked PRs according to actual Git topology. It does not turn
planning order into artificial dependencies.

The current task coordinates native subagents using shared developer and
code-reviewer roles. Implementation lanes have isolated worktrees; the coordinator
alone holds repository claims. Each committed candidate passes independent local
review before publication, then a ready PR receives an explicit `@codex review`
request, including its first review. Both gates and required CI must pass for
the current HEAD. Two repair rounds apply per PR across local and hosted review.
Completion verifies selected task checks, assembled outcomes, PR linkage, progress
updates and exact whole-group release. Safe pauses also release once every actor
is stopped and work preserved; resume reacquires and reconciles existing work.
See [task delivery](skills/deliver-features/references/task-delivery.md) and
[completion](skills/deliver-features/references/completion.md).

PR delivery, merge, and issue closure are separate facts. A partial task PR
cannot close its parent spec. G receives exact justified closing references;
closure that needs multiple unmerged contributions remains an explicit
post-merge action. Delivery never merges, deploys, releases, or directly closes
implementation issues without separate authorization.

## Shared boundaries

- [Subagent roles](references/subagents.md) own reusable research and spec-review
  definitions. Study, Spec and Delivery select them while retaining their own delegation,
  lifecycle, fallback, and final decisions.
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
  bounded native subagents. Learn remains local-only. Audit remains read-only,
  reports partial inventory honestly, and distinguishes missing visibility from
  proven contract violations.

This source tree is the maintained SE design surface; installed caches are
verification surfaces, not editable source.
