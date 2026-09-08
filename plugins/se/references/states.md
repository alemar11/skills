# Spec delivery readiness

This reference owns the `spec-delivery` namespace, its persisted GitHub labels
and Markdown `delivery` field, and the label catalog. Spec owns authorization;
Deliver owns the verified handoff to a human. These states are independent of
issue open/closed state, task progress and semantic `spec_revision`.

## States and GitHub labels

| State | Meaning | Color | Label description |
| --- | --- | --- | --- |
| `ready-for-agent` | Authorized for delivery of the agreed scope; dependencies and existing work still govern pickup. | Green `0E8A16` | Authorized for agent delivery; dependencies still gate start. |
| `ready-for-human` | Implementation delivered and verified; awaiting human review, merge or final acceptance. Excluded from automatic pickup. | Orange `D97706` | Implementation delivered; awaiting human review or acceptance. |

When active, GitHub stores exactly one of these labels on the authoritative
parent spec.
Markdown stores the same exact value in its `delivery` frontmatter field.
Neither label, or an empty/null/absent field, means inactive; it is not a third
named state. Task issues and exported snapshots do not receive these states.
Unknown or conflicting values do not authorize automatic pickup.

## Transitions and ownership

- Spec enables `ready-for-agent` only after a verified authoritative save and
  established pickup authorization under its delivery-authorization reference.
- Deliver changes `ready-for-agent` to `ready-for-human` only after the entire
  current spec revision meets its delivery completion criteria, including task
  closure links and combined validation. Ready PRs need not be merged. Partial,
  blocked or task-subset delivery does not trigger the transition. Explicitly
  requested delivery of an inactive saved spec may reach `ready-for-human` under
  the same completion criteria; no intermediate pickup marker is required.
- An already-correct human state is a verified no-op. Ordinary saves and revisions
  preserve it. Only explicit renewed delivery authorization permits a return to
  `ready-for-agent`, after reconciling the changed scope and existing work.
- Explicit revocation removes either owned label or empties the Markdown field.
  Human acceptance and parent closure remain manual unless separately authorized.

The marker is eligibility, not a lock. Before dispatch, reconcile the same spec
identity/revision with existing assignments and PRs. Resume active work; do not
reimplement a delivered revision because a marker update failed. A caller-owned
monitor must filter for `ready-for-agent` on open GitHub parents or authoritative
Markdown specs and reconcile before enqueueing.

## Applying and verifying state

Use G GitHub Issues for exact GitHub label operations, with the caller's scoped
provider preflight and hosted-content safety. Authorized state changes include
creating the missing destination label and applying it without another approval.
Use the exact name, color and description above in every repository; do not infer
colors from local conventions. Reuse existing labels; normalize a differing
color to this catalog while preserving an existing description. Never rename or
delete a repository label or change unrelated labels as incidental maintenance.

Read the exact parent and label catalog first. Ensure the destination label
exists with its canonical color, then replace the old state on that parent,
preserving unrelated labels and open/closed state. Prefer one provider update;
if separate writes are necessary, remove agent eligibility before adding the
human label. Read back the destination label/color and the parent's exact state:
destination present, opposite absent. Label creation alone is not transition proof.

For Markdown, reread the exact authoritative file, reconcile concurrent edits,
change only `delivery`, and verify the new value and preservation of all other
frontmatter, body, task details and progress. Do not edit exported copies or
increment the semantic revision. Respect the source checkout's ownership;
coordinate the metadata edit with its writer rather than overwriting their work.
Normal delivery authority covers this source metadata change, but not a push to
its default branch or an otherwise unrequested commit/publication.

An ambiguous effect requires readback before retry. Preserve verified delivery
and report the metadata handoff separately if its write fails; the handoff is
incomplete and must resume without restarting implementation. Return the exact
source, revision, PR evidence and observed state. Do not claim readiness implies
merge, deployment, human acceptance or completion of the parent spec.
