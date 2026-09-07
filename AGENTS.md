# Repository Guidelines

Reusable skills live in `skills/`, maintainer skills in `.agents/skills/`,
plugins in `plugins/`, and MCP helpers in `mcps/`. Each skill has `SKILL.md`;
each plugin has `.codex-plugin/plugin.json`.

For cross-package purpose or ownership, consult `CONTEXT.md` and its relevant
scoped context. Read the nearest package `AGENTS.md` before maintaining that
package. A narrow edit does not require a repository-wide documentation pass.

## Instruction design

- User instructions take precedence over skill guidelines. Preserve established
  authorization and complete the requested work; ask only for a material
  unresolved decision or an action outside that authorization.
- If a skill causes a pause or departure from the request, link the exact file,
  quote the responsible instruction, and distinguish its requirement from your
  interpretation. Continue unaffected authorized work.
- Keep instructions that change decisions: selection boundaries, non-obvious
  constraints, ownership, and completion criteria. Remove generic coaching,
  duplicated rules, and fixed itineraries without a correctness reason.
- Keep descriptions short and selective. Put shared constraints and conditional
  routing in `SKILL.md`; put branch-specific procedures in one linked reference
  with a read condition. Do not repeat deferred content or add a router to a
  self-contained skill.
- Prefer concise prose and proportionate outputs; require a format only when
  the consumer needs it. Stop verification when relevant checks pass unless
  new evidence justifies more work.

## Identity and contracts

- Use lower-kebab-case for directories, public identifiers, slugs, and assigned
  enum values; use `snake_case` for machine-readable fields. Preserve
  externally owned syntax such as Git refs, URLs, environment variables, and
  provider names. Document compatibility exceptions at the owning contract.
- Prefer explicit or path-derived identities over display titles. Use one
  canonical spelling; do not add aliases for retired identifiers.
- Give field registries, templates, protocols, and result shapes one owner.
  Link to it rather than duplicating its definitions.
- Skills with workflow states must route to `references/states.md`, defining
  their namespace, meanings, transitions, and persisted versus transient or
  external state. Update it with behavioral changes; do not invent a state
  machine merely to describe an ordinary sequence of work.
- Separate configuration from caller inputs, execution facts, and derived
  results. Observing a value does not make it a persisted option.
- Keep skill-owned model and reasoning roles indexed in
  [codex-model-index.md](references/codex-model-index.md), one row per profile,
  including intentional default inheritance. Update affected rows with the
  runtime owner; the index must not duplicate its policy.
- Use lowercase Markdown filenames under `references/`, except `README.md`
  and `AGENTS.md`.

## Codex integration

Describe runtime interactions with Codex by outcome, authorization, execution
location, lifecycle, verification, and recovery. Runtime skills and references
must not encode Codex tool names, API signatures, payloads, or response schemas.
Use the live interface for mechanics. Report an unavailable required capability
without claiming success or substituting a different outcome.

Distinguish requested state, creation receipts, and independently observed
state. Titles are metadata, not identity. Reconcile uncertain effects before
retrying a mutation.

## Skill maintenance

- Use skill-creator for new skills or substantial reshapes. Follow the
  [Agent Skills specification](https://agentskills.io/specification) and
  [Codex skill reference](https://developers.openai.com/codex/skills/).
- Discoverable skills need `agents/openai.yaml`. Keep it, README entries,
  installation prompts, and actual dependencies aligned with public behavior.
  Preserve invocation policy unless its change is requested. Include a Skill
  Dependencies section only for real runtime dependencies.
- After adding a reusable skill, run `./skills-link.sh` and verify its
  `~/.agents/skills/<name>` link. This helper links only `skills/`; it does not
  install maintainer skills or change plugin marketplaces.
- Remove retired source, metadata, catalog/install entries, registries, and
  repository-owned installation links together, then scan for stale references.
- Choose an unused repository color when adding `brand_color`.
- Keep `skills/plugins-reload/SKILL.md` aligned with the local marketplace's
  plugin set and supported installation workflow.

## Plugin maintenance

- Use plugin-creator for new plugins or substantial reshapes. The manifest owns
  identity, version, assets, and bundled-skill exposure; keep paths valid from
  the plugin root.
- Register additions, renames, and removals in
  `.agents/plugins/marketplace.json`; align README and marketplace descriptions.
- Place bundled skills in `skills/<skill>/`, shared artifacts in `scripts/`,
  and maintenance source in `projects/<tool>/` under the plugin root.
- Every committed plugin change requires a semantic version update. Align an
  embedded CLI's version unless the package documents independent versioning.
- Installed caches are verification surfaces, never editable source.

## Knowledge and maintenance boundaries

Keep `AGENTS.md` focused on maintenance ownership and durable repository rules;
keep invocation behavior in skills. Add package-local guidance only for rules
not inferable from its tree, manifest, or runtime contract. Put distinct build
or artifact rules nearest their owner and remove redundant local guidance.

Update `CONTEXT.md` only for evidence-backed shared purpose, vocabulary,
boundaries, known state, unknowns, and routing. Put conditional detail in
indexed `project-context/` topics and accepted decisions in indexed ADRs.
Exclude tentative plans, secrets, and raw logs.

Runtime skills must not route to maintainer-only skills or perform incidental
self-upgrade, metadata synchronization, or reference refresh. A skill whose
explicit purpose is maintenance may perform the requested maintenance. Keep
maintenance implementations outside shipped runtime artifacts and install lists.

## Validation and delivery

Validate changed discovery metadata, reference paths, and representative usage
contracts. Do not add Markdown-only tests. For executable changes, use affected
behavioral tests and verify the shipped artifact. Use forward model tests only
when static checks cannot establish the changed behavior.

Scope rebuildable caches to `~/.cache/dotagents/skills/<skill>/` or
`~/.cache/dotagents/plugins/<plugin>/`; bundled-skill caches belong under the
plugin's `skills/<skill>/` subdirectory. Do not store user configuration there.

Preserve unrelated work. When commits are requested, separate responsibilities
across skills or plugins. Run `git diff --check` before handoff.
