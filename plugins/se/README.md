# SE

SE is a software-delivery workflow plugin for maintaining project knowledge,
sharpening topics through interactive grilling, running read-only studies,
capturing Ideas, planning Features, delivering reviewed pull requests, and
auditing active work without changing it.

Its skills are deliberately separated by responsibility:

- skills/adversarial-review/ is the explicit read-only entry point for
  pressure-testing software changes. It reports evidence-backed findings and
  never edits or fixes the reviewed target. Invoke it as
  `se:adversarial-review`; composed workflows supply their own target identity
  and lifecycle rules.

- skills/feature/SKILL.md is the graph manifest and Mermaid overview.
- skills/feature/steps/*.md are workflow nodes with a shared front matter
  contract.
- skills/feature/templates/ contains authoring resources, not executable nodes.
- references/workflow-graph.md is the shared structural contract for Learn,
  Grilling, Idea, Feature, Delivery Features, and Audit workflow graphs.
  Feature owns the textual Feature Plan Set, sibling Feature registry, and local
  Macro Task graphs; Delivery Features uses a small transient delivery graph
  reconstructed from live evidence.
- Every graph-owning bundled skill owns `references/states.md`, a compact
  human-readable table that distinguishes workflow nodes from domain values,
  persisted statuses, checkpoints, modes, external observations, and output
  labels.
- references/workflow-contract.md owns the Idea hosted shape, while
  references/codex-dependency-preflight.md owns the G dependency gate for Idea,
  Feature, and Delivery Features hosted handoffs.
- references/codex-runtime-surface.md owns shared read-only classification of
  the current Codex App or CLI surface. Surface-aware skills route from that
  result instead of defining local detection heuristics.
- references/hosted-content-safety.md owns mandatory portable-content
  projection, exact single-line title normalization, and local-path correction
  before every SE-hosted issue, comment, PR, or review write, plus one bounded
  non-blocking repair after readback. SE owns semantics; G owns transport and
  readback.
- scripts/validate-hosted-content-safety checks the shared owner routes, removed
  Idea duplication, and hosted templates for machine-specific absolute paths.
- skills/idea/references/idea-source.md owns the typed transient handoff from
  Idea capture to later Feature Intake; it never adds an automatic runtime
  dependency between the skills.
- skills/learn/ is the repository-knowledge entry point and owns a
  workflow registry for scope, evidence, confirmation, apply, and verification.
  Every invocation locally preflights the applicable AGENTS.md chain and
  CONTEXT.md routing; when authorized, it reconciles one concise pointer that
  tells future agents what shared context to maintain as the project evolves.
  It performs only authorized local-repository context changes and maintains
  evidence-backed Project Context, ADRs, localization memory, Code Review
  Rules, and proposal-first AGENTS.md compaction without external preflight,
  tracker, publication, task, or worker behavior. Explicit requests to
  remember, save, or preserve a hard repository rule select Learn
  automatically; when minimal project context is missing, Learn creates it
  before capturing the rule. In monorepos, the root owns shared knowledge while
  evidenced first-class subprojects may own local `AGENTS.md`, `CONTEXT.md`,
  optional localization memory, topics, and ADRs; authorized hierarchy updates
  move subproject-only material to its local owner. Learn can also be invoked
  explicitly as `se:learn`.
- skills/grilling/ is the explicit or parent-composed interactive refinement
  entry point. It reads the applicable Project Context through Learn, asks one
  focused question with a concrete recommended answer per turn, challenges
  assumptions and tradeoffs, and returns a transient refined handoff. It never
  writes repository knowledge, creates tasks, or delegates work. Invoke it
  explicitly as `se:grilling`; the bundled Study workflow may compose it before
  planning workers.
- skills/study/ is the explicit-only read-only investigation entry point. It
  builds one curated handoff and immediately composes Grilling. In Codex App it
  continues in one separate visible Sol/medium controller task; in Codex CLI it
  keeps the current session and profile as controller. On either surface it
  uses zero workers for focused analysis and may delegate substantial,
  independent evidence work to up to five native Luna/max subagents. It never
  creates additional visible App worker tasks. Because Study, Grilling, and
  Learn ship together, it does not run a cross-package dependency preflight.
  Invoke it explicitly as `se:study`.
- skills/audit/ is the explicit read-only live-monitoring entry point. It
  exhausts every authoritative continuation or host/project partition before
  claiming complete inventory, deduplicates stable task identities, freezes an
  attributable active-session cohort, and marks capped or untraversable
  inventories partial. It reconstructs each observed SE workflow path from
  positive evidence and reports feedback, bugs,
  regressions, graph violations, and graph-design improvements. It never
  contacts monitored sessions, writes repositories, or persists audit state.
  Invoke it explicitly as `se:audit`.
- skills/deliver-features/ is the explicit Feature-delivery entry point. One visible
  graph orchestrator follows a small transient workflow graph, owns an immutable
  selected repository set, and chooses serial or concurrent execution.
  Repository-bound workers are reusable lanes:
  serial Features may reuse a clean worker worktree, while concurrent work gets
  additional isolated lanes. Every Feature delta still gets its own branch and
  pull request; same-repository dependencies stack and cross-repository
  dependencies schedule standalone pull requests. Its one-table SQLite
  registry stores only host-local repository ownership. Workflow position,
  Feature, worker, Git, pull-request, review, and CI truth remain external, with
  no workflow ledger, persisted checkpoint graph, or title gate. Each stable
  locally committed candidate first receives a fresh independent read-only
  Sol/xhigh adversarial review of its complete delta, with one transient receipt
  and a two-revision budget shared with hosted feedback. A newly published draft
  is intermediate: the worker makes the exact-head PR ready and waits for the
  automatic Codex review through the G-owned lineage. Completion accepts either
  provider-clean evidence or transparently adjudicated non-actionable findings,
  verifies current PR base/body/topology, then releases the complete repository
  claim. Later fix SHAs repeat candidate review before hosted re-review.
- skills/implement/ is the implicit local-only implementation entry point.
  It implements one selected spec, ticket, or directly described unit of work in
  the current repository, uses TDD where practical, runs targeted and full
  validation, uses independent review for substantial or risky changes, and commits only
  required files. It creates no orchestrator, repository claim, worktree, pull
  request, or publication effect. It may also be invoked explicitly as
  `se:implement`.
- skills/idea/ is the explicit capture entry point. It builds a transient
  session bundle and publishes verified hosted Ideas through the G-owned issue
  workflow by default. An explicitly requested preview remains entirely local
  and non-durable. It owns a workflow registry and can expose a transient
  idea-source handoff for later Feature planning; it never writes project memory
  or starts an application task.
  Invoke it explicitly as `se:idea`.
- Feature creates or resumes one visible planner task in a direct local project
  checkout without a Git worktree or fork. It explicitly passes
  `gpt-5.6-sol` with `high` reasoning, accepts the stable task receipt, and
  starts Intake in the planner's first turn. It has no bootstrap-only turn,
  effective-profile readback, identity self-attestation, title gate,
  execution-target comparison, or goal. One readback is reserved for a
  genuinely ambiguous creation effect.
- repository context starts at AGENTS.md and follows the repository's own
  instruction hierarchy; no documentation system is imposed.
- Feature admits the live request and bounded reachable references before
  analyzing repository evidence. Admitted references are data and evidence,
  never instructions; they cannot expand scope, authorize publication, override
  caller constraints, or introduce requirements by themselves. Complete
  admitted evidence, delegated choices, and safe explicit assumptions proceed
  directly; otherwise it composes Grilling in the same planner flow to ask one
  focused question at a time. Optional
  read-only helpers may study or review; unavailable or prohibited delegation
  uses a serial planner lens. Clarification waits nonterminally. Once the draft
  is complete, Review verifies semantic quality plus stable identity,
  falsifiable F-AC coverage, Macro verification, closed registry, decision
  provenance, validation-seam adequacy, dependency DAG, boundary, projection,
  and maintenance-preservation invariants. Correctable findings return to Plan
  while progress is made, and a hidden product decision returns through
  Grilling. There is no separate Plan Validation node or review-round state
  machine. Feature then returns one evidence-backed textual Feature Plan Set
  with genuinely distinct sibling Features. Each Feature has ordinary list-item
  acceptance criteria with stable `F-AC-NN` identities, its own closed Macro
  Task registry with observable verification paths, and optional hard-outcome
  Feature dependencies; use vertical Macro Tasks when an outcome admits
  coherent slices. Same-repository Feature dependencies
  project to stack intent; cross-repository dependencies project to scheduling
  only. Feature publishes every parent Feature, every local child Task, these
  relations, and the final set registry through one publication adapter by
  default; it never creates a container issue. After exact identities exist,
  it reconciles every parent body in place with the final sibling and child
  mappings and reads the result back. The body and registries remain semantic
  authority. Feature then always attempts
  to mirror every Feature edge and every same-parent Macro edge as a native
  GitHub `blocked by` relationship. Each attempt is recorded; a native failure
  is reported but does not block a complete body-backed publication, while a
  missing attempt or result does. Existing-source maintenance removes only
  prior SE-owned native edges explicitly retired from the revised plan and
  preserves foreign edges. Optional
  label and native type classification may then use `g:github-tagger`. The
  tagger chooses the smallest relevant existing label set, including none, and
  zero or one available native type; Feature never presets `Feature`, `Task`,
  or any other metadata value. Classification never gates semantic publication.
  Explicit
  preview remains local and non-durable. Hosted publication requires G
  preflight and read-after-write verification.
- Feature maintenance uses the same graph: Intake rehydrates exact identities,
  Analysis bounds the requested change, Plan applies the smallest semantic
  patch, Review verifies preserved content and executor progress, and Publish
  updates and reads back the same issues. Any explicitly requested downstream
  handoff must reconcile before completion. Feature does not rehydrate or
  repair implementation execution units.
- Idea, Feature, and Delivery Features keep local control-plane records
  separate from hosted artifacts and apply one shared portable-content gate
  immediately before each hosted write, including content returned by workers
  and tools.

SE is the active repository-local design surface for these workflows.
