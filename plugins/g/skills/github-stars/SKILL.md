---
name: github-stars
description: "List and manage the authenticated GitHub user’s stars and star lists."
---

# GitHub Stars

Read [network execution](../../references/network-execution.md) before provider
access. Use authenticated `gh` directly for inventory, ordinary stars, and list
deletion; use the shipped G helper only for list membership updates.

Read [workflows](references/workflows.md) for the requested operation. Before
assigning or unassigning list members, also read the
[membership helper contract](references/script-summary.md) and
[result states](references/states.md).

Resolve the host, authenticated account, and exact repository or list identities
before writes. Inspection and dry runs never mutate. An explicit star, unstar,
assignment, removal, or list-deletion request authorizes only that operation;
ask only when its target or scope remains ambiguous.

Report repository URLs, list names and IDs, observed outcomes, and incomplete
coverage or per-target failures. Do not present a write receipt as verified state.
