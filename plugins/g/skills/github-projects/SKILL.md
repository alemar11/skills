---
name: github-projects
description: "Manage GitHub Projects, fields, items, links, and lifecycle for users or organizations."
---

# GitHub Projects

Before any shell command that may contact GitHub or a package registry, read
and follow [Network execution](../../references/network-execution.md). Before
the first provider operation, load
[the GitHub CLI preflight](../../references/gh-dependency-preflight.md) and
complete its Projects capability and scope checks.

Resolve `<plugin-root>` as two directories above the directory containing this
`SKILL.md`.

## Role

Own GitHub Projects lifecycle mechanics for user- and organization-owned
Projects: project discovery and settings, fields, issues and pull requests as
items, draft items, item field values, repository or team links, templates,
archival, closure, and deletion.

Do not manage project view layouts, insights, built-in automations, webhooks,
or organization configuration. Do not add an issue or pull request to a
Project merely because another G workflow created or changed it. Compose with
that workflow only when the user or caller explicitly requests the Projects
operation.

## Transport

- Use authenticated `gh project` with JSON output for structured reads and
  mutations whose arguments contain only exact identities or typed factual
  values.
- Use `gh api graphql --input <absolute-request-json>` for exact identity reads
  not exposed by high-level JSON and for mutations carrying a title,
  description, README, draft body, field name or option, or text field value.
  Put the operation and all variables in the reviewed request file; do not
  interpolate provider text into a shell command.
- Use neither the G CLI nor the maintenance-only `projects/g/` source tree for
  Projects operations. The GitHub product name and that source directory are
  unrelated.
- Use current provider output as authority. Preserve provider-owned IDs,
  lifecycle values, visibility, data types, and field values without
  translating them into G configuration.

## Identity

Resolve a Project to all available exact facts before mutation:

- owner login and whether it is a user or organization;
- project number, GraphQL node ID, and canonical URL.

Accept a canonical user or organization Project URL or an explicit owner plus
project number. Treat a title as discovery evidence only: list the owner's
Projects and proceed only when it identifies one exact Project. Resolve `@me`
to the active account login before reporting or mutating.

Resolve fields, single-select options, iterations, and project items to their
node IDs before changing them. A field name, option name, iteration title, or
item title is not sufficient when more than one match is visible. For an issue
or pull request item, preserve both its canonical content URL/ID and its
Project item ID. For a draft item, preserve both its Project item ID and the
underlying draft-issue node ID.

## Reads

Read Projects, settings, fields, options, iterations, or bounded item collections
with their field values. Pure reads omit `project_operation` and `mutation_mode`.
An empty collection is valid evidence, not an access failure.

## Mutations

1. Resolve one canonical `project_operation` and `mutation_mode` from
   [the invocation registry](../../references/options.md). Direct create, edit,
   add, archive, link, close, reopen, copy, mark, unmark, clear, or delete
   language authorizes only the named operation and target. Otherwise remain
   in `dry-run`.
2. Require the exact existing target or complete creation input. Deletion,
   field deletion, item deletion, closure, unlinking, and archival never infer
   a target from display order or a partial title.
3. Read the current state before mutation. Return `no-op` when it already proves
   the requested state. For create-like operations, retain the pre-existing ID
   set needed to distinguish a new provider object during recovery.
4. For `dry-run`, return the resolved target, proposed change, transport, and
   `previewed` without running the provider mutation.
5. For `apply`, perform the smallest single mutation. Adding an issue or pull
   request and setting its Project fields are separate operations with separate
   authorization and results. Treat each unit of a compound or multi-item
   request as its own canonical operation; execute them as an ordered set of
   individually verified operations rather than inventing a batch operation.
6. Read the exact target back after every attempted mutation. Assign one
   `project_operation_result` from
   [the state registry](references/states.md). After an ambiguous response,
   reconcile once; never replay the mutation.
7. If one operation in a requested set is `failed`, `unavailable`, or `unknown`,
   stop further dependent operations and report the verified state of every
   operation already attempted.

Creating custom fields is limited to text, number, date, and single-select.
Existing iteration fields may be assigned by exact iteration ID. Changes to an
issue or pull request's assignees, labels, milestone, or repository are content
operations, not Project item-field mutations; route them to the workflow that
owns that issue or pull request, then re-read the Project item if needed.

Archiving or deleting a Project item affects its Project membership, not the
underlying issue or pull request. Never translate `delete-item` into deletion
of repository content.

Team links and template state apply only to organization-owned Projects where
GitHub exposes them. Do not substitute a repository link when a requested team
link is unavailable.

## Composition

For cross-domain work, verify the owning operation before passing its exact
provider identity to Projects. Creating an issue, adding its Project item, and
setting fields are separately verified operations within the authorized request.

## Result

Report the owner, project number/ID/URL, item and field identities when used,
canonical operation, mutation mode, pre-read evidence, immediate provider
receipt, exact readback, and one `project_operation_result` per mutation.
Report scope or capability gaps as `unavailable`. For `unknown`, state that the
mutation may have applied and that retry is forbidden until a later exact read
resolves it.

## References

- [workflows.md](references/workflows.md): direct `gh` command patterns, safe
  file-backed GraphQL transport, and reconciliation rules.
- [states.md](references/states.md): canonical Projects operation results.
- [Shared invocation registry](../../references/options.md): canonical
  `project_operation` and `mutation_mode` values.
