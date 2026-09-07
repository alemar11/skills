# Context Preflight

Run this local preflight for every Learn invocation, before the
selected branch. It is derived run state, not a second `memory_slice`:

1. Resolve the actual root-to-target `AGENTS.md` chain. Repository-root
   `AGENTS.md` owns the root `CONTEXT.md` pointer. Each evidenced first-class
   subproject may own one additional managed block in its local `AGENTS.md`
   pointing to local `CONTEXT.md` while preserving root-first routing. Do not
   copy the same managed block into every file in the chain.
2. Read the root `CONTEXT.md` first when it exists, then follow its scoped
   routes and indexes as required by the selected operation. If it does not
   exist, distinguish an authorized setup that will create it from a missing
   surface that must be reported.
3. Inspect each applicable canonical `## Agent skills` / `### Domain memory`
   block and classify it as `current`, `missing`, `stale`, `duplicated`, or
   `not-applicable`. `stale` includes a missing root-first instruction, a
   missing evolution rule, stale paths, or copied conditional detail.
4. When an owning `CONTEXT.md` exists, or authorized setup will create it,
   check whether its managed pointer needs a change. For a missing, stale, or
   duplicated pointer, read the [pointer templates](setup-workflow.md#agentsmd-pointer-block)
   and draft the appropriate block. Reconcile it as a companion change only
   when the current request authorizes that context write; otherwise report
   the exact target and before/after block.
5. If the root context is absent and no authorized setup creates it, do not add
   a dangling pointer merely because `AGENTS.md` was inspected.

The preflight must also compare accepted project evolution against the context
surface. In an authorized context-bearing run, when the change affects shared
purpose, vocabulary, durable project rules, boundaries, stable routing, known
state, or explicit unknowns, update the root or matched scoped `CONTEXT.md`
surface and relevant indexes in the same run. For an unrelated selected slice,
report the candidate for `domain-memory` instead of widening the run.
Conditional detail belongs in an indexed topic file, accepted load-bearing
decisions belong in an indexed ADR, and agent operating rules remain in
`AGENTS.md`. Do not infer a context update from file churn alone; require
repository evidence or an accepted decision.
