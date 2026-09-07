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
detailed task contract and links to the parent. Parent and task issue types or
labels are optional metadata, never identity, readiness, or work-dispatch signals.

For `operation=preview`, render the parent, every child body, intended targets,
and proposed mappings without any hosted write or collision claim. New local
source previews need no G access. An explicit hosted source read remains governed
by Intake's preflight and caller constraints.

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
   references and all child parent/dependency summaries. Read back the complete
   spec and task bundle; no task detail may disappear during projection.
4. Establish parent-child relationships and verify them. If a native relation
   is unsupported, record the observed limitation and retain verified reciprocal
   body links as the association. Missing or incorrect body links block.
5. Attempt each canonical task dependency as a native blocking relationship
   where supported, and record the result for every edge. An unavailable native
   capability is recorded explicitly; it never changes the semantic graph.
6. Optionally classify issues through `g:github-issues` after semantic save.
   Metadata failure does not block completion or imply an implementation order.

Every required issue identity, body, task association, and dependency summary
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
