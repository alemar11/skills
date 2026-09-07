---
name: focus
description: Create one new Codex task with a compact handoff of the current discussion. Use only when explicitly invoked.
---

# Focus

Invocation authorizes one new task. Infer the latest unresolved objective or
accepted direction from the conversation; do not browse or inspect repository
files merely to write the handoff. Leave the calling task unchanged.

Write a concise title with one relevant leading emoji and a handoff of at most
200 words: objective, accepted decisions, constraints, blocker, and next action
as applicable. End the handoff with:

> Do not begin work yet. Acknowledge this focus briefly, then wait for the user's follow-up.

For repository work, match the current root and host to one saved project and
use it directly. For projectless work, create a standalone task. Preserve the
user's configured model and reasoning defaults. Do not fork or send an extra
follow-up message.

Read [states](references/states.md) before creation and reconciliation. Require
support for the requested destination and independent task verification; report
a missing capability or ambiguous project rather than creating elsewhere.

Create once, then independently verify identity, destination, execution mode,
and operational state. Set the title during creation when supported; if needed,
make at most one title correction and read it back. Title drift is a warning
unless the user requires an exact title.

After an uncertain result, reconcile before retrying. Reuse an existing task;
retry creation only after authoritative evidence proves none was created.
If uncertainty remains, report the partial result without creating a replacement.
Return the native created-task link or card and any unresolved limitation.
