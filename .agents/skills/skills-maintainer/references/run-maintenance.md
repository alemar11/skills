# Run Maintenance Playbook

Use this playbook when the user invokes the maintainer skill generically with `run`, `run your tasks`, or another default maintenance imperative.

## Purpose
- Keep one or more existing skills healthy with proactive, low-ambiguity improvements.
- Treat `run` as the default entrypoint for this maintainer skill.
- Apply concrete maintenance work automatically when the rationale is clear.

## Task Boundary
- If the user does not name skill targets, inspect all local skills in the repository.
- `run` may update multiple skills when each change has a concrete rationale and low ambiguity.
- Auto-apply only safe maintenance items such as:
  - metadata and docs alignment
  - clearer triggers, workflow, guardrails, examples, or references navigation
  - stale path or wording fixes
  - directly coupled `README.md` or `AGENTS.md` wording drift
- Do not infer upstream `benchmark`, Postgres `refresh`, or brand-new skill creation from bare `run`.
- If a candidate change is strategic, high-ambiguity, or likely to alter intent, report it as follow-up instead of auto-applying it here.

## Workflow
1. Enumerate local skills and directly coupled repo docs:
   - top-level reusable skills
   - project-local maintainer skills under `.agents/skills/*`
   - related `README.md` and `AGENTS.md` entries
2. Inspect for actionable drift and shortlist the skills with clear, maintainable improvements.
3. For each shortlisted skill, apply a targeted upgrade using the rules from `skill-upgrade.md`.
4. Run `metadata-sync.md` for the touched skills and coupled repo docs.
5. Run the relevant checks from `doc-consistency.md` across touched areas and repo-level reference drift.
6. Finish with `release-checklist.md` and report `PASS`, `PASS (NOOP)`, or `FAIL`.

## Quality Gates
- Every changed skill has a concrete rationale.
- Multi-skill runs stay easy to explain skill by skill.
- `run` ends with no unresolved metadata drift or broken references in the touched scope.
- Return `PASS (NOOP)` when no low-ambiguity improvements are found.

## Reporting Contract
- Scope covered
- Skills inspected
- Skills changed
- Checks executed
- Why each changed skill was updated
- Result
- Any deferred follow-up
