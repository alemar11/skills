# GitHub Release states

This skill does not persist workflow state. GitHub owns release lifecycle
state; the skill derives transient planning and verification state for one
invocation.

## Provider-owned lifecycle

| State | Kind | Meaning |
| --- | --- | --- |
| `missing` | External | The exact tag exists but has no GitHub Release. A separately authorized draft or publish operation may create one. |
| `draft` | External | A GitHub Release exists but is not published. Its notes and assets may be refined before an authorized publish operation. |
| `published` | External | The release is public. Notes may be updated with separate authority; deletion or tag and asset changes are different operations. |
| `prerelease` | External attribute | The release is marked as non-stable. Canonical RC tags must use this attribute. |
| `latest` | External attribute | GitHub marks the release as latest. Historical backfills must preserve another release's latest status. |
| `immutable` | External attribute | GitHub protects the published release's tag and assets. Title and notes remain independently editable when GitHub permits it. |

`prerelease`, `latest`, and `immutable` may coexist with a lifecycle state; they
are not mutually exclusive lifecycle stages.

## Transient workflow state

| State | Kind | Meaning |
| --- | --- | --- |
| `target-unresolved` | Mutation gate | The repository, tag, or comparison range is ambiguous or missing. Stop before a release mutation. |
| `notes-preview-ready` | Derived | An exact proposed title and body are prepared; mutation depends on the request's existing authorization. |
| `draft-creation-authorized` | Mutation gate | The user approved the exact ordinary-create preview; create one draft and verify it. |
| `direct-publish-authorized` | Mutation gate | The user explicitly requested create and publish for one resolved release; skip preview and draft, then verify the published release. |
| `notes-update-authorized` | Mutation gate | The user authorized the notes/title update for the exact existing release. |
| `verified` | Derived | Provider readback matches the authorized tag, lifecycle state, and text or asset fields. |

The `release_operation` values are selectable invocation options owned by
`plugins/g/references/options.md`, not persisted states. A direct-publish
instruction authorizes only the named release creation; it does not authorize
a missing tag, a later notes update, asset mutation, or deletion.
