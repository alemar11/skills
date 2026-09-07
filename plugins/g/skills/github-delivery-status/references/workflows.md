# Delivery Status Collection

## Bind the observation

Resolve the exact GitHub host, `owner/repository`, and PR number from the
request or verified local remote. Use the same host for every `gh api` call.
Run the shared gh preflight without installing tools or changing credentials.

Use [snapshot.graphql](snapshot.graphql) to read identity, full HEAD, base,
lifecycle, mergeability, review decision, repository merge settings, and PR
automation. Record the start time and HEAD. With variables supplied as typed
arguments, the file-backed request is:

```sh
gh api graphql --hostname HOST -F query=@SNAPSHOT_FILE \
  -f owner=OWNER -f repo=REPOSITORY -F number=PR_NUMBER
```

Check both the process result and GraphQL `errors`; partial `data` is not a
complete success. A missing repository/PR or unreadable identity cannot support
a readiness result. An expected-head mismatch is `blocked`; do not silently
replace the caller's candidate. A closed/merged PR ends inspection with its
lifecycle; do not continue delivery or post-merge work.

## Collect current gates

Read each paginated connection separately with the same owner, repo, and number
variables, using `gh api graphql --paginate --slurp` and `-F query=@QUERY_FILE`:

- [checks.graphql](checks.graphql): every check run and commit status, its
  provider state, link, and app identity.
- [threads.graphql](threads.graphql): every review thread and resolution state.
- [closing-issues.graphql](closing-issues.graphql): every closing issue reference.

Each query owns one `$endCursor` and `pageInfo`. Require the final page to
report `hasNextPage=false`; a missing/repeated cursor, failed page, malformed
connection, GraphQL error, or early output limit means incomplete collection.
Keep each page's full HEAD and reject mixed-head pages. A valid null status
rollup means no reported checks; missing or errored data does not. Keep both
same-name check runs and statuses; do not deduplicate by name.

Read the target base branch's policy through explicit REST GET requests:

| Surface | Endpoint |
| --- | --- |
| Active rules, all pages | `repos/OWNER/REPOSITORY/rules/branches/ENCODED_BASE?per_page=100` |
| Each active rule's ruleset and visible bypass actors | `repos/OWNER/REPOSITORY/rulesets/RULESET_ID?includes_parents=true` |
| Classic protection | `repos/OWNER/REPOSITORY/branches/ENCODED_BASE/protection` |

Percent-encode the entire base branch as one path segment. Use `--paginate`
for active rules and retain page boundaries or coverage evidence. Follow the
provider's pagination rather than assuming the first 100 rules are exhaustive.
Malformed responses and inaccessible endpoints are unavailable evidence, not
empty policy. Distinguish a provider-confirmed unprotected branch from an
ambiguous 404 or authorization failure. Record a failed optional ruleset-detail
read without discarding already verified active rules.

## Close and interpret the observation

Repeat the snapshot after the connections and policy reads. Require the same
repository, PR, full HEAD, and base throughout. If they changed, discard the
combined evidence; recollect once for general inspection, or report the caller's
candidate stale. Continued drift is an incomplete observation, not readiness.
If lifecycle, review decision, or merge state changed materially, reconcile the
affected gates before classifying; there is no atomic provider snapshot.

Apply [states.md](states.md), preserving raw values and the observation time.
Keep repository auto-merge capability, this PR's existing auto-merge request,
and queue entry separate from readiness and authority. Include supported merge
methods and viewer permission only when useful; neither proves bypass rights.

For incomplete evidence, name the unavailable surface and resulting limit.
For pending gates, leave any later observation to the caller's bounded monitor.
For transport/authentication failure, distinguish provider rejection from
inconclusive network failure and rerun only the relevant preflight. Never
install tools, change credentials, or mutate the PR to make a read succeed.

Provider query fields and pagination are documented in the
[GitHub pull-request schema](https://docs.github.com/en/graphql/reference/pulls)
and [gh api manual](https://cli.github.com/manual/gh_api).
