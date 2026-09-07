# Issue Metadata Provider Reads

Read this reference after the shared GitHub CLI dependency preflight has
succeeded. These commands are read-only and do not authorize later mutations.

## Resolve The Target

Confirm the exact repository and whether its owner is an organization:

```sh
gh repo view --repo <owner>/<repo> \
  --json nameWithOwner,isInOrganization,owner,url
```

Read the exact issue and its current context. Keep `issueType` in the field
list; `type` is not a valid issue-view field.

```sh
gh issue view <number-or-url> --repo <owner>/<repo> --comments \
  --json number,title,body,state,url,updatedAt,labels,issueType,milestone,assignees,projectItems,parent,subIssues,blockedBy,blocking
```

Reject a pull request or any provider result whose repository and issue
identity do not match the resolved target.

## Read The Label Catalog

```sh
gh label list --repo <owner>/<repo> --limit 1000 \
  --json name,description,color
```

If the result reaches the requested limit and completeness cannot be proven,
report the label catalog as incomplete rather than assuming that the final page
was reached. Preserve exact names; descriptions may be absent.

## Read The Native Type Catalog

Native issue types belong to organizations. For a personal repository, report
the type capability as unavailable and do not call an organization endpoint.
For an organization repository, read the current catalog:

```sh
gh api "orgs/<org>/issue-types"
```

Use only exact names and descriptions returned by the provider. A not-found or
permission response does not prove an empty catalog. Report the type catalog
as unavailable, continue with usable labels, and derive the overall disposition
from [states.md](states.md) and the selected branch. Do
not expand OAuth scopes or change authentication unless the user separately
authorizes that credential mutation.

## Read Taxonomy Proposal Evidence

For an explicit taxonomy proposal, collect a bounded open-and-closed issue
corpus after resolving the exact repository:

```sh
gh issue list --repo <owner>/<repo> --state all --limit <bounded-count> \
  --json number,title,body,state,url,createdAt,updatedAt,labels,issueType
```

Exclude pull requests and preserve the returned count and any truncation
evidence. If the requested limit is reached, report the total corpus as unknown
and do not claim complete coverage. Select and read additional exact issues or
comments only when needed to validate a candidate category. Reuse the label and
native type catalog reads above for collision checks; for proposal work,
include disabled issue types when the provider returns them so they are not
proposed again under a new name.

The provider may expose organization-level issue-type creation and maintenance
APIs. This reference intentionally defines no taxonomy write command: proposal
mode must not use those APIs.

Repository evidence from an exact matching local checkout is read locally. If
there is no matching checkout, use supported provider file reads or report the
missing evidence; do not clone a repository or substitute a different checkout
without separate authority.

## Readback

After an authorized metadata operation, repeat the exact issue read without
reusing the pre-write response. Verify label names and `issueType` from the new
provider observation before assigning a terminal application status.
