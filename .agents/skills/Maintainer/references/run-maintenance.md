# Run Maintenance Playbook

Use this playbook for the repo-wide pass of the unified `maintain skills`
task, including bare maintainer imperatives such as `run`, `run your tasks`,
or other default maintenance requests.

## Purpose
- Keep one or more existing skills or plugins healthy with proactive, low-ambiguity improvements.
- Treat `run` as the default entrypoint for this maintainer skill.
- Apply concrete maintenance work automatically when the rationale is clear.

## Task Boundary
- If the user does not name targets, inspect all local skills and repo-local plugins in the repository.
- `run` may update multiple skills or plugins when each change has a concrete rationale and low ambiguity.
- Auto-apply only safe maintenance items such as:
  - metadata and docs alignment
  - clearer triggers, workflow, guardrails, examples, or references navigation
  - stale path or wording fixes
  - Codex-dependency labeling and optional-tool fallback clarity
  - directly coupled `README.md` or `AGENTS.md` wording drift
- Do not infer domain `refresh` or brand-new skill creation from bare `run`.
- If a candidate change is strategic, high-ambiguity, or likely to alter intent, report it as follow-up instead of auto-applying it here.

## Workflow
1. Enumerate local packages and directly coupled repo docs:
   - reusable skills under `skills/*`
   - repo-local plugins under `plugins/*`
   - project-local maintainer skills under `.agents/skills/*`
   - related `README.md` and `AGENTS.md` entries
2. Inspect for actionable drift and shortlist the packages with clear, maintainable improvements.
   - Include stale Codex-dependency inventory or ambiguous Codex-tool wording in this inspection.
3. For each shortlisted target, apply a targeted upgrade using the rules from `skill-upgrade.md`.
4. Run `metadata-sync.md` for the touched skills, plugins, and coupled repo docs.
5. Run the relevant checks from `doc-consistency.md` across touched areas and repo-level reference drift.
6. Finish with `release-checklist.md` and report `PASS`, `PASS (NOOP)`, or `FAIL`.

## Quality Gates
- Every changed skill or plugin has a concrete rationale.
- Multi-target runs stay easy to explain target by target.
- Touched Codex-dependent skills name their required Codex tools/contracts clearly, and touched portable skills keep Codex-only helpers optional.
- `run` ends with no unresolved metadata drift or broken references in the touched scope.
- Return `PASS (NOOP)` when no low-ambiguity improvements are found.

## Reporting Contract
- Scope covered
- Packages inspected
- Packages changed
- Checks executed
- Why each changed target was updated
- Result
- Any deferred follow-up
