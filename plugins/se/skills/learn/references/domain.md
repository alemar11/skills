<!-- SE-owned reference derived from the durable repository-context contract. -->

# Context Domain And Routing

Use this reference to discover and route durable project context in a Git
repository. Root `CONTEXT.md` is the shared entry point. An evidenced
first-class monorepo subproject may own a local context tree; flat topic files
and ADRs are loaded only when their scope or `Read when` condition applies.

## Discovery Order

1. Read repository-root `CONTEXT.md` when it exists.
2. Follow every non-overlapping matching row in its `## Scoped Contexts` table.
   A matched row without a context file is still a routing fact; inspect its
   owned paths directly without inventing vocabulary or a dangling pointer.
3. For each matching first-class subproject, read the applicable root-to-target
   `AGENTS.md` chain and its local `CONTEXT.md` when present.
4. Read relevant indexed `project-context/<topic>.md` files first from the root
   for shared context, then from the selected subproject for local context.
5. Read `TRANSLATION.md` beside each selected context when localization memory
   exists and is material.
6. Read the applicable `project-context/adr/index.md`, then relevant ADRs;
   cross-project decisions resolve at root and subproject-only decisions resolve
   in the local context tree.

The current Git repository is the default selected root. Explicit user scope or
a validated Feature spec may authorize additional repository
identities, but a composed caller must supply candidate local Git roots and
verify each root against exactly one identity. Reject extra or unmatched roots.
Never fabricate a path from a hosted ref, saved project, common parent, or path
proximity.

## Context-Owning Scopes

The Git repository root always owns shared Project Context. A directory inside
a monorepo is a first-class subproject context owner only when durable evidence
shows a stable product, service, application, deployment, documentation, build,
or ownership boundary. Workspace membership alone may identify a candidate but
does not require one tree per small library package. Incidental directories
never own Project Context.

Each context-owning scope may have exactly one `AGENTS.md`, `CONTEXT.md`,
optional `TRANSLATION.md`, and `project-context/`. The local
`project-context/` is created only when at least one local topic or accepted ADR
needs it. A subproject tree remains inside the selected Git repository and does
not become a separate repository identity.

## Repository Layout

Single repository:

```text
/
├── AGENTS.md
├── CONTEXT.md
├── TRANSLATION.md                 # optional
└── project-context/
    ├── adr/
    │   ├── index.md
    │   └── ADR-0001-descriptive-name.md
    ├── backend-api.md
    └── worker-runtime.md
```

Monorepo:

```text
/
├── AGENTS.md
├── CONTEXT.md                     # shared context and scope routing
├── TRANSLATION.md                 # optional shared localization
├── project-context/               # shared topics and cross-project ADRs
│   ├── adr/
│   └── shared-runtime.md
└── apps/
    ├── accounting/
    │   ├── AGENTS.md              # local always-active rules and pointer
    │   ├── CONTEXT.md             # scope-specific entry point and delta
    │   ├── TRANSLATION.md         # optional local localization rules
    │   └── project-context/       # local topics and accepted local ADRs
    │       ├── adr/
    │       └── ledger-workflow.md
    └── support/
        ├── AGENTS.md
        └── CONTEXT.md
```

Repository-wide topic files live under root `project-context/`. Subproject-only
topic files live under that subproject's `project-context/`. Keep each topic
folder flat; `adr/` is its only initial subdirectory.

## Root Routing Table

Use this table only when internal scopes are meaningful:

```markdown
## Scoped Contexts

| Scope | Owned paths | Context |
| --- | --- | --- |
| Accounting | `apps/accounting/`, `packages/ledger/` | `apps/accounting/CONTEXT.md` |
| Support | `apps/support/` | — |
```

Rows must have one stable scope name and non-overlapping owned paths. Select
every matching row. Ask the owner to resolve overlap before persisting a table.
Every created local `CONTEXT.md` must have one corresponding root routing row.

## Ownership

Root `CONTEXT.md` owns shared purpose, vocabulary, cross-scope boundaries,
routing, the shared topic index, root ADR index pointer, and explicit unknowns.
A subproject `CONTEXT.md` owns only its local purpose delta, vocabulary,
boundaries, unknowns, topic index, and ADR pointer, and links back to the root.

Root `AGENTS.md` owns repository-wide always-active rules. A subproject
`AGENTS.md` owns only additional or overriding rules for its paths, points to
the local `CONTEXT.md`, and preserves the root-first instruction chain.

Topic files own conditional detail, examples, rationale, domain contracts, and
operational notes for their context owner. `AGENTS.md` owns only always-active
rules and short pointers. `TRANSLATION.md` owns localization rules beside the
context it serves. Root ADRs own cross-project decisions; local ADRs own
accepted subproject-only decisions.

Do not duplicate the same normative rule across these surfaces. If a topic or
ADR contradicts an existing `AGENTS.md` rule or ADR, stop and surface the
conflict.

## Bootstrap And Closeout

Authorized setup/bootstrap creates or updates root `CONTEXT.md` at every
selected Git root, even when evidence supports only a minimal entry point with
explicit unknowns. During explicit monorepo setup or hierarchy update,
repository evidence may establish first-class subproject boundaries and is
enough to create minimal local `AGENTS.md` and `CONTEXT.md` routing surfaces.
Rich vocabulary, rules, topics, ADRs, and localization files still require
strong evidence or explicit accepted decisions.

## Monorepo Rebalancing

An authorized setup, refresh, or hierarchy update may reorganize an existing
flat context layout. Classify every affected item before moving it:

- keep cross-project rules, vocabulary, topics, and decisions at the root;
- move subproject-only always-active rules to the closest local `AGENTS.md`;
- move subproject-only context, topics, ADRs, and localization guidance into
  that subproject's local tree;
- update root routing, topic/ADR indexes, backlinks, and relative links in the
  same change; and
- remove the old copy only after the new owner is verified, leaving no
  duplicated normative guidance.

Do not split content whose ownership crosses subprojects, create local trees for
incidental folders, or guess through overlapping scope boundaries.

For existing projects, load `domain-modeling.md` before writing. For an
implementation closeout, reconcile each accepted durable decision against
landed behavior and update only the named context, topic, project document, or
ADR surfaces.

Never record tentative proposals, rejected ideas, secrets, raw session logs, or
generic architecture advice as durable context.
