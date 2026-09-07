# GitHub Repository Triage Workflows

## Queue Snapshot

```bash
gh repo view <owner/repo> --json nameWithOwner,url,defaultBranchRef
gh issue list --repo <owner/repo> --state open --limit 50 --json number,title,author,labels,createdAt,updatedAt,url
gh pr list --repo <owner/repo> --state open --limit 50 --json number,title,author,isDraft,reviewDecision,mergeStateStatus,statusCheckRollup,createdAt,updatedAt,url
```

Report URLs first, then the reason each item matters. Prefer categories such as
blocked, stale, needs review, needs CI, and needs owner input.

## Item Inspection

```bash
gh issue view <number> --repo <owner/repo> --json number,title,body,author,labels,assignees,comments,url
gh pr view <number> --repo <owner/repo> --json number,title,body,author,isDraft,reviewDecision,mergeStateStatus,statusCheckRollup,comments,url
```

Inspect only enough detail to make the triage recommendation. Avoid broad
historical reads unless the user asks for a deep queue audit.

## Multiple repository comparison

Accept explicit repository identities or a user-supplied file containing one
`owner/repo` per line. Ignore blank lines and `#` comments; validate identities
and resolve their host before issuing commands. Do not discover additional
repositories from organizations, stars, or unrelated local checkouts.

Apply the queue reads above independently to each selected repository with
explicit `--repo`. For a recent CI/release comparison, add:

```bash
gh run list --repo <owner/repo> --limit 10 --json databaseId,headSha,status,conclusion,url,createdAt
gh release list --repo <owner/repo> --limit 10 --json tagName,isDraft,isPrerelease,publishedAt
```

Report each repository's URL, queue sizes with their coverage, sampled CI
failures or pending runs, latest relevant release, and evidence-backed next
action. Retrieve the selected release's URL if it is part of the report.
Keep no-release evidence distinct from an unreadable release endpoint; an old
release alone does not prove a release gap without relevant commits or policy.

The `--limit` commands produce samples. State the limits and filters; when an
inventory reaches its limit, report at least that many items unless a provider
total is available. For exact counts or an exhaustive audit, read provider
connection totals or paginate all issue and pull-request pages with `gh api`.
GraphQL pagination requires `pageInfo { hasNextPage endCursor }` and an
`$endCursor` variable; REST pagination follows every next-page link. The REST
issues endpoint includes PRs, which must be excluded from issue counts.

Preserve unavailable repositories and individual failed reads alongside
successful evidence from the others. Identify the failed surface and resulting
coverage gap; do not substitute zero counts or healthy CI. Queue summaries do
not establish exact-head merge readiness; use `$g:github-delivery-status` when
that conclusion is needed.

See [gh API pagination](https://cli.github.com/manual/gh_api).

## Focused Follow-Up Routing

Never mutate as a side effect of a read-only triage request. Route GitHub issue
creation, type changes, comments, labels, parent/sub-issue relationships, and
closure to `$g:github-issues` with `mutation_mode=apply`, the exact
repository and issue target, and one matching `issue_operation` only after the
user authorizes that write. Use `mutation_mode=dry-run` only when the user asks
to preview a specific write-shaped operation. Pure queue reads omit
`mutation_mode` and an operation field.

Route evidence-backed issue disposition, acceptance, or closure judgment to
`$g:github-investigation`. Route PR review-thread replies to
`$g:github-review-threads` with the exact repository and PR,
`review_operation=reply`, and `mutation_mode=apply`. For read-only inspection,
use `review_operation=inspect` and omit mutation authority.
