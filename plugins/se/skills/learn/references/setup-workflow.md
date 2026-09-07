<!-- SE-owned reference derived from the durable repository-context contract. -->

# Setup Workflow Details

Use this reference for the interactive setup editor, draft checklist, write
rules, `AGENTS.md` pointer block, and completion report. Keep the public
`SKILL.md` focused on routing and hard boundaries.

When a composed caller selects multiple Git repositories, run setup
independently in each selected repository. Never create shared coordination
memory at their common parent.

## Current Settings Summary

When reviewing existing setup, summarize values in the selected setup slice
before recommending changes. Include the full list only for an explicit full
review:

- execution context: `fresh-setup`, `existing-project-bootstrap`, or
  `current-project` (derived in the exact
  precedence from `options.md`, not a stored key or option)
- root/subproject context routing and context owners
- translation memory decision
- `AGENTS.md` setup block state, including its owner, read-first pointer,
  evolution guidance, and duplicate/over-copy status
- Code Review Rules section state when that slice is selected

Use `Unknown` only when a value is absent or ambiguous. If the user only asked
to view current settings, stop after the summary.

Reject runtime-only worker configuration in project-context setup files; those
fields belong to Delivery Features planning contracts.

## Settings Editor

When the requested section is unclear, use the setup-target question in
[setup-questions.md](setup-questions.md). Otherwise edit only the named or
required section and preserve unrelated custom prose, path
conventions and dry-run overrides
unless the user explicitly changes them.

Editable sections:

- `domain-memory`
- `durable-capture`
- `translation-memory`
- `agents-pointers`
- `agents-compaction`
- `code-review-rules`
- `done`

For each selected setup section, show the current value first, then
`keep-current` and the relevant alternatives:

- `domain-memory`: show the current root `CONTEXT.md`, first-class subproject
  context owners, indexed topic files, scoped routes, and applicable root or
  local ADR roots. Refresh those
  surfaces from evidence; during authorized setup/bootstrap, always create or
  update root `CONTEXT.md` at every selected Git root in the setup
  scope. Do not present or persist a domain-layout enum.
- `translation-memory`: `enabled`, `not-applicable`, `needs-confirmation`.
- `agents-pointers`: create a missing canonical pointer block, refresh stale or
  over-copied evolution guidance, or remove duplicate managed pointer blocks
  while preserving unrelated instructions.
- `code-review-rules`: inspect, propose, or update the exact Code Review Rules
  section in the closest applicable `AGENTS.md`.
- `durable-capture`: show the candidate, scope, exact destination, and wording
  when a material ambiguity requires confirmation; an unambiguous explicit
  save/remember/preserve request supplies direct scoped authority.
- `agents-compaction`: show the applicable chain measurement and before/after
  proposal; never apply a compaction from threshold detection alone.

After edits, show intended changed files and before/after settings. An explicit
request to set up, configure, initialize, update, or refresh project context is
write authority for that scope, so proceed without a second confirmation. For
review-only, recommendation, dry-run, or indirectly suggested setup, return the
report without writing.

Ask only about a materially ambiguous target or behavior-affecting value that
repo evidence and the defaults below cannot resolve. Do not force the user
through unrelated editable sections. If ambiguity remains, load
[setup-questions.md](setup-questions.md) and use its applicable first-time-user
prompt.

## Invocation Preflight

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
   draft the appropriate root or subproject block below. If a block is missing
   or stale and the current run already authorizes the relevant local context
   write, reconcile it as a companion change. Otherwise report the exact target
   and before/after block.
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

## Setup-First Durable Capture

For an explicit request to remember, save, or preserve a specific repository
rule, inspect setup before capture. Learn is minimally ready when the selected
Git root has root `CONTEXT.md` and the selected context-owning scope has an
applicable canonical Project Context pointer whose target and evolution
guidance are current. A first-class subproject rule also requires its local
`CONTEXT.md` and local pointer.

