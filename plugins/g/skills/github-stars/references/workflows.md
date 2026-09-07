# GitHub Stars Workflows

Use `gh auth status --hostname <host>` and `gh api --hostname <host> user` to
establish the acting account without printing tokens. Include the resolved host
in direct API calls; helper membership updates use the active authenticated host.

## Inventory

List the authenticated user's stars with `gh api --hostname <host> --paginate
'user/starred?per_page=100'`. Keep each repository's `full_name` and `html_url`.
Use the star media type only when timestamps are needed. A requested sample may
stop early, but report its limit and incomplete coverage; never treat failed or
missing pages as an empty inventory.

For star lists, query GraphQL `viewer.lists(first: 100, after: $endCursor)` with
connection `totalCount`, `pageInfo { hasNextPage endCursor }`, and nodes containing
`id`, `name`, `slug`, and `isPrivate`. For items, query the selected
`node(id: $id)` as `UserList`, then paginate its `items` connection and collect
repository IDs, `nameWithOwner`, and URLs. Paginate each connection independently;
`gh api graphql --paginate` requires the `$endCursor` variable and pageInfo.
Check GraphQL errors even when HTTP succeeds. Missing cursors or pages leave
coverage unknown and cannot establish absence or unique name resolution.

Use exact IDs for operations. Resolve an exact slug or name against the complete
viewer list inventory; ambiguous matches require an ID. Verify a supplied ID
belongs to that viewer. Never infer list identity from a partial title match.

## Star or unstar

Resolve each explicit `owner/repo` through `GET repos/{owner}/{repo}` and preserve
the canonical identity. Check `GET user/starred/{owner}/{repo}`: 204 means starred;
404 means unstarred only after account and repository access are established.
Other failures leave state unknown.

For an authorized change, use `PUT user/starred/{owner}/{repo}` to star or `DELETE`
on that endpoint to unstar, with an explicit `gh api --method`. Already-correct
state is a no-op. A dry run reports the target and intended change after reads,
without issuing the write. Independently repeat the status check after a write.
After an ambiguous response, reconcile that status before retrying.

For batches, deduplicate canonical repositories and retain per-target outcomes;
report changed, already-correct, previewed, failed, and unresolved targets without
claiming the entire batch succeeded. Unstarring can remove list memberships;
do not silently recreate them or substitute unstar for removal from one list.

## Delete a list

Resolve its exact ID in the complete viewer list inventory. For explicit deletion,
submit GraphQL `deleteUserList(input: {listId: $listId})`; use a file-backed query
and variables when constructing the request. A dry run stops after showing the
resolved name and ID. Requery the viewer's complete list inventory to verify its
absence. A failed read or GraphQL error cannot prove deletion. Reconcile an
ambiguous write before retrying. Deleting a list does not authorize unstarring
its repositories.

## Assign or unassign list members

Use the [membership helper](script-summary.md), which reads all existing list
memberships before replacing the set. Assignment never implicitly stars a
repository. Preserve every unrelated membership. Independently read the affected
repository's memberships after the command and compare the complete desired set;
a successful helper receipt alone does not prove readback. Reconcile uncertain
outcomes before retrying, using fresh memberships rather than a stale set.

## Provider references

- [GitHub REST starring](https://docs.github.com/en/rest/activity/starring)
- [GitHub GraphQL reference](https://docs.github.com/en/graphql/reference)
- [gh api pagination and file-backed inputs](https://cli.github.com/manual/gh_api)
