# Hosted Content Safety

This is SE's canonical owner for portable content, single-line titles, pre-write
correction and bounded post-write repair. Apply it to every hosted issue, PR,
comment, review request, review and Feature maintenance changelog produced by
Spec, Deliver or Delivery Features. It also governs commit messages
prepared for publication under an SE assignment, as described below.

SE owns the semantic projection; G owns transport, mutation, receipts and readback.
G does not infer repository context or sanitize meaning. SE computes corrections
and updates the same hosted artifact through its owning G workflow.

## Internal records and hosted content

Internal records may retain workflow-required local facts such as `project_root`,
worktree paths, host/task identity, prompts, dialogue and tool output. Keep them
separate from hosted content.

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

## Commit messages prepared for publication

When an assignment includes later publication, apply portable projection to
new commit subjects and bodies before creating the commit. Validation prose
should name relevant checks and results without copying machine-specific
environment assignments or command paths. Keep exact local execution details
in the private handoff when needed.

Inspect existing commit messages before publishing the assigned range. This
content policy does not authorize rewriting existing commits or force-pushing.
Report a discovered local path against the full commit SHA; do not create a
replacement commit merely to hide it. Already-published commit messages use
this warning path, not the mutable-artifact repair procedure below.

## Final pre-write correction

Immediately before every write, inspect the exact final title and body, comment
or review handed to G against the projection and title rules above. Check copied
content too, and ensure the evidence needed by the operation remains intact.
Correct failures in the same rendered content and repeat the complete check;
any later content change requires another check. Never hand a known local
absolute path to G. Omitting optional local evidence follows the warning rule
above and does not require a planning question or block the enclosing workflow.

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
