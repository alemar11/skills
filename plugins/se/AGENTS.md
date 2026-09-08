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
| `references/states.md` | Shared spec-delivery readiness states, GitHub label colors, authorization and verified human handoff. |
| `references/workflow-graph.md` | Graph vocabulary, registry structure, terminal meanings, authority, and validation. |
| `references/codex-dependency-preflight.md` | Availability of required G workflows before hosted access. |
| `references/codex-runtime-surface.md` | Read-only App/CLI classification; capability checks are not surface evidence. |
| `references/review-repair-budget.md` | Delivery/Implement per-PR repair budget across local/hosted gates, reservations and recovery. |
| `references/execution-scope.md` | Uniform standalone/composed responsibilities and delegation policies across SE skills. |
| `references/subagents.md` | Reusable research, development and review roles with default profiles; callers own transport, orchestration and disposition. |
| `references/hosted-content-safety.md` | Portable hosted content, title normalization, and bounded same-artifact repair. |
| `scripts/validate-hosted-content-safety` | Static ownership, routing, and hosted-template checks. |

## Skill ownership

- Deliver owns the lightweight worker-to-PR workflow and its local worker role,
  optional integration and recovery references. It has no graph, claim registry,
  mandatory review gate or repair ledger. Deliver Features-specific invariants
  below remain scoped to that existing skill. Preserve both invocation contracts.

- Learn owns local durable context, localization, review rules, and managed
  AGENTS pointers. It does not own tracker, task, or delivery state.
- Grilling Session owns read-only interview refinement and composes Learn for context.
- Study owns read-only study topology, its curated handoff, Grilling Session, worker cap,
  and synthesis. App/CLI details and worker operations live in its references.
- Spec owns coherent specs, stable spec/F-AC/task identities, actionable
  task contracts, recommended order, real prerequisites, accepted decisions,
  review, and GitHub/single-file Markdown projections. Its specification
  reference owns content, and templates project it. Its delivery-authorization
  reference owns the post-save authorization decision; shared readiness states
  own metadata and Deliver owns the human handoff, not queue execution.
- Adversarial Review owns independent read-only critique and generic findings;
  composed callers own target identity, lifecycle, and disposition mapping.
- Delivery Features owns selected-spec/task scheduling, integration and acceptance,
  surface-specific developer transport, native research/review subagents, claims,
  budget reservations, progress, and reviewed PR delivery.
  Its closeout owns run measurements and generalized workflow improvement reports.
  It composes Implement, Adversarial Review and Review PR; it does not duplicate
  their procedures. Delivery owns candidate lifecycle, finding adjudication and
  hosted acceptance; its state meanings remain in its own `references/states.md`.
- Review PR requests or resumes one hosted Codex review, waits, and returns the
  provider result to the calling task. It owns no subagents, repairs, CI or
  acceptance. G owns provider operations, lineage and bounded waiting.
- Implement owns bounded local implementation/repairs and candidate handoff;
  composed callers own independent review, orchestration, claims and publication.

## Maintenance invariants

Preserve these boundaries when changing their runtime owners; do not copy their
full protocols into this file:

- Feature specs preserve observable outcomes, accepted technical decisions,
  relevant baseline evidence, paired task verification checks, and full coverage. Task
  order is independent of identity and hard prerequisites. Planning never
  overwrites executor progress or prescribes workers and PR topology.
- One outcome may span repositories. Delivery maps task contributions into
  repository-bound units, verifies actual prerequisite availability and assembled
  outcomes, and owns PR grouping, stack/integration choices, and closing refs.
- GitHub and Markdown preserve one spec/task contract and one authoritative
  destination. Exports are explicit snapshots. Native edges are projections;
  preserve body-backed meaning, per-edge results, and foreign provider edges.
- Material spec questions compose Grilling Session in the planner. Safe assumptions
  and explicitly delegated decisions do not require extra interviews. Every
  complete draft passes Review, with progress-bounded correction.
- Spec runs in the invoking session and updates its title when supported.
  Title availability does not gate planning. Model profiles remain in runtime
  owners and the repository model index.
- Separate Delivery Features concurrency from PR topology. Overlapping writers
  never share a worktree. Parent drift invalidates dependent evidence.
- For Deliver Features, preserve exact-base/full-HEAD candidate and hosted evidence, review-revision
  budgets, reconciled recovery, and final whole-group claim release. Draft,
  blocked, and deferred results are not successful delivery.
- `repository-claims` owns only fenced ownership of the immutable repository set.
  Its schema/version constants are authoritative. Do not persist workflow,
  Feature, worker, Git, PR, review, or CI state there; add no TTL, heartbeat,
  force release, or stale-owner recovery. Only the bound orchestrator uses the
  token. Safe pauses preserve work and release after verified quiescence; only
  unresolved actor, preservation, or release safety retains ownership/uncertainty.
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
