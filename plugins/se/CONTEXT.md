# SE Context

Repository context: [`../../CONTEXT.md`](../../CONTEXT.md)

Scope: `plugins/se/`

## Project Purpose Delta

SE is the repository's graph-first software-delivery plugin. Its bundled Learn,
Grilling Session, Study, Idea, Spec, Adversarial Review, Review PR, Delivery Features,
Deliver, Deslop, and Implement skills have distinct runtime contracts, while `AGENTS.md`
and `README.md` define package maintenance ownership and routing.

Spec owns one coherent spec and actionable task plan, saved to GitHub or one
Markdown file. Deliver Features owns task-to-PR grouping and integration, with task
prerequisites independent of Git topology. The Spec content contract is at
[`specification.md`](skills/spec/references/specification.md).
Spec also owns the [delivery authorization](skills/spec/references/delivery-authorization.md)
marker and post-save pickup decision. Authorization is separate from semantic
revision and execution progress; exports remain inactive snapshots. No monitor
is started by publishing or marking a spec.

Study, Spec and Deliver Features share subordinate role definitions in
[`subagents.md`](references/subagents.md). Their callers own delegation and
lifecycle. Deliver Features is designed for an Astra coordinator in the current task,
retaining caller-configured reasoning and profile overrides. App delivery uses
run-scoped visible developer tasks in exact saved-project worktrees; CLI delivery
uses native developer subagents. Research and review remain native subagents.
It publishes ready PRs after
local and explicitly requested hosted review, and releases claims on verified
safe pauses. Deliver Features owns progress separately from semantic spec content.

Deliver Features composes Implement for bounded local work and Review PR for hosted
review request/monitoring. Standalone and composed Review PR use the calling
task with no subagents and report the provider result without repairs, CI or
acceptance decisions. Deliver Features owns candidate review, finding adjudication,
selected-spec verification and progress; its budget is shared with Implement.
Every Deliver Features invocation ends with a [closeout](skills/deliver-features/references/closeout.md)
covering results, available duration/usage evidence and generalizable workflow
improvements. The coordinator owns this audit and does not apply its proposals.

[Deliver](skills/deliver/SKILL.md) is a separate worker-to-PR workflow for specs,
issues and bounded requests. Its current-task delivery lead is designed for Astra,
retaining configured reasoning and explicit profile overrides. It
owns its worker role locally, avoiding Deliver Features' phase/review contract.
Workers complete implementation through required CI, or hand validated commits
to an assigned integration worker for a shared PR. Integration is a regular worker
assignment that combines contributions and verifies the assembled behavior; the
orchestrator verifies selected outcomes and integration. Compatible serial work,
including stacked branches, reuses workers/worktrees; concurrent assignments use
separate workers/worktrees. Deliver returns bounded results and resume context;
backlog monitoring and queue persistence belong to its caller. Claims, mandatory
reviews, source-progress writes and retrospectives are not part of its default
path. Deliver Features remains unchanged and independently invokable.
