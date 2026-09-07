<!-- SE-owned reference derived from the durable repository-context contract. -->

# Domain Memory Modeling

Use this internal reference whenever `memory_slice=domain-memory` creates,
updates, reviews, or reconciles `CONTEXT.md`, relevant domain docs, or ADRs.
`$se:learn domain-memory` is the public invocation; this reference owns
the internal semantic workflow.

## Goal

Keep a project's shared language and durable decisions current. Turn accepted
terminology, boundaries, rules, and decisions into lightweight documentation
that future agents and maintainers can reuse. Do not invent a domain model
before there is evidence from the user, repository, or existing docs.

## Operation Boundary

Honor the `domain_operation` option resolved by `$se:learn`. Use its
evidence-derived `execution_context`; never accept that classification as a
caller-selected option:

- `execution_context=fresh-setup`: create the smallest evidence-backed initial context surface.
- `execution_context=existing-project-bootstrap`: reconcile accepted knowledge from current repo
  evidence and, when explicitly loaded, strong recent same-repo history.
- `domain_operation=inline-update`: capture durable decisions accepted during a
  direct composed decision-shaping workflow.
- `domain_operation=implementation-closeout`: reconcile a carried knowledge delta against the
  behavior and validation that actually landed.
- `domain_operation=periodic-review`: report or propose changes by default; write only when the
  evidence and acceptance satisfy Project Context's authority boundary.

Stay within the selected context, authorized target surfaces, and evidence
boundary. Do not expand into localization, pointer, or unrelated domain
surfaces.

When a caller supplies a `knowledge_delta`, treat it as input data: accepted
terms, rules, boundaries, or decisions plus evidence and intended targets.
Reconcile it against the current repository before capture. Do not reduce it to
an enum or treat its presence as write authority.

For a repository-owned shard of a cross-repository delta, require every target
to remain inside the current Git root. A cross-repository decision additionally
names one `canonical_decision_target` in the exact
`<feature-id>--<repository-key>/<repo-relative-path>` form. Resolve that prefix
to the explicitly selected owning member of the caller's validated Feature
Spec Set and require the remainder to fit the owner's accepted paths. Only that
owner writes the full record; another repository may capture a repo-local
context change and a backlink that copies the exact target. Reject a shard that
duplicates the canonical record, targets a peer root, or leaves canonical
ownership ambiguous.

## Workflow

### 1. Inspect existing context

- Resolve the selected Git root and read its root `CONTEXT.md` first when it
  exists. During authorized setup/bootstrap, create or update it at every
  selected Git root, even when evidence supports
  only a minimal entry point with explicit unknowns. Outside setup/bootstrap,
  use repository evidence and create it only with authorized durable content.
  Explicit user scope or a durable Feature spec authorizes
  repository identities. A composed cross-repository caller supplies candidate
  local Git roots separately, verifies each root against one authorized
  identity, and runs this workflow independently in each verified repository.
  Also inspect the relevant root and local `project-context/adr/` trees,
  `README.md`, project docs, product specs, issue
  templates, and nearby source or tests that define the vocabulary already in
  use.
- When a selected repository's root `CONTEXT.md` contains
  `## Scoped Contexts`, select every non-overlapping row matched by the
  affected paths or accepted product identities, then read each available
  subproject `CONTEXT.md` and applicable `AGENTS.md`. The repository root
  remains applicable after selection.
  For a matched row without a context file,
  inspect its owned paths directly and create the scoped file only when
  authorized evidence supports durable scope-specific content.
- Stop and ask only when scoped routes overlap or ownership remains
  indeterminate. Do not guess, and do not mistake legitimate cross-scope work
  for routing ambiguity.
- During explicit monorepo setup or hierarchy update, identify evidenced
  first-class subprojects using stable product, service, application,
  deployment, documentation, build, or ownership boundaries. Create or update
  a minimal local `AGENTS.md` and `CONTEXT.md` for each selected first-class
  subproject even when richer local knowledge is sparse. Do not create a local
  tree for every workspace package or incidental directory.
- Prefer updating an existing relevant file over creating a new one.
- During authorized setup/bootstrap, ensure root `CONTEXT.md` exists before
  completion even when no durable term or rule is yet established. Outside
  setup/bootstrap, create it when an authorized durable term or rule needs a
  home. For a verified monorepo, create the minimal root routing surface before
  creating any subproject context.
