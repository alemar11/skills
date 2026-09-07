# SE Plugin Maintenance

SE owns the graph-based planning and delivery workflows. Consult `CONTEXT.md`
for package context when relevant; keep shared repository rules at the root.
Do not restore retired compatibility surfaces.

## Shared ownership

A shared reference belongs in `references/` only when at least two skills
consume its contract. Each consumer routes to it at the relevant read condition.
Keep skill-specific states, topology, templates, and branch detail with the skill.
When ownership changes, update affected consumers and remove obsolete routes.

| Shared owner | Contract |
| --- | --- |
| `references/workflow-contract.md` | Idea hosted shape. |
| `references/workflow-graph.md` | Graph vocabulary, registry structure, terminal meanings, authority, and validation. |
| `references/codex-dependency-preflight.md` | Availability of required G workflows before hosted access. |
| `references/codex-runtime-surface.md` | Read-only App/CLI classification; capability checks are not surface evidence. |
| `references/hosted-content-safety.md` | Portable hosted content, title normalization, and bounded same-artifact repair. |
| `scripts/validate-hosted-content-safety` | Static ownership, routing, and hosted-template checks. |

## Skill ownership

- Learn owns local durable context, localization, review rules, and managed
  AGENTS pointers. It does not own tracker, task, or delivery state.
- Grilling owns read-only interview refinement and composes Learn for context.
- Study owns read-only study topology, its curated handoff, Grilling, worker cap,
  and synthesis. App/CLI details and worker operations live in its references.
- Idea owns tentative proposal capture, preview/publication, and the typed Idea
  source handoff. It does not define Feature requirements or durable memory.
- Feature owns Plan Set semantics, stable Feature/F-AC/Macro identities,
  dependencies, decision provenance, review, and hosted projections. Its
  `steps/` own node contracts; `templates/` are not workflow nodes.
- Adversarial Review owns independent read-only critique and generic findings;
  composed callers own target identity, lifecycle, and disposition mapping.
- Delivery Features owns selected-Feature scheduling, claims, workers, review
  gates, and verified standalone/stacked PR delivery. Candidate review mechanics
  live in `references/candidate-review.md`; its state meanings live in
  `references/states.md`. G owns hosted review transport and lifecycle.
- Implement owns selected local implementation without an orchestrator or claims.
- Audit owns frozen-cohort observation and evidence-calibrated conformance;
  it has no scripts, ledger, task profile, or persistent report.

## Maintenance invariants

Preserve these boundaries when changing their runtime owners; do not copy their
full protocols into this file:

- Feature plans express observable outcomes, falsifiable F-ACs, closed Macro
  registries, verification intent, and provenance. No implementation units,
  commands, worker scheduling, or executor-owned progress changes belong there.
- Same-repository Feature dependencies imply stack intent; cross-repository
  dependencies imply scheduling only. Macro dependencies stay within a parent.
  Native GitHub edges are diagnostic projections; bodies remain semantic
  authority. Preserve attempted-edge/result coverage and foreign provider edges.
- Material Feature questions compose Grilling in the planner. Safe assumptions
  and explicitly delegated decisions do not require extra interviews. Every
  complete draft passes Review, with progress-bounded correction.
- Keep Feature planner setup independent of Delivery Features claims and task
  verification. Preserve its accepted stable-receipt start and first-turn Intake;
  title metadata does not gate work. Model profiles remain in runtime owners
  and the repository model index, not duplicated here.
- Separate Delivery Features concurrency from PR topology. Overlapping writers
  never share a worktree. Parent drift invalidates dependent evidence.
- Preserve exact-base/full-HEAD candidate and hosted evidence, review-revision
  budgets, one-use recovery, and final whole-group claim release. Draft,
  blocked, and deferred results are not successful delivery.
- `repository-claims` owns only fenced ownership of the immutable repository set.
  Its schema/version constants are authoritative. Do not persist workflow,
  Feature, worker, Git, PR, review, or CI state there; add no TTL, heartbeat,
  force release, or stale-owner recovery. Only the bound orchestrator uses the
  token. Blocked/deferred runs retain claims until authorized release.
- Hosted writes pass the shared content-safety owner, including worker output.
  G owns transport/readback; SE owns semantic projection and correction.
- Graph node IDs and transitions stay synchronized across registries, step
  frontmatter, state glossaries, and Mermaid projections. Terminal nodes have
  no outgoing edges. Preserve bracketed `F-AC-NN` syntax as an explicit external
  rendering exception; criteria are not checkbox progress state.

## Validation

Validate affected metadata, links, state ownership, registry row arity,
registered transitions, terminal reachability, and graph projections. Do not
assert Markdown wording or section placement. Use bounded forward-model checks
when changed semantics cannot be established statically.

For hosted-content changes, run `scripts/validate-hosted-content-safety` and
inspect affected write owners. For executable claims or version alignment,
run `python3 -m unittest discover -s plugins/se -v` from the repository root;
`test_all.py` must discover the claims and alignment suites. Verify claims help,
version, and an absent-registry read-only doctor. Never use production claims
as test fixtures.

Check manifest/marketplace paths and scan for retired identifiers after routing
changes. Keep the repository-claims version and its version assertions aligned with
the plugin manifest in every versioned commit.
