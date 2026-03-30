# GitHub issue workflows

Use this reference when the task involves issue state changes, implementation
updates, or cross-repo transfer behavior.

## issue-close-with-evidence

Purpose: close an issue after implementation work is complete and the issue
should no longer remain open.

### Operator policy

- Follow this sequence:
  1. verify the issue state is open,
  2. gather implementation evidence,
  3. post a concise closure note,
  4. close the issue.
- Prefer the dedicated helper script over manual `gh issue comment` plus
  `gh issue close` sequences.

### Preferred helper

```bash
scripts/issues_close_with_evidence.sh --issue <number> --commit-sha <sha> [--commit-url <url>] [--pr-url <url>] [--repo <owner/repo>] [--allow-non-project] [--dry-run]
```

### Closure note template

- `Implemented in commit <short_sha> (<commit_url>).`
- `Implemented via PR <pr_url>.`
- Prefer including both commit and PR links when available.

## issue-implementation-update

Purpose: record that work was implemented or prepared while keeping the issue
open.

### Operator policy

- Follow this sequence:
  1. verify the issue state is open,
  2. gather implementation evidence,
  3. post a concise update comment,
  4. leave the issue open unless the user explicitly asks to close it.
- Until a dedicated helper exists, prefer:
  - `gh issue comment <number> --repo <owner/repo> --body-file <file>`
  - `gh issue comment <number> --repo <owner/repo> --body <text>`
- Keep operational follow-up steps explicit and separate from the
  implementation evidence.

### Standard implementation-update comment shape

- short lead-in stating the work was implemented or prepared
- what has been done
- implementation evidence:
  - branch name when useful
  - commit SHA or commit URL
  - PR URL when available
- validation run, if relevant
- manual follow-up or rollout steps, if any

### Example evidence lines

- `Implemented on branch <branch>.`
- `Implemented in commit <short_sha> (<commit_url>).`
- `Draft PR: <pr_url>.`
- `For existing databases, run:`
- fenced SQL block when schema catch-up is required

## issue-transfer

Purpose: continue issue work in another repository while preserving the right
backlinks and source-state behavior.

### Operator policy

- Prefer `scripts/issues_copy.sh` when the source issue should stay open and
  work should continue in both places.
- Prefer `scripts/issues_move.sh` when work should continue only in the target
  repository.

### Standard target-body notes

- Copies: `Copied from <source_repo>#<issue> (<source_url>).`
- Moves: `Moved from <source_repo>#<issue> (<source_url>).`

### Standard source backlink comment for moves

- `Moved to <target_repo>#<new_issue> (<new_url>). Continuing work there.`

### Standard move behavior

1. create the target issue,
2. add the backlink comment on the source issue,
3. close the source issue if it is still open.

## gh-issue-view-json-field-pitfalls

- `gh issue view --json projects` is invalid and returns
  `Unknown JSON field: "projects"`.
- Use `projectItems` and/or `projectCards` instead.
- If fields are uncertain, run once with an intentionally invalid field and
  use the CLI's returned `Available fields` list.
