# G Invocation Registry

Use these canonical input fields when a G skill or composing workflow
must normalize behavior for one invocation. They are protocol inputs, not
persistent user settings or a checklist to present to the user. Derive them
from the explicit request and ask only when the target, action, or mutation
authority is ambiguous. Field names are `snake_case`; assigned values are
lower-kebab.

## G-owned invocation fields

| Field | Allowed values | Default | Meaning |
| --- | --- | --- | --- |
| `mutation_mode` | `apply`, `dry-run` | `dry-run` | For a write-shaped GitHub operation, whether it executes or returns a preview. Omit this field for pure reads. |
| `issue_operation` | `create`, `edit`, `set-type`, `remove-type`, `create-label`, `add-label`, `remove-label`, `comment`, `attach-parent`, `remove-parent`, `add-sub-issue`, `remove-sub-issue`, `add-blocked-by`, `remove-blocked-by`, `close`, `reopen` | none | The one issue lifecycle operation being requested. |
| `project_operation` | `create`, `copy`, `edit`, `close`, `reopen`, `delete`, `mark-template`, `unmark-template`, `link-repository`, `unlink-repository`, `link-team`, `unlink-team`, `create-field`, `delete-field`, `add-item`, `create-draft-item`, `edit-draft-item`, `set-item-field`, `clear-item-field`, `archive-item`, `unarchive-item`, `delete-item` | none | The one GitHub Projects mutation being requested. Pure project, field, and item reads omit it. |
| `commit_operation` | `commit-only`, `commit-and-push`, `push-only` | none | The local Git operation owned by Git Commit. |
| `commit_kind` | `regular`, `fixup`, `amend-fixup` | `regular` | The commit form for a commit-producing operation. Non-regular kinds require an exact `target_commit`. |
| `review_operation` | `inspect`, `check`, `wait`, `ready-check`, `ready-wait`, `terminal-evidence`, `request`, `comment`, `edit-comment`, `submit-review`, `reply`, `resolve` | none | The one pull-request review operation being requested. `ready-check` and `ready-wait` observe the provider review caused by one typed ready transition; they never post a request. |
| `release_operation` | `inspect`, `create-tag`, `draft`, `publish`, `update-notes`, `upload-asset`, `delete` | `inspect` | The requested tag or GitHub Release lifecycle operation. `publish` also covers an explicitly requested direct create-and-publish operation. |

Keep an operation separate from its issue, PR, project, project item, field,
release, label, or relationship reference.

`target_commit` is exact factual input, not an option value. Require it for
`commit_kind=fixup|amend-fixup`, resolve it to one full commit SHA, and omit it
for `commit_kind=regular` and `commit_operation=push-only`.

## Boundary normalization

| Input evidence | Canonical invocation |
| --- | --- |
| `commit`, `commit this`, or `create a commit` | `commit_operation=commit-only` |
| `commit and push` | `commit_operation=commit-and-push` |
| `push-only` | `commit_operation=push-only` |
| `fixup <commit>` | `commit_operation=commit-only`, `commit_kind=fixup`, and exact `target_commit` |
| `fixup and push <commit>` | `commit_operation=commit-and-push`, `commit_kind=fixup`, and exact `target_commit` |
| `amend fixup <commit>` | Commit-producing operation plus `commit_kind=amend-fixup` and exact `target_commit` |
| Pure inspection, check, wait, or other read | Omit `mutation_mode` |
| List, view, or filter GitHub Projects, fields, or items | Omit `project_operation` and `mutation_mode` |
| Explicit GitHub Projects mutation with an exact owner and target or complete creation input | Matching `project_operation` plus `mutation_mode=apply` |
| `create a release` or `create a draft release` without direct publication language | `release_operation=draft`, `mutation_mode=apply`; prepare the notes and create the draft within the requested scope |
| `create and publish the release` for one resolvable existing tag | `release_operation=publish`, `mutation_mode=apply`; skip the notes preview and draft stage |
| `improve the release description` | `release_operation=update-notes`, `mutation_mode=apply`; prepare and apply the replacement within the requested scope |
| `dry run`, `preview only`, `local only`, or `do not mutate` for a write-shaped request | `mutation_mode=dry-run` |
| Other explicit create, edit, publish, post, close, or reopen instruction for an exact target | `mutation_mode=apply` plus the matching operation |

Resolve natural-language instructions to canonical values. Structured callers
must use only the applicable registry fields; reject unknown fields or values.
Factual envelope fields such as `ok: true`, GitHub API fields, CLI flags, and
other externally owned syntax are not option values and remain unchanged.

## Issue metadata classification

A request to select suitable labels or a type uses the conditional
[classification workflow](../skills/github-issues/references/metadata-classification.md).
An exact caller-selected metadata operation bypasses classification.
Classification resolves `mutation_mode` before selection and derives separate
`add-label` and `set-type` operations only for supported changes. A composed
classification request supplies the exact repository, issue, optional requested
dimensions, and `mutation_mode`; it need not preselect an `issue_operation`.
Taxonomy proposals are read-only and omit both operation and mutation fields.

## Caller-owned authorization

G does not own planning or orchestration authority. When another
workflow calls a G mutating skill, that caller must normalize
its own policy to `mutation_mode=apply`, the exact target, and one canonical
G operation before invocation, except for the classification branch above.
G rejects caller-owned planning,
tracker, orchestration, delivery, publication, permission, or phase fields
instead of interpreting them. `mutation_mode=apply` authorizes only the named
operation and target.
