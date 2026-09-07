---
name: github-tagger
description: "Choose existing issue labels and type, or propose missing taxonomy read-only when requested."
---

# GitHub Tagger

Before any shell command that may contact GitHub or a package registry, read
and follow [Network execution](../../references/network-execution.md).

## Role

Choose the smallest evidence-backed set of existing labels, including none,
and zero or one native issue type for an exact issue. Explicit taxonomy analysis
instead proposes missing definitions read-only. `g:github-issues` owns writes;
route there directly when the user already selected exact metadata.

## Scope

- Default to `tagger_mode=issue-classification`, which classifies one exact
  issue number or URL per invocation. A caller handling a batch must invoke
  this workflow separately for every frozen issue identity.
- Select `tagger_mode=taxonomy-proposal` only for an explicit request to audit,
  design, recommend, or propose repository issue taxonomy. This mode accepts
  one exact repository and does not require one target issue.
- Treat repository labels and enabled native issue types as the assignable
  classification catalog. Never hardcode names such as `bug`, `feature`, or
  `task`.
- Read visible issue fields, milestone, assignees, project membership,
  relationships, dependencies, and current state only as context. Do not
  change them from this skill.
- Add zero or more supported labels and set at most one supported issue type.
  Preserve all existing labels; do not create, rename, remove, or reinterpret
  taxonomy during issue classification.
- Taxonomy proposal mode may recommend new repository labels and organization
  issue types, but never creates, edits, disables, deletes, or assigns them.
- Keep closure, priority decisions, ownership assignment, queue triage,
  planning, and technical investigation in their focused workflows.

## Transport

Use authenticated `gh` for provider reads. Before the first provider operation,
load
[`../../references/gh-dependency-preflight.md`](../../references/gh-dependency-preflight.md),
then read [Provider reads](references/provider-reads.md). Distinguish an empty
catalog from a catalog that could not be read.

This skill performs no direct write transport. Route each authorized
`add-label` or `set-type` operation to `$g:github-issues`, then independently
read the issue back before reporting success.

## Mutation Authority

- Taxonomy proposal mode is always read-only. An instruction to analyze,
  propose, recommend, or audit taxonomy does not authorize creating or changing
  any label, type, or issue.
- Resolve an explicit instruction to tag, label, assign labels, apply the
  classification, or set the type on the exact issue as
  `mutation_mode=apply`.
- Resolve requests to classify, categorize, recommend, suggest, preview, or
  explain suitable metadata without an explicit application verb as
  `mutation_mode=dry-run`.
- Accept a composed handoff only when it already contains the exact repository,
  issue identity, and canonical `mutation_mode`. Reject caller-owned tracker,
  planning, or orchestration policy.
- `mutation_mode=apply` authorizes only adding the selected existing labels and
  setting the selected existing type. It never authorizes label removal,
  taxonomy changes, or mutation of contextual metadata.

## Issue Classification Workflow

1. Resolve the exact repository and issue identity. Stop if the target is a
   pull request, does not exist, or remains ambiguous.
2. Resolve `mutation_mode` and the requested classification dimensions from
   the request. Evaluate both labels and native type unless the caller narrows
   the request to one dimension. Do not ask for confirmation when the direct
   user instruction already authorizes the exact operation.
3. Read the issue title, body, relevant comments, current labels, current type,
   state, and available contextual metadata. Preserve the issue URL for the
   final report.
4. Inventory the current assignable catalog:
   - every repository label with its exact name and available description;
   - every enabled native issue type assignable to the issue, with its exact
     name and available description;
   - visible categorical field definitions and current contextual metadata
     only when they help interpret the issue.
5. After both the issue and catalog are available, read
   [Classification](references/classification.md) and derive one proposal from
   the current evidence. Read [States](references/states.md) before returning
   or applying a proposal.
6. Re-read the target and selected catalog entries immediately before a write.
   If the issue changed materially or a selected value is no longer
   assignable, reclassify instead of applying stale output.
