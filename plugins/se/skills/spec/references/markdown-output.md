# Markdown Output

Read only when the selected destination is Markdown. The content contract is
[specification.md](specification.md); use [spec.md](../templates/spec.md) with
one [task.md](../templates/task.md) section per indexed task.

## Target and authority

Resolve one exact file in the owning repository using the caller's path or an
established repository convention. If neither exists, propose
`docs/specs/<spec_id>.md` within the verified repository. Ask only when competing
destinations or existing unrelated content make that choice material. A
Markdown save authorizes this spec file and required parent directories, not a
commit, product-code edit, or incidental project-context update.

An existing-spec revision keeps its exact file identity. Inspect existing
content before writing; never overwrite an unrelated artifact, follow an
unexpected symlink outside the authorized repository, or replace another
spec because its title resembles the requested one.

## Render and save

Render the complete document before changing the target. Include the main
specification, acceptance criteria, ordered task index, dependencies, and full
task details in the same file. Use the stable task IDs as explicit section
anchors so reordering does not break links. Do not create per-task files or
require GitHub identities, labels, or native relationships.

For `operation=preview`, return that complete candidate and proposed path
without creating directories or files. For `operation=save`, compare the target
with the version inspected, apply the scoped change, and read it back. If a
concurrent edit appeared, reconcile that content before writing; do not clobber
it. Verify exact identity and revision, complete task membership and details,
acceptance coverage, anchors, dependencies, and preservation of unrelated or
executor-owned content. An ambiguous write is reconciled against this exact
path before any retry.

Use portable repository-relative evidence links or attributable external
sources. Machine-specific planner paths, prompts, tokens, and task transcripts
do not belong in the saved specification.

G is unnecessary for rendering or saving Markdown. If the source is a GitHub
issue, Intake still performs the G preflight for that source read. A local-only
source constraint prohibits that read on either destination.

For an export from a different authoritative destination, follow
[existing-specs.md](existing-specs.md): label the file as a snapshot and preserve
the source identity and revision. A copy does not silently become authoritative.
