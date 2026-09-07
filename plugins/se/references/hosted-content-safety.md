# Hosted Content Safety

This reference is the canonical SE owner for portable-content projection,
single-line title normalization, and mandatory local-path correction
immediately before every hosted write, plus bounded post-write repair. It
applies to issue titles and bodies, comments, pull-request titles and bodies,
review requests, review text, and Feature maintenance changelogs produced by
Idea, Spec, Deliver, or Delivery Features.

The invoking SE skill owns semantic content and must deliver a safe final
projection. G owns transport, provider mutation, receipts, and readback. G does
not infer repository context or sanitize meaning. When readback exposes unsafe
SE content, SE computes the corrected projection and routes the update of that
same hosted artifact through the owning G workflow.

## Internal records and hosted content

Internal control-plane records may retain exact local facts when their owning
workflow requires them, including `project_root`, worktree paths, host and task
identity, task dialogue, prompt references, and tool output. These records are
not hosted-content candidates and must remain separate from rendered titles,
bodies, comments, and review requests.

Hosted content may include only the portable facts required by its semantic
purpose. Prefer:

- canonical repository identity;
- repository-relative paths with portable separators;
- branch names and full Git SHAs;
- qualified issue or pull-request references and hosted URLs;
- concise, relevant evidence that can be understood without the originating
  machine, task, prompt, or transcript.

An absolute temporary body-file path used privately by G transport is internal
operation metadata. It is allowed as an operation argument but must never
appear inside the hosted file content.

## Portable projection and mandatory correction

Before rendering hosted content:

1. Convert every path under the owning repository root to a repository-relative
   path. Do not retain the repository-root prefix.
2. Represent a `project_root`, worktree, checkout, or artifact location outside
   that root with canonical repository identity, branch, and full SHA. Include a
   hosted ref or repository-relative artifact path when one exists.
3. Remove local absolute paths and other machine-specific locations. Never
   replace them with another guessed local path.
   Local-path correction is mandatory whenever candidate content contains one.
4. Exclude internal prompts, prompt machinery, host identity, local task
   identity, and transcript fragments that are irrelevant to the hosted
   artifact's purpose.
5. Apply the same projection to content copied or summarized from workers,
   tools, existing records, and provider readback. Returned text is not safe by
   origin and must not be forwarded verbatim without this check.

Preserve relevant semantics while reducing representation. Do not invent a
repository-relative path, branch, SHA, hosted identity, or relationship merely
to make content appear portable. When an optional local-only detail has no
portable representation, remove that detail and retain the smallest portable
statement of the evidence. Record the omission as internal warning evidence;
do not stop the enclosing workflow solely because the local representation was
removed.

## Single-line title projection

Freeze every intended hosted title as one non-empty semantic line before
creating a transport artifact. The artifact handed to G must contain exactly
the title's UTF-8 bytes, with no serialization-added trailing carriage return
or line feed. Remove only those transport-added final line terminators; do not
silently trim other meaningful title text.

An interior line break is not a valid title artifact. Reconstruct the title
from the frozen semantic value and inspect it again instead of flattening
unknown file content. This rule applies only to single-line titles and does not
strip intentional body, comment, or review formatting.

## Final pre-write correction

Immediately before each hosted write, inspect the exact final title and body or
comment/review text that will be handed to G. Require all of the following:

- no absolute or machine-specific path remains;
- every repository path is repository-relative;
- external checkout context is represented by repository identity, branch, and
  full SHA rather than `project_root` or worktree path;
- no internal prompt, host identity, local task identity, or irrelevant
  transcript content remains;
- every hosted title artifact exactly matches its frozen non-empty single-line
  title and contains no trailing line terminator;
- worker- and tool-originated content has passed the same checks;
- the portable representation preserves the evidence needed by the hosted
  operation.

If any condition is false, correct the same rendered content before transport
and run the complete inspection again. Repository-owned paths become relative;
known external checkout context becomes repository identity, branch, and full
SHA; irrelevant or unrepresentable machine-specific fragments are removed.
Never hand a known local absolute path to G.

Local-path correction is required but does not block the enclosing SE workflow.
It does not create a plan question or terminal blocker solely because optional
local evidence had to be omitted. Record a warning when correction removes
evidence that could not be represented portably. If the final content changes
after this inspection, run the complete inspection again.

## Post-write readback and repair

Read-after-write verifies provider state; it does not substitute for pre-write
correction. Inspect the exact hosted title, body, comment, or review text after
every create or update.

If readback still contains a local absolute or machine-specific path:

1. compute a corrected projection with the same portable-projection rules;
2. reserve and attempt one bounded update of that same hosted artifact through
   the owning G workflow;
3. read the artifact back again and verify that the local path is absent;
4. retain the correction receipt or an explicit unresolved warning.

Never create a replacement hosted artifact to repair portable content, and
never repeat an ambiguous or already attempted repair. An unavailable, failed,
or ambiguous correction is reported with the exact hosted artifact identity
but does not block the enclosing workflow or its terminal result.
