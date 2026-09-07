---
name: github-stars
description: "List and manage the authenticated GitHub user’s stars and star lists."
---

# GitHub Stars

Before any shell command that may contact GitHub or a package registry, read
and follow [Network execution](../../references/network-execution.md).

## Transport

Use `<plugin-root>/scripts/g stars`, backed by authenticated `gh`, for every
provider read and write in this skill.

Before the first provider-facing shared CLI operation, load
[`../../references/gh-dependency-preflight.md`](../../references/gh-dependency-preflight.md)
and require its host and authentication checks.

## Commands

Use `<plugin-root>/scripts/g stars --help` for syntax and
[workflows](references/workflows.md) for the selected operation.

## Workflow

1. Run the shared doctor with scoped network permission and require
   `authentication_status=verified` before private or authenticated-user
   operations.
2. Use list operations for inventory and search.
3. Confirm destructive actions such as unstar or list delete unless the user
   explicitly asked for them.
4. Return repository URLs and list names/ids in results.

## References

- `references/workflows.md`: star and star-list workflows.
- `references/script-summary.md`: `stars` command contract.
