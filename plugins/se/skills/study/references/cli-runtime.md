# Study CLI Runtime

Read this reference only when `study_surface=cli-session`. It owns same-session
control, current-directory context, immediate Grilling Session, and surface-specific
subagent context.

## Current-session controller

The invoking CLI session is the Study controller. Do not create a separate App
task, fork the session, or transfer the handoff elsewhere.

- Keep the controller's current model and reasoning profile. Study neither
  overrides nor gates that inherited profile.
- Use the current working directory and supplied discussion as the initial
  repository context. A saved App project is not required.
- Retain the curated handoff transiently as the authoritative Study brief. Do
  not write it to disk.
- Compose `$se:grilling-session` immediately and ask its first question directly in
  the current CLI session. There is no parent relay or setup-only turn.

Continue the interview in this session until its state is `refined`,
`user-stopped`, or `blocked`. Create no subagents while an answer is pending.
After a refined or stopped handoff, apply the shared worker planning rules in
[orchestration.md](orchestration.md).

The CLI branch has no App controller task identity, requested title, host,
saved-project task placement, or App task telemetry. Mark those state fields
`not-applicable` internally and omit their report sections.

## Subagent context

After Grilling Session is refined or stopped, apply the shared native-subagent contract
in [orchestration.md](orchestration.md). Every subagent remains under the
current CLI controller lineage and uses the current working-directory context.
Subagents have no App task title, saved-project placement, or archival fields.
