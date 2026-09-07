---
name: audit
description: "Monitor active tasks using G skills read-only. Use only for an explicit $g:audit request."
---

# G Session Audit

## Scope

Use this skill only after an explicit `$g:audit` invocation. Monitor current
Codex App tasks that show direct evidence of using a skill owned by the G
plugin, regardless of project or host. Do not treat plugin installation,
catalog visibility, a repository path, or a cached copy as runtime use.

Keep the audit read-only. Return the report in the current audit task; do not
write a report file unless the user separately authorizes that destination.
Load [references/states.md](references/states.md) before assigning coverage,
finding kind, bug status, or priority.

## Workflow

1. Inspect the current Codex App capability declarations before using them and
   supply only inputs exposed by the current runtime.
2. Establish the visible project inventory when available, then discover
   recent tasks across available hosts. Reconcile project and host identities
   where the responses expose them. Select every returned task
   that is currently active and can be attributed to a G skill. If the runtime
   cannot establish complete active task coverage, mark the report
   `coverage=partial` and do not claim that all sessions were observed.
3. Exclude the current audit task, other audit/monitor tasks, inactive tasks,
   unrelated chats, and tasks that only expose the skill catalog.
4. Confirm G use from task-visible evidence such as an explicit `$g:<skill>`
   invocation, a linked `plugins/g/skills/<skill>/SKILL.md`, or a G-owned
   script/tool call mapped to the current plugin manifest. Do not infer use
   from titles, descriptions, project paths, or cache state.
5. Read each selected task authoritatively, recording its real
   `thread_id`, `host_id` when exposed, project/repository when exposed,
   status, used G skills, and the evidence frontier. If the read fails,
   times out, or is truncated across the relevant turns, report the evidence
   gap instead of inferring behavior.
6. When bounded multi-task waiting is available, wait in batches of at most
   eight tasks. Re-read a task after a material transition, a cursor or
   evidence gap, and before the final judgment. Continue until every selected
   task reaches a terminal state or the user stops the audit. Without bounded
   waits, use bounded authoritative reads and report the reduced coverage.
7. Compare observed behavior with the exact active G skill contract. Separate
   selection, workflow order, authority/mutation safety, tool routing,
   evidence quality, recovery, and instruction-cost findings.

## Findings and priorities

Classify every item with the canonical finding-kind meanings in
`references/states.md` and keep those report categories separate. Do not treat
model behavior, App availability, repository state, user input, or another
plugin's failure as a G bug unless G owns the missing guardrail.

Assign stable bug IDs in first-seen order (`LIVE-001`, `LIVE-002`, ...). Apply
the status transitions and priorities from `references/states.md`, and keep one
entry per root cause.

## Final report

Return a compact Markdown report with this order:

1. **Monitored tasks** — task ID, host, project/repository, terminal status,
   and confirmed G skills.
2. **Performance snapshot** — compliant behavior, useful feedback, and
   coverage/evidence gaps.
3. **Feedback** — strengths and friction with task-visible evidence.
4. **Bug registry** — ID, status, priority, affected skill, impact, evidence,
   owning surface, and smallest remediation.
5. **Improvements** — proposal, expected value, risk, and priority.
6. **Priority order** — the highest-value next actions, ranked.
7. **Terminal assessment** — assess each used G skill separately and
   distinguish target defects from external runtime or repository conditions.

## Mutation boundary

Do not call task creation, messaging, title, pin, archive, handoff, Goal, Git,
GitHub, or repository-write tools from this skill. If the user requests a fix,
finish the audit and switch to the owning implementation workflow explicitly.

## References

- `references/states.md`: coverage, finding, annotation, and priority states.
