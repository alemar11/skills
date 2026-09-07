# Issue Taxonomy Proposals

Read this reference only when an explicit user request requested
repository taxonomy analysis. This branch is read-only even when the
provider exposes taxonomy-management APIs.

Read [metadata-provider-reads.md](metadata-provider-reads.md) for catalogs and
issue-corpus access, and [states.md](states.md) for the result disposition. Use
`$g:github-investigation` when analysis requires deeper code or history evidence.
Do not derive `mutation_mode` or `issue_operation` for a read-only proposal.

## Target And Evidence Boundary

Resolve one exact repository before analysis. Label proposals are scoped to
that repository. Native issue-type proposals are scoped to its owning
organization; omit them for a personal repository.

Build a fresh evidence bundle from:

- the complete current repository label catalog and the organization's visible
  issue-type catalog, including disabled types when the provider exposes them;
- issue forms, issue templates, contribution guidance, repository description,
  architecture or ownership documentation, and stable component boundaries;
- a representative corpus of repository issues across open and closed state,
  recent and older work, existing metadata assignments, and issues with no
  labels or type;
- selected comments only when the issue body does not establish the intended
  category.

Exclude pull requests from the issue corpus. Prefer complete issue coverage
when the repository is small. For a large repository, use a stratified sample
and report the total visible corpus, the number examined, the selection method,
and any blind spots. If an exact matching local checkout is unavailable, use
provider-visible repository content and report the missing local evidence
instead of substituting another checkout.

Repository folder names, one unusual issue, label popularity, and current
assignee or milestone state are not sufficient evidence for a taxonomy entry.

## Gap Test

Propose a new taxonomy entry only when all of these are true:

1. Multiple distinct issues establish a recurring classification need.
2. No existing label or enabled type expresses the distinction accurately.
3. The distinction is stable enough to classify future issues.
4. Inclusion and exclusion boundaries can be stated clearly.
5. The candidate does not duplicate or ambiguously overlap an existing or
   disabled entry.

Prefer the smallest proposal set and return no proposal when the current
taxonomy is sufficient. Prefer a label for repository-specific component,
platform, domain, impact, or workflow distinctions. Consider a native issue
type only for an issue's primary kind of work when the distinction is likely to
remain meaningful across the organization. When repository-only evidence
cannot justify organization-wide scope, propose a label or mark the type
candidate as requiring organization-level validation.

Do not encode transient status, assignee, milestone, release, unverified
severity, or implementation detail as a new category. Do not propose a label
that merely duplicates an issue type unless repository evidence shows that the
two dimensions are intentionally independent.

## Proposal Shape

For every proposed label, return:

- exact proposed name using the repository's established naming convention;
- a concise description within the provider's current limit;
- a valid proposed color, treated only as presentation metadata;
- the recurring gap and representative issue URLs that support it;
- explicit inclusion and exclusion examples;
- collision and overlap checks against the current catalog;
- estimated coverage within the examined corpus.

For every proposed native issue type, return:

- exact proposed name, description, color, and intended enabled state;
- the organization-level category boundary;
- representative issue URLs and the repositories actually examined;
- why existing labels and types are insufficient;
- any missing organization-wide evidence or provider-limit concern.

Issue types are singular on an issue. Never propose overlapping types that
would require one issue to hold more than one.

## Mutation Boundary

Do not create, update, disable, delete, or assign labels or issue types from
this mode. Provider API availability and caller write permissions are reported
facts, not mutation authority.

A later explicit request may route an exact accepted label definition to
[lifecycle.md](lifecycle.md) as one `issue_operation=create-label` operation. Applying an
organization issue-type proposal is outside this workflow and requires a
separately owned, explicitly authorized organization-taxonomy operation. Never
improvise that write from a proposal.

## Result

Return:

- exact repository and owning organization, when any;
- issue-corpus coverage and repository sources examined;
- current label and type catalog availability;
- the minimal proposed label and issue-type definitions, which may both be
  empty;
- evidence, overlap checks, limitations, and creation-readiness per proposal;
- one `taxonomy_disposition` from `states.md`;
- an explicit statement that no taxonomy or issue metadata was mutated.