When either surface is absent or stale, treat minimal setup as a prerequisite,
not as a separate user-selected slice or `full-setup`. Under direct scoped
capture authority, create or repair only the minimal evidence-backed root
context chain and canonical pointers, then write the rule to the closest
applicable `AGENTS.md`. Do not create empty topic files, ADR trees, translation
sidecars, or unrelated subproject contexts. If the rule, repository scope,
destination, wording, or a conflict is materially ambiguous, draft setup and
capture together and wait for confirmation; after approval, apply and verify
setup before capture.

## Decision Defaults

- Do not define durable worker assignments, worker-count limits, or scheduled
  checks in project context.
- Read root `CONTEXT.md` first when it exists. During authorized domain
  setup/bootstrap, always create or update it at every Git root selected by the
  setup scope. Populate only evidence-backed purpose,
  vocabulary, rules, boundaries, and routing. When richer evidence is absent,
  keep a minimal entry point and state the missing knowledge explicitly rather
  than inventing it.
- For a verified monorepo, use repository evidence for root scope routing.
  During explicit full setup or hierarchy update, create minimal local
  `AGENTS.md` and `CONTEXT.md` surfaces for every evidenced first-class
  subproject in scope. Create local topics, ADRs, and translation files only
  when durable evidence and authority support their content. Every additional
  Git repository explicitly selected by a composed setup follows the mandatory
  root-context rule; repositories outside that scope remain untouched.
- Recommend enabled translation memory only when localization support and
  durable translation rules are confirmed by evidence or the user.

## Draft Checklist

Before writing, show only applicable items from this list:

- current settings summary for review mode;
- before/after summary for proposed changes;
- intended `AGENTS.md` pointer block;
- intended exact `## Code Review Rules` block, target instruction chain, and
  candidate evaluation when that slice is selected;
- `AGENTS.md` minimization plan;
- durable-capture target, exact wording, and confirmation state when selected;
- AGENTS chain measurement and section classification when compaction is selected;
- intended root `CONTEXT.md` creation or update, including evidence-backed
  content, stable routing, and any explicit unknowns;
- intended subproject `AGENTS.md` and `CONTEXT.md` owners, or why root-only
  routing is sufficient;
- existing root material to keep shared or move into a subproject, with index
  and link updates;
- intended `TRANSLATION.md`, or why localization memory should not be written;
- intended ADR drafts, if any.

## Write Rules

For an explicit setup or update request:

- Update only files needed for the selected memory surfaces.
- Create or update the canonical `AGENTS.md` pointer block when the root
  context exists or is being created, and apply only authorized minimization of
  managed duplicate/copying. Include this companion target in the draft and
  completion report.
- When `code-review-rules` is selected, update the closest applicable
  `AGENTS.md` with the exact `## Code Review Rules` section. Keep the persisted
  block limited to accepted invariant, consequence, and safe path; preserve
  unrelated instructions and keep evidence, evaluation matrices, and
  provenance in the run report or Project Context references.
- Create or update root and subproject `CONTEXT.md` through
  `references/domain-modeling.md`. During authorized setup/bootstrap, ensure
  root `CONTEXT.md` exists at every selected Git root in the setup scope before
  writing any subproject context or completing setup. During
  authorized full monorepo setup or hierarchy update, also create or update the
  local `AGENTS.md` and `CONTEXT.md` for every evidenced first-class subproject
  in scope.
- Create or update `TRANSLATION.md` only when localization memory is confirmed.
- Create ADRs only for accepted, load-bearing decisions.
- For durable capture, write after an explicit save/remember/preserve request
  supplies unambiguous scoped authority, after the user confirms the exact
  target and wording, or when a composed caller supplies accepted knowledge,
  named targets, and inline capture authority. Apply required minimal setup
  before the capture write.
- For compaction, keep mandatory rules in `AGENTS.md`, create flat topic files
  under explicit compaction authority, and update the `CONTEXT.md` index in
  the same change.
- Preserve unrelated or uncertain content in `AGENTS.md`, `CONTEXT.md`,
  `TRANSLATION.md`, ADRs, and project docs.
