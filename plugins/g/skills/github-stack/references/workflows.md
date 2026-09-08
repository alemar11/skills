# Stacked PR workflows

Use the shipped artifact, never the upstream command directly:

```bash
<plugin-root>/scripts/g --json stack <command> [args...]
```

Run the network preflight and extension readiness checks from `SKILL.md` first.
Use `--json` when the result will be inspected or handed to another workflow.

## Create or adopt a stack

Plan the dependency order before creating branches. The first branch is closest
to the trunk and later branches depend on the earlier ones.

```bash
<plugin-root>/scripts/g --json stack init --base main api-layer ui-layer
<plugin-root>/scripts/g --json stack view --json
```

Use `add <branch>` to add one cohesive layer on top of the current stack. Use
ordinary Git staging and commits for deliberate scope; do not use `add -Am` as
the default when changes need to be split.

To adopt an existing remote stack locally, use an explicit target:

```bash
<plugin-root>/scripts/g --json stack checkout <stack-number-or-pr-or-url>
```

If local and remote tracking disagree, do not answer an interactive prompt.
Remove only local tracking with `unstack --local`, inspect the remote state,
then retry checkout if the user still wants adoption.

## Link existing PRs

Use `stack link` when the PRs already exist or when an external branch tool owns
the local branch lifecycle. Arguments are bottom-to-top:

```bash
<plugin-root>/scripts/g --json stack link <bottom-pr> <top-pr>
```

Consume the exact PR identities and publication readbacks from the caller when
available. Verify both repositories, the child base, both full heads, and the
intended bottom-to-top order before treating the link receipt as authoritative.
This is distinct from `send`: `send` owns the current branch publication, while
this skill owns the explicit parent/current relationship. Do not use `link` to
guess a stack from branch names or ambiguous PRs.

Linking existing PRs can create a remote stack without local tracking. In that
case, `view --json` cannot inspect it from the current branch. Verify the remote
relationship through authenticated `gh` by reading each PR's stack identity and
the complete ordered entries, including full heads and PR bases. Missing local
tracking is not evidence that linking failed; do not repeat the link or create
another stack. Use `checkout <exact-stack>` only when local adoption is needed
and the owning worker has preserved its current work. Local base refs may lag
the remote PR base; report and verify them separately.

## Publish a complete stack

Use this only when the user explicitly requests multi-branch publication:

```bash
<plugin-root>/scripts/g --json stack submit --auto
```

Add `--open` only when the user explicitly wants new or existing PRs marked
ready for review. Without `--open`, preserve the extension's default draft
behavior. `submit` pushes active branches and creates or updates multiple PRs;
it is not atomic and may leave earlier branches published if a later push fails.

Do not use this path for a normal `$g:send` request. It does not create
the Send-owned issue linkage, body verification, draft-preservation evidence,
or the one-branch publication evidence.

## Modify a middle layer

When a higher branch reveals a missing lower-layer change:

1. Navigate explicitly with `down`, `bottom`, or `checkout <branch-or-pr>`.
2. Make and commit the change on the branch where it logically belongs.
3. Rebase dependents with `rebase --upstack`.
4. Inspect with `view --json`.
5. Push the updated active branches with `push` when explicitly requested.

This keeps unrelated lower-layer changes out of the higher PR and makes the
review sequence reflect the dependency chain.

## Sync after upstream or merge changes

Use `sync` for routine stack reconciliation after trunk changes or a merged
lower PR:

```bash
<plugin-root>/scripts/g --json stack sync
```

It may fetch, fast-forward the trunk, cascade rebases, push active branches,
update PR state, and update the remote stack. It can also replay remaining
branches after a squash merge. Because it affects the whole stack, announce
the scope before running it. Use `--prune` only when deleting local branches
for merged PRs is part of the request.

If local and remote stack definitions diverge, stop on the non-interactive
abort and report both states. Do not force a replacement or recreate the stack
without explicit direction.

## Rebase conflicts

Start or narrow a rebase explicitly:

```bash
<plugin-root>/scripts/g --json stack rebase
<plugin-root>/scripts/g --json stack rebase --upstack
```

On a conflict, inspect the reported files, resolve the conflict, stage the
resolved files with `git add`, and continue:

```bash
<plugin-root>/scripts/g --json stack rebase --continue
```

If resolution is not safe or the user withdraws the operation:

```bash
<plugin-root>/scripts/g --json stack rebase --abort
```

Never claim the stack was pushed or synchronized until a subsequent `view
--json` or equivalent readback confirms the resulting branch and PR heads.

## Merge and teardown

Use the explicit stack target and confirmation flag:

```bash
<plugin-root>/scripts/g --json stack merge <pr-or-stack-number> --yes
```

Choose `--squash`, `--rebase`, or `--merge` only when requested. Stack merge is
all-or-nothing at the stack operation level, but repository rules and merge
queues still control final GitHub behavior.

To remove grouping before restructuring, use remote `unstack <stack-number>`;
to keep the GitHub grouping and remove only local tracking, use
`unstack --local`. Unstacking does not delete the underlying PRs or branches,
but remote unstack is still a GitHub mutation and requires explicit authority.
