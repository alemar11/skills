---
name: plan-hard
description: Create a higher-rigor implementation plan when the user explicitly asks for deeper planning, a harder plan, or a stress-tested plan before coding. Use to research the codebase, ask focused clarifying questions, write a phased plan under `./plans/`, and review it for gaps before implementation starts.
---

# Plan Hard

## Goal

Produce a deeper implementation plan than a normal planning pass. Slow down,
reduce ambiguity, surface hidden risks, and leave behind a concrete plan that
is ready for careful execution.

Only create the plan. Do not implement the work.

## Trigger Rules

- Use when the user explicitly invokes `plan-hard` or asks for a harder,
  deeper, or more stress-tested plan.
- Use when the task is ambiguous, high-risk, multi-phase, or likely to hide
  ordering problems or missing validation steps.
- Do not use for straightforward planning work that does not need an extra
  review pass.

## Workflow

### 1. Research First

- Inspect the codebase, architecture, existing patterns, and nearby tests.
- Identify dependencies, edge cases, rollout concerns, and likely failure
  modes before drafting the plan.

### 2. Clarify High-Risk Unknowns

- Ask focused clarifying questions before drafting the plan when ambiguity
  could materially change the work.
- Prefer `request_user_input` when available.
- Respect the runtime limit of 1-3 questions per `request_user_input` call;
  if more clarification is needed, ask only the highest-signal next batch.
- Prioritize questions about:
  - scope and non-goals
  - success criteria
  - compatibility constraints
  - rollout/rollback expectations
  - validation expectations

### 3. Fetch Official Docs When Needed

- If the plan depends on external libraries, frameworks, APIs, or tools whose
  current behavior matters, fetch the relevant official documentation before
  finalizing tasks.
- Use the runtime's best official-doc path for the current environment rather
  than relying on memory when the detail is likely to drift.

### 4. Draft the Plan

Create a phased plan with:

- a short overview
- prerequisites
- logical sprints or phases
- atomic tasks with clear boundaries
- validation per task
- testing strategy
- risk and rollback notes

Each task should be:

- small enough to commit independently when practical
- specific about files or areas touched when known
- explicit about dependencies on earlier tasks
- testable or otherwise verifiable
- concrete about what "done" means

### 5. Save to `plans/` by Default

- In the current working directory, ensure a `plans/` directory exists.
- If it does not exist, create it before saving the plan.
- Save the generated plan to `plans/<topic>-plan.md`.
- Derive `<topic>` from the request using kebab-case.

Examples:

- `fix auth timeout bug` -> `plans/auth-timeout-bug-plan.md`
- `design a safer webhook retry flow` ->
  `plans/safer-webhook-retry-flow-plan.md`

### 6. Run a Gotcha Pass

- Re-read the saved plan and look for:
  - missing steps
  - missing dependencies
  - vague acceptance criteria
  - unsafe ordering
  - rollout or rollback gaps
  - missing validation
- If real gaps remain, ask the minimum follow-up questions needed and update
  the saved plan.

### 7. Review Before Returning

- Review the saved plan for:
  - missing dependencies
  - ordering failures
  - unhandled edge cases
  - vague or untestable tasks
- If explicit delegation is allowed in the current run, you may ask a subagent
  to perform this review. Tell the reviewer not to ask questions and to return
  only actionable feedback.
- Otherwise, perform the same review locally before returning.
- Incorporate useful review feedback into the saved plan before finishing.

## Plan Template

```markdown
# Plan: [Task Name]

**Generated**: [Date]
**Estimated Complexity**: [Low/Medium/High]

## Overview
[Summary of the work and the recommended approach]

## Prerequisites
- [Dependencies or requirements]
- [Tools, libraries, access, or docs needed]

## Sprint 1: [Name]
**Goal**: [What this phase accomplishes]
**Demo/Validation**:
- [How to demo or verify the phase]

### Task 1.1: [Name]
- **Location**: [File paths or areas]
- **Description**: [What to do]
- **Complexity**: [1-10]
- **Dependencies**: [Earlier tasks or `None`]
- **Acceptance Criteria**:
  - [Specific outcome]
- **Validation**:
  - [Tests or verification steps]

### Task 1.2: [Name]
[...]

## Sprint 2: [Name]
[...]

## Testing Strategy
- [How to validate the work]
- [What to verify per phase]

## Potential Risks & Gotchas
- [What could go wrong]
- [Mitigation]

## Rollback Plan
- [How to safely undo or disable the change]
```

## Output Expectations

- Return the final saved plan path.
- Summarize the main phases, the riskiest assumptions, and any open questions
  that remain.
- Do not implement the plan.

## Example Requests

- "Plan hard for this auth migration before we touch any code."
- "Give me a deeper, stress-tested implementation plan for this feature."
- "Make a harder plan for this refactor and save it under `plans/`."
