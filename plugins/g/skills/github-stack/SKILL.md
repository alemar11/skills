---
name: github-stack
description: "Manage stacked Git branches and dependent pull requests through the G stack CLI."
---

# GitHub Stack

Before any shell command that may contact GitHub or a package registry, read
and follow [Network execution](../../references/network-execution.md).

## Role

Use this skill for stack-level work through `<plugin-root>/scripts/g
stack ...`. The wrapper delegates stack state, branch ordering, PR linking,
rebasing, synchronization, and merge behavior to the official
`github/gh-stack` extension while enforcing non-interactive invocation.

Resolve `<plugin-root>` as two directories above this `SKILL.md`. Read
[`../../references/stack-cli.md`](../../references/stack-cli.md) before using
the command surface, load
[`../../references/gh-dependency-preflight.md`](../../references/gh-dependency-preflight.md)
for the scoped `gh` and `gh-stack` readiness gate, and load
[`references/workflows.md`](references/workflows.md) for the requested lifecycle
operation.

## Boundaries

- Use `$g:send` for publishing or updating one PR, including its title,
  body, closing issue references, draft state, and push ownership.
- Use this skill for an explicit parent/child link, even when the PRs were just
  published by `$g:send`. `send` does not infer or invoke `stack link`; do not
  replace this explicit relationship flow with `stack submit`.
- Use this skill when the user explicitly asks for stack-wide publication,
  navigation, rebase, sync, restructuring, merge, or recovery.
- Do not silently turn a single-PR request into a stack-wide operation.
- `stack submit` is an explicit multi-branch publication mode. It does not
  inherit `send`'s issue-linkage, body, or draft-preservation contract; route
  those responsibilities separately when required.

## Readiness and authorization

1. Resolve the repository and plugin root.
2. Load and pass the shared `gh` dependency preflight. It owns the host CLI,
   authenticated-provider, and exact `github/gh-stack` checks.
3. If the extension is missing, stop and report the prerequisite. Run
   `g --json stack ensure --install` only after the user explicitly
   authorizes installing `github/gh-stack`.
4. Never fall back silently to an ordinary unstacked PR workflow when stack
   state is unavailable, ambiguous, or unsupported.
5. Treat `push`, `submit`, `sync`, `rebase`, `merge`, and remote `unstack` as
   separate mutations. Explain their scope before executing them.

## Non-interactive rules

Always supply the positional arguments and flags required by the wrapper:

- `init`, `add`, and `checkout` require an explicit branch, stack, PR, or URL;
- `view` requires `--json`;
- `submit` requires `--auto`;
- `merge` requires an explicit target and `--yes`;
- remote `unstack` requires an explicit target; use `unstack --local` for local
  tracking only.

Never invoke blocked interactive commands such as `modify`, `switch`, `alias`,
or `feedback`. Do not use the raw escape hatch unless the typed surface cannot
express an explicitly requested non-interactive operation.

## Core operating rules

- Model the stack from trunk upward: foundational changes belong in lower
  branches and dependent changes in higher branches.
- Keep each branch a cohesive, independently reviewable unit.
- When changing a lower or middle branch, work on that branch, commit there,
  then run `rebase --upstack` before returning to the higher branch.
- Use `view --json` for a locally tracked stack; remote-only links use the
  relationship readback in `references/workflows.md`. Verify before and after
  consequential operations and preserve exact branch/PR state in the handoff.
- For conflicts, resolve and stage files, then use `rebase --continue`; use
  `rebase --abort` to restore the pre-rebase state.
- After a lower PR merges, use `sync` to fetch, reconcile, rebase, push, and
  update stack state. Use `--prune` only when local merged branches should be
  removed.
- Merge stacks only with `stack merge ... --yes`; do not substitute
  `gh pr merge`.
