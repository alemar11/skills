---
name: github-issues
description: "Manage GitHub issues and relationships, classify labels and types, or propose issue taxonomy."
---

# GitHub Issues

Own issue lifecycle operations, evidence-based label/type selection, and explicit
read-only taxonomy proposals. Product planning and orchestration remain with
the caller.

## Select the work

- For exact issue reads or lifecycle operations, including caller-selected
  metadata, comments, attachments, and relationships, read
  [lifecycle.md](references/lifecycle.md).
- For content-based label/type selection on an existing issue, read
  [metadata-classification.md](references/metadata-classification.md). The
  request selects preview or application; classification does not authorize
  label removal or taxonomy changes.
- Only for an explicit request to audit, design, recommend, or propose issue
  taxonomy, read [taxonomy-proposals.md](references/taxonomy-proposals.md).
  This branch is read-only and requires a repository, not a target issue.

These are request-derived branches, not persisted modes. Exact metadata
operations do not require classification. Read [states.md](references/states.md)
when interpreting native dependency, classification, or taxonomy results.

## Shared boundaries

Before contacting GitHub, read the shared
[network execution](../../references/network-execution.md) and
[GitHub CLI preflight](../../references/gh-dependency-preflight.md) contracts.
Use authenticated `gh`; binary uploads use only the bundled attachment
transport documented in the lifecycle branch.

Resolve the exact repository and target before mutation. Preserve existing
user authority: explicit write instructions authorize their scope; a preview
or recommendation alone does not. Normalize operations with the shared
[options](../../references/options.md). Classification may derive separate
label and type operations from one authorized classification request.

Keep free-form provider fields file-backed. Independently read mutations back
and reconcile uncertain effects before retrying. Report exact issue URLs,
verified changes or proposals, and unresolved evidence; do not infer success
from a write receipt.

Use `$g:github-investigation` for root-cause or disposition judgment and
`$g:github-repository-triage` for issue/PR queues. Classification and taxonomy
analysis require Investigation only when their evidence needs deeper source or
history analysis.
