<!-- SE-owned reference derived from the durable repository-context contract. -->

# Initial CONTEXT.md Seed

Use this reference when `project-context` bootstraps a Git repository. It
controls how much evidence-backed content to add; it does not
decide whether root `CONTEXT.md` exists.

## Mandatory root entry point

Authorized setup/bootstrap always creates or updates root `CONTEXT.md` at every
selected Git root in the setup scope. When durable repository evidence
is sparse, create a minimal entry point and make the missing knowledge explicit
without inventing project facts. For example:

```markdown
# Context

Project Context entry point for this repository.

## Open Questions

- Project purpose, shared vocabulary, and durable boundaries are not yet
  established.
```

During explicit monorepo setup, verified first-class subproject boundaries are
enough to create minimal local `AGENTS.md` and `CONTEXT.md` routing surfaces.
Rich local content remains evidence-gated. Every additional Git repository
explicitly selected by a composed setup follows the same mandatory root-context
rule; repositories outside that scope remain untouched.

## Evidence threshold

Seed domain content only when at least one durable repository source supports
it:

- README, vision docs, architecture docs, product docs, or component docs
- AGENTS.md rules that describe accepted repo behavior
- package manifests, schemas, tests, source directories, or public APIs
- accepted user decisions and committed repo behavior

Issues, PRs, Feature specs, discussion threads, and final session summaries may help
discover candidate knowledge, but they are not durable repo authority by
themselves. Before citing a candidate in `CONTEXT.md`, capture or verify it in a
repo-owned document, ADR, source file, schema, or test. Source links may remain
as optional provenance in that durable source.

Do not seed from guesses, tentative plans, rejected options, secrets, raw logs,
or generic architecture advice.

When `AGENTS.md` is a source, capture only durable project context or accepted
repo behavior. Leave agent operating rules in `AGENTS.md` and keep feature
metadata contracts with their consuming feature workflows.

For a detected monorepo, verified repository structure is enough evidence for
stable scope routing in the mandatory root `CONTEXT.md`. During explicit full
setup or hierarchy update, stable first-class subproject boundaries also
support minimal local `AGENTS.md` and `CONTEXT.md` files. Structure alone is not
evidence for richer vocabulary, behavioral rules, local topics, ADRs, or
translation guidance. Routing tables may use `—` when a candidate scope is not
yet established as a first-class context owner.

## Seed shape

Load and follow `references/domain-modeling.md` before writing. Use the root or
scoped shape in `references/documentation-shapes.md`, and use routing tables
only from `references/domain.md`. Keep the initial seed short and include only
sections that have evidence.

When a neighboring `TRANSLATION.md` exists and localization affects domain
terms, audience, product naming, or user-facing copy, `CONTEXT.md` may include
a one-line pointer such as `Localization: see TRANSLATION.md`. Do not require
this pointer and do not create broken links.

Use concise bullets. Link or name source files when that helps future agents
verify the statement, for example `README.md`, `VISION.md`, `docs/...`,
`agents/README.md`, `be/docs/openapi.yaml`, or a specific source/test path.

## What to capture

- Project purpose and explicit non-goals.
- Product areas, subprojects, services, packages, or ownership boundaries.
- Stable scoped-context routing proved by repository structure.
- Canonical names and terms future Feature specs/issues should reuse.
- Durable rules that affect implementation, validation, promotion, or docs.
- Open questions only when current evidence clearly leaves a decision
  unresolved or conflicting.

## What to avoid

- Full architecture inventories or file trees.
- Subproject context files that merely repeat the root context.
- Repeating command lists already owned by AGENTS.md or README files.
- Copying agent operating instructions that should remain in `AGENTS.md`.
- Recording translation or localization rules that belong in `TRANSLATION.md`.
- Long research notes that belong in project docs.
- ADR-level decisions unless the user explicitly asks to record accepted
  decisions and the evidence is load-bearing.