7. For `mutation_mode=dry-run`, make no write. Return the exact proposed labels,
   proposed type, evidence, skipped dimensions, and status.
8. For `mutation_mode=apply`, send only missing labels through one canonical
   `issue_operation=add-label` handoff and send a changed type through a
   separate canonical `issue_operation=set-type` handoff. Apply the
   unambiguous subset when the classification is partial; skip ambiguous
   dimensions.
9. After every write receipt, read the exact issue back. On an uncertain or
   partial failure, reconcile provider state before retrying and never repeat
   an already-applied operation.
10. Report the exact issue URL, catalog availability, prior assignments,
    proposal, concise evidence per selected value, `classification_disposition`,
    `application_status`, verified final assignments, and anything skipped.

## Taxonomy Proposal Workflow

1. Require an explicit taxonomy-analysis request and resolve one exact
   repository. Set `tagger_mode=taxonomy-proposal` and do not derive
   `mutation_mode` for this read-only branch.
2. Read [States](references/states.md), inventory the complete visible label
   and native type catalogs, and distinguish an empty catalog from unavailable
   metadata.
3. Inspect repository-owned issue templates, contribution guidance,
   architecture or ownership evidence, and stable product or component
   boundaries. Use `$g:github-investigation` when this requires deeper code or
   history analysis.
4. Inspect a representative open-and-closed issue corpus. Preserve exact issue
   URLs, exclude pull requests, include issues with missing metadata, and report
   sampling or visibility limits.
5. Read [Taxonomy proposals](references/taxonomy-proposals.md) and test for
   recurring gaps against the existing catalogs.
6. Propose the smallest evidence-backed set of new label definitions and, for
   an organization repository, new issue-type definitions. Returning no
   proposal is valid when existing taxonomy is sufficient or evidence is weak.
7. Make no mutation, even when provider APIs and caller permissions could
   support one. Return exact creation-ready definitions only as recommendations.
8. Report corpus coverage, sources, current-catalog availability, proposals,
   evidence, limitations, `taxonomy_disposition`, and the explicit no-write
   result.

## Issue Classification Selection Rules

- Use label and type descriptions as repository-owned semantics. Names are
  secondary evidence and colors are never enough to establish meaning.
- Choose the smallest orthogonal label set. Do not add a label that merely
  duplicates the selected type unless repository evidence establishes that
  both are intentionally used together.
- Selecting zero labels is correct when no available label is pertinent.
- Treat issue type as singular. Select zero types when none clearly applies;
  leave the current type unchanged rather than inventing or removing a type.
- Do not infer workflow readiness, severity, priority, ownership, or release
  scope from vague wording. Select such metadata only when the issue evidence
  and repository-owned description establish it.
- Never force a match. Ambiguity and unavailable metadata are valid reported
  outcomes, not permission to invent a category.

## Skill Dependencies

- `$g:github-issues` is required only for authorized `add-label` and `set-type`
  mutations. Classification and dry-run output remain owned by this skill.
- `$g:github-investigation` is required when choosing metadata depends on code,
  root-cause, fix-quality, or acceptance-evidence judgment that the issue text
  does not establish, or when taxonomy analysis needs repository history or
  source evidence beyond stable documentation and issue templates.

## References

- `references/classification.md`: evidence ranking, selection, drift, and output
  rules. Read after the issue and assignable catalog are available.
- `references/taxonomy-proposals.md`: repository and issue-corpus evidence,
  gap tests, proposal shapes, and the no-write boundary. Read only for an
  explicit taxonomy proposal.
- `references/provider-reads.md`: read-only `gh` operations for the target issue,
  label catalog, and organization type catalog.
- `references/states.md`: canonical transient dispositions and external-state
  boundaries. Read before applying or returning a result.
- `../../references/options.md`: shared canonical G invocation fields.