- Move subproject-only material to its local owner during an authorized
  hierarchy update, update root routes and indexes, verify the new target, and
  only then remove the old copy.
- Do not duplicate moved project context in root and local `AGENTS.md`,
  `CONTEXT.md`, or `project-context/` targets.

## AGENTS.md Pointer Block

Use this shape as the managed block. Include only sections whose target
surface exists, is derived at runtime, or is authorized in the selected slice;
preserve unrelated custom prose outside the block. Omit `Localization` unless
`TRANSLATION.md` exists or is authorized; never create a broken pointer:

```markdown
## Agent skills

### Domain memory

`CONTEXT.md` is the shared-context entry point. Read it first, then follow its
`Scoped Contexts` table when relevant. When the project evolves, update only
evidence-backed shared purpose, vocabulary, durable project rules, boundaries,
known state, explicit unknowns, scope routing, and topic/ADR indexes; route
conditional detail to indexed `project-context/` topics and accepted
load-bearing decisions to indexed ADRs. Keep always-active agent rules in
`AGENTS.md`; exclude tentative plans, secrets, and raw logs.

### Localization

[one-line summary of supported localization memory]. See `<path-to-TRANSLATION.md>`.
```

For a first-class subproject's local `AGENTS.md`, use this local variant and
resolve `<relative-root-context>` from the subproject directory:

```markdown
## Agent skills

### Domain memory

Read the repository-root [`CONTEXT.md`](<relative-root-context>) first, then
this subproject's `CONTEXT.md`. Maintain shared purpose, vocabulary, rules,
boundaries, routing, and cross-project decisions at the repository root;
maintain only subproject-specific deltas, local topics, and local ADRs here.
Keep always-active subproject rules in this `AGENTS.md`; exclude tentative
plans, secrets, raw logs, and duplicated root guidance.
```

Keep each block concise and manage only its `Domain memory` entry. Do not paste
project vocabulary, workflow procedures, implementation policy, localization
rules, worker-dispatch rules, context seed material, or conditional topic
content into `AGENTS.md`. Each block is a compact pointer/evolution projection;
the full capture contract remains in the routed Learn references. The invoking
implementation workflow owns its session worker questions, checkpoint,
dispatch, and ledger progress record.

The `## Code Review Rules` section is a separate exact review contract, not a
project-context pointer. Manage it only when the `code-review-rules` slice is
selected; do not fold its evaluation detail into this pointer block.

## Completion Report

Summarize only the applicable fields:

- execution context;
- files written;
- capture outcome and confirmation state when durable capture was selected;
- AGENTS chain files, byte totals, threshold classification, and moved sections
  when compaction was selected;
- settings reviewed and changed;
- root/subproject context routing and context owners;
- root material kept shared and subproject-only material moved, including
  updated indexes and links;
- localization-memory decision and evidence;
- `AGENTS.md` minimization outcome;
- `AGENTS.md` Project Context pointer owner and state, including whether the
  evolution rule was current, updated, or deferred;
- Code Review Rules target, rule count, evaluation state, history coverage, and
  result when selected;
- session-history window and whether it was used;
- root-context creation or update, evidence-backed terms/rules/routing, and
  explicit unknowns;
- `TRANSLATION.md` audience, locale, terminology, or open questions seeded;
- ADRs created or updated;
- workflows that can now consume setup.

## Standard Ambiguity Questions

Normally ask no questions. After repository evidence and the defaults above
leave a material ambiguity, load
[setup-questions.md](setup-questions.md) and use exactly one applicable
evidence-first template. Its canonical question set covers setup target,
  separate project contexts, overlapping project ownership, repository-rule
  ownership, and localization conventions.

Keep Project Context internals out of user-facing prompts. Ask about concrete
projects, repositories, paths, rules, and localization behavior, then
translate the answer to canonical configuration internally. Never ask the user
whether evidence is sufficient, combine two unresolved decisions in one
question, or ask a question already resolved by an explicit request, durable
repository evidence, or a documented default.
