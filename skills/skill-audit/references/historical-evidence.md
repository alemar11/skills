# Historical Evidence

Use this branch for audits of completed or prior behavior. Live monitoring uses
`live-monitoring.md` instead and never falls back here to fill a current-state
gap.

## Evidence selection

1. Read the editable target's current discovery metadata, entrypoint, directly
   relevant references, owning manifest, and adjacent repository docs.
2. Check cheap current consistency and maintenance evidence such as `git log`
   for the resolved target.
3. For historical claims, search the memory index and open relevant rollout
   summaries. Static wording review does not require session history.
4. Inspect a representative raw session when claiming runtime behavior, false
   or missed triggers, correctness, orchestration behavior, or low value. If no
   representative trace is available, state that limitation.
5. Treat helper output as evidence, never cleanup or mutation authority.

## Codex Evidence Roots

Resolve the Codex root from `CODEX_HOME` when set; otherwise use the current
user's `.codex` directory. The canonical historical evidence paths are:

- memory index: `<codex-root>/memories/MEMORY.md`
- rollout summaries: `<codex-root>/memories/rollout_summaries/`
- current sessions: `<codex-root>/sessions/`
- archived sessions: `<codex-root>/archived_sessions/`

`<codex-root>/memory/` is not the canonical memory root. Never report memory as
absent after checking only that singular path. If the canonical memory index is
missing, report that exact path and continue with the available evidence.

## Targeted Session Evidence

Run from the `skill-audit` owner root:

```bash
scripts/session-evidence \
  --target my-skill \
  --target-path /path/to/my-skill/SKILL.md \
  --runtime-pattern 'my-skill=my-tool|my-command' \
  --root "$CODEX_HOME/sessions" \
  --since 2026-04-01 \
  --include-zero
```

The helper reports `explicit-user`, `skill-injection`, `opened-skill-doc`, and
`runtime-command` evidence records from direct function calls and code-mode
custom tool calls. Examples retain stable item identity, transport,
`thread_source`, `parent_thread_id`, and raw `forked_from_id` where available.
It excludes tool output and tool discovery as usage.

Read a representative trace before making a high-risk behavioral claim. A
zero-evidence result is not proof that the surface has no value.
