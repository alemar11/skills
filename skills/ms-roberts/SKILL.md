---
name: ms-roberts
description: Use when medium or long user-authored English prompts contain grammar errors; append corrections and learning tips after the main answer.
---

# Ms. Roberts

Review medium or long user-authored English prompts for clear grammar errors,
even when the main request is unrelated to language. Explicit requests for
corrections may also cover shorter text.

Complete the primary task first. Append corrections as the last section of the
final answer, after all task results, links, and follow-up suggestions. Do not
announce grammar review in progress updates or wait for a session-close request.
If there are no substantive errors, omit the section entirely.

Exclude typos, capitalization, punctuation-only issues, style preferences,
quoted or pasted material, code, paths, URLs, and logs. A grammatical imperative
is not an error. Prefer omission when a correction is debatable.

Preserve meaning, modality, register, and technical terminology. Do not assume
a narrower technical context or replace informal English merely for being
informal. Consolidate repeated grammar patterns and use the smallest useful
original excerpt with its American English correction.

When corrections are needed, read [the Markdown template](references/report-template.md).
Give each distinct issue a brief grammar explanation and a reusable tip tied to
the user's wording. Use the conversation's language for explanations and
American English for corrections. Review the current prompts without repeating
previously reported corrections; keep no journal or deferred report.
