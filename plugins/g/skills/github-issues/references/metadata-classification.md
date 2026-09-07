# Issue Metadata Classification

Read for content-based label/type selection for one exact issue. For a batch,
freeze the issue identities and classify each separately. Reject pull requests,
missing issues, and ambiguous targets.

## Request and authority

Evaluate labels and native type unless the request narrows the dimensions.
An explicit tag, label, apply-classification, or set-type request authorizes
`mutation_mode=apply`; classify, categorize, recommend, suggest, preview, or
explain without an application request selects `dry-run`. Existing exact
metadata selections use the lifecycle branch directly.

A composed classification handoff needs an exact repository and issue identity
and canonical `mutation_mode`. It cannot import tracker, planning, or
orchestration policy. Classification authority permits adding supported labels
and setting one supported type only; it never permits removals or changes to
contextual fields or taxonomy.

Read [metadata-provider-reads.md](metadata-provider-reads.md) for the issue and
complete assignable catalogs before selecting values. Read relevant comments
and contextual fields only as evidence. Use `$g:github-investigation` when
selection requires code, root-cause, fix-quality, or acceptance evidence beyond
the issue text. Read [states.md](states.md) before returning or applying results.

## Catalog Boundaries

Build a fresh per-invocation snapshot. Do not cache repository or organization
metadata across issues or runs.

- Labels are repository-scoped. Preserve their exact provider-owned names and
  use descriptions as the primary statement of meaning.
- Native issue types are organization-scoped and singular on an issue. Only an
  enabled type that is currently assignable belongs in the candidate set.
- A missing issue-type capability, an empty type set, and a failed type-catalog
  read are different facts. Report which one was observed.
- Visible issue fields, milestone, assignees, projects, parent/sub-issue links,
  dependencies, and current workflow state may explain context but are outside
  this classification branch's mutation surface.
- Label color is presentation metadata. Never translate a color into severity,
  priority, status, or category.

## Evidence Order

Evaluate candidates in this order:

1. Explicit facts and requested outcome in the issue title and body.
2. Clarifications or corrections in relevant issue comments.
3. Exact label and type descriptions owned by the repository or organization.
4. Consistent use on a small set of clearly analogous issues when descriptions
   are absent or insufficient.
5. Candidate names as a final supporting signal, never as the only basis for a
   specialized workflow, priority, severity, ownership, or release label.

Later evidence cannot override a contradiction in earlier, stronger evidence.
Do not treat popularity, label color, or one superficially similar issue as a
classification rule.

## Selection

### Issue type

- Select at most one exact available type that describes the issue's primary
  kind of work.
- Selecting no type is correct when no available type is clearly pertinent.
- Keep the current type when it remains well supported.
- Replace a current type only when one available alternative is clearly better
  supported and the invocation authorizes application.
- If two or more types remain plausible, skip the type dimension and explain
  the ambiguity.

### Labels

- Select only labels that add independent information, such as an evidenced
  component, platform, domain, impact, or repository-defined workflow fact.
- Prefer the smallest set that materially improves categorization.
- Selecting no labels is correct when none of the available labels is
  pertinent.
- Preserve every existing label. Report a suspected contradiction but do not
  remove or replace it without a separate explicit lifecycle request.
- Avoid duplicating the selected issue type with an equivalent label unless
  descriptions or consistent repository usage show that dual assignment is
  intentional.
- Do not apply labels whose conditions require evidence absent from the issue,
  such as readiness, confirmed severity, ownership, release eligibility, or a
  verified root cause.

## Disposition

Set `classification_disposition` from the canonical registry in `states.md`:

- `complete-match` when every requested classification dimension has one clear
  supported result and there is no unresolved conflict;
- `partial-match` when at least one label or type is clear while another
  requested dimension is ambiguous, unavailable, or blocked;
- `no-confident-match` when the catalogs are readable but no exact value is
  justified;
- `no-available-metadata` when the relevant catalogs were read successfully and
  expose no assignable classification values;
- `metadata-unavailable` when no usable classification catalog can be proven
  because capability, access, or provider reads are indeterminate.

An unavailable type catalog with a usable label catalog yields `partial-match`
when type was requested. Record the skipped type dimension explicitly.

## Application

For authorized changes, read [lifecycle.md](lifecycle.md). Normalize missing
labels into one `issue_operation=add-label` operation and a changed type into
a separate `issue_operation=set-type` operation. These are internal operations
of this skill, not a second skill handoff. Re-read the issue and selected catalog
entries immediately before writes; after each receipt, independently read the
exact issue back. Reconcile an uncertain or partial failure before retrying and
never repeat a change already applied.

- In `dry-run`, return a proposal only and set `application_status=previewed`
  when at least one change is proposed.
- In `apply`, add only missing proposed labels and set the proposed type only
  when it differs. Apply an unambiguous subset from `partial-match` and report
  every skipped dimension.
- If all proposed values already match, make no write and use `unchanged`.
- Use `partially-applied` only after readback proves at least one requested
  change and another remains unapplied.
- Use `failed` only after readback proves that none of the attempted changes
  reached the target. An uncertain write remains unresolved until readback.
- Use `not-applicable` when there is no safe proposal to preview or apply.

## Drift And Recovery

Treat the issue text, current assignments, and catalog snapshot as one
classification input. If any of them changes before mutation, discard the
proposal and recompute it. After an ambiguous provider response, read the exact
issue before retrying. Never infer failure solely from a missing immediate
receipt, and never retry a label or type already visible on readback.

## Result Shape

Return a concise report with:

- exact repository, issue number, and URL;
- requested classification dimensions;
- catalog availability and candidate counts without dumping the full catalog
  unless requested;
- previous labels and type;
- proposed `add_labels` and `issue_type` values using exact provider spelling;
- one short issue-derived rationale per selected value;
- skipped dimensions and ambiguity or availability reasons;
- `classification_disposition` and `application_status`;
- independently read-back final labels and type for any apply run.
