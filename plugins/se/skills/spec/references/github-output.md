# GitHub Output

Read only for GitHub preview or save. The content contract is
[specification.md](specification.md). G owns issue transport, safe file handling,
provider operations, and readback; Spec owns the semantic projections.

## Projection

Save one main spec issue in its `owner_repository` and one associated issue per
task. Put a single-repository task in that repository. Put a multi-repository
task in the spec's owner repository unless the caller explicitly chooses another
affected repository; its body still names every contributing repository.

The parent owns the specification and ordered task index. Each child owns its
detailed task contract, including prerequisites, and links to the parent.
Use the spec template for the parent and the task template for each child;
keep task details out of the parent. The parent task list links to every child.
Issue types and classification labels are optional metadata, never identity or
dispatch signals. The main spec's [delivery marker](delivery-authorization.md) is
the explicit pickup-authorization exception.

For `operation=preview`, render the parent, every child body, intended targets,
and proposed mappings without any hosted write or collision claim. New local
source previews need no G access. An explicit hosted source read remains governed
by the hosted-source preflight and caller constraints.

## Save and verify

Before hosted reads or writes, run the shared
[G dependency preflight](../../../references/codex-dependency-preflight.md).
Before each write, apply
[hosted-content safety](../../../references/hosted-content-safety.md) to the
exact final title/body, including worker- or provider-originated content.

1. Resolve exact target repositories and inspect for existing artifacts with
   the intended spec/task identities. Reuse a verified matching identity; a
   materially different collision needs reconciliation before creation.
2. Create the main spec, then each missing task issue. Preserve receipts and
   read back each artifact before proceeding. Existing revisions update the
   same artifacts under [existing-specs.md](existing-specs.md).
3. Once all identities exist, reconcile the parent task index with their exact
   references and each child's parent reference. Read back the complete
   spec and task bundle; no task detail may disappear during projection.
4. Establish parent-child relationships and verify them. If a native relation
   is unsupported, record the observed limitation and retain verified reciprocal
   body links as the association. Missing or incorrect body links block.
5. Derive dependencies from every task body and attempt each canonical dependency
   as a native blocking relationship where supported, and record the result for every edge. An unavailable native
   capability is recorded explicitly; it never changes the semantic graph.
6. Optionally classify issues through `g:github-issues` after semantic save.
   Classification must not add or remove the delivery marker. Optional
   classification failure does not block semantic save or imply execution order.

Every required issue identity, body, task association, and task prerequisite
must be verified. Native relationship/dependency failures are warnings when
the complete body-backed representation is verified; absent result coverage
is not success. Preserve foreign provider edges and metadata. On revision,
remove only native edges proved SE-owned and explicitly retired from the plan.

After an ambiguous operation, inspect the same intended artifact before retrying.
Reuse a proved identity, retry only after proved non-application, and stop on
unresolved ambiguity. Partial publication reports the exact completed and
remaining artifacts; never replay the whole batch or substitute a local save.

Saving the plan does not close tasks, the parent, or source issues. A separately
requested source-Idea closure or downstream notification occurs only after the
complete save is verified and through its authorized owner. Reconcile that
requested effect before completion.

## Delivery marker

After the complete authoritative bundle is verified, apply the decision from
[delivery-authorization.md](delivery-authorization.md) through `g:github-issues`.
For approval, inspect the main issue's exact repository label catalog. Reuse the
existing label without changing its color or description. If missing, create
the owned label with description "Fully specified and queue-ready; listed
dependencies still gate start" and the repository's workflow-label color
convention, or `0E8A16` when none exists. The user's pickup approval covers this
creation and application; no taxonomy proposal or second permission is required.

Verify label existence, apply it only to the main spec issue, and read back its
presence while preserving all other labels. A task issue or an export must never
receive the pickup marker from this workflow. For explicit revocation, remove
only this marker from the main issue and verify absence; do not delete the
repository label.

Marker operations follow the same G preflight, hosted-content safety and
uncertain-effect reconciliation as other writes. A failed or ambiguous marker
operation leaves the verified spec saved but the requested authorization change
incomplete. Retry only the unresolved effect against the same repository/issue;
do not recreate the spec or report pickup enabled from label creation alone.