- If no suitable authorized destination exists, defer capture and name the
  missing file or surface explicitly.

### 2. Sharpen the model

Track only durable items:

- **Terms**: project-specific words, aliases, and nearby concepts that differ.
- **Boundaries**: where a concept, workflow, actor, or module stops and another
  starts.
- **Rules**: invariants, permissions, lifecycle transitions, validations, and
  failure states.
- **Decisions**: accepted choices future work should not relitigate.
- **Open questions**: unresolved points that must remain visibly uncertain.

Challenge fuzzy terms with concrete edge cases before recording them. When two
names appear synonymous, resolve whether they are aliases or distinct concepts.

### 3. Update the smallest durable surface

- Add or revise shared glossary entries, routing, and explicit unknowns in root
  `CONTEXT.md`; put only scope-specific deltas in the selected subproject
  `CONTEXT.md`.
- Add conditional workflow or behavioral detail to the owning root or
  subproject's flat `project-context/<topic>.md` file with a title, scope,
  `Read when` condition, and owner/update logic, then add or update that owner's
  `CONTEXT.md` index row.
- Keep `CONTEXT.md` as the entry point and index; do not duplicate the topic
  file's full body there.
- Add an ADR beneath root `project-context/adr/` for a cross-project decision or
  beneath the selected subproject's `project-context/adr/` for a local decision,
  only when the accepted load-bearing decision would otherwise be reopened.
  Create or update the owning `project-context/adr/index.md` in the same change.
- During an authorized hierarchy update, move existing subproject-only material
  from root surfaces into the local owner. Update root routes, indexes,
  backlinks, and relative links; remove the old copy only after verifying the
  new owner, and never duplicate normative guidance.
- Leave unresolved questions explicit rather than smoothing them over.
- Use project vocabulary and link durable repo sources such as source files,
  tests, schemas, project docs, or ADRs when available.
- Treat issues, PRs, discussion threads, and session history as discovery
  evidence or optional provenance, not as the sole authority for durable
  context. Restate accepted meaning in a repo-owned source and cite that source.

Use `references/documentation-shapes.md` only when the project does not already
have a stronger local format.

### 4. Handle periodic review

When invoked by an automation or batch workflow:

- Treat conversations, session logs, issue activity, and commit history as
  candidate evidence, not authority by themselves.
- Re-read current context and relevant repo evidence before accepting a
  candidate.
- Default to a review report or proposed patch when acceptance is unclear.
- Do not create an ADR from batch review alone unless the decision is clearly
  accepted and load-bearing.
- Keep candidates whose destination is missing or evidence is weak under a
  concise `Deferred Candidates` result.

Use this closeout shape when useful:

```markdown
## Accepted Updates

- Durable item captured now, with destination.

## Deferred Candidates

- Candidate still needing acceptance, evidence, or a destination.

## ADR-worthy Decisions

- Accepted load-bearing decision that may deserve an ADR.

## No Durable Change

- Use when nothing warrants capture.
```

Omit empty sections unless `No Durable Change` is the only correct result.

### 5. Return the capture result

Return to `$se:learn`:

- docs created or updated,
- terms, rules, boundaries, or decisions captured,
- evidence used,
- candidates or capture deferred and why,
- unresolved domain questions,
- ADR-worthy decisions,
- the derived `capture_outcome` result (`captured`, `deferred`, or
  `no-durable-change`) plus separate destination or deferral data,
- documentation-diff verification for
  `domain_operation=implementation-closeout`.

For a nonempty implementation-closeout delta, account for every accepted item
and every required named target. Return `capture_outcome=captured` only when all
are reconciled, each destination is updated or verified already current, and
the complete documentation diff is verified. If any item, target, evidence, or
destination remains unresolved, return `capture_outcome=deferred` with the
specific destination and reason; `no-durable-change` cannot complete that
closeout. If landed behavior rejects or contradicts a supplied accepted item,
do not silently reinterpret the delta: return `deferred` and require an owner
decision or a separately authorized planning/implementation correction.

## Guardrails

- Do not record transient preferences, tentative ideas, rejected proposals,
  secrets, raw logs, or weak inferences.
- Do not create ADRs for small preferences.
- Do not remove existing domain notes unless the user explicitly invalidates
  them or durable repo evidence proves them stale.
- Do not ask questions answerable from the repository.
- Do not rewrite broad docs to add one narrow term.
- Do not make runtime skills depend on repo-maintenance documentation.
