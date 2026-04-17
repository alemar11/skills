# GitHub workflow behaviors

Use this file for decision policy shared by workflow scripts.

## Issue label suggestion policy

Goal: suggest labels for issue creation without mutating anything by default.

### Inputs

- `--title`: issue title text.
- `--body`: issue body text.
- target repo labels via `gh label list --json name,description`.

### Scoring rubric

- `title_exact_match` (0.60)
  - Add when the full normalized label token appears in the title text.
- `body_exact_match` (0.35)
  - Add when the full normalized label token appears in the body text.
- `description_relevance` (up to 0.20)
  - Add by normalized overlap between label description tokens and title/body tokens.
- `keyword_alias` (up to 0.25)
  - Add for common aliases present in title/body.

### New label fallback policy

- Resolve candidates from existing repo labels first and score them only from `--title` / `--body`.
- Only when existing-label candidates are absent (or below threshold) consider reusable, generic fallback candidates from a curated alias set (`bug`, `enhancement`, `documentation`, `tests`, `build`, `dependencies`, `chore`).
- Create fallback labels only when explicitly enabled and always with `gh label create --repo ...` (repo scope only).
- Never create non-reusable names (issue numbers, PR-specific names, one-off phrases, or mixed-context terms).
- Report creation outcome (`created` vs failure reason) with the same ranked output schema.

#### Suggested default aliases

- `bug`, `enhancement`, `documentation`, `docs`, `tests`, `test`, `build`, `ci`, `chore`.

#### Score normalization

- `score = min(1.0, title_exact_match + body_exact_match + description_relevance + keyword_alias)`.
- Return only labels with `score >= --min-score`.
- Return sorted by score descending, then name.

### Output contract

When suggestions are available, print or emit ranked list entries with:

- `name` (string)
- `score` (float 0..1)
- `reason` (short explanation)
- `source` (`title`, `body`, `description`, `alias`, or `combined`)
- `confidence` (`high|medium|low` based on score tiers)

### Decision rules

- Suggestions are informational only.
- Do not apply labels directly.
- Apply only after the user confirms selected labels.

## Commit issue-link policy

Goal: propose issue-close wording for commit intents.

### Candidate extraction sources

Evaluate candidate issue IDs from the strongest source to weakest:

- explicit argument `--issue-number`
- branch name pattern (for example `issue-123`, `gh-123`, `feature/issue-123`, `fix/123-something`)
- context text patterns (`#123`, `issue 123`, `fixes 123`, `close 123`, etc.)

### Resolution semantics

- If exactly one high-confidence candidate exists:
  - propose a close token using configured `--token`.
- If multiple candidates exist:
  - mark decision as ambiguous and request explicit user choice.
- If no candidate exists:
  - leave message unchanged and mark state as `no_candidate`.
- If an existing close token already exists in the message:
  - preserve message and mark `already_linked`.
  - allow execution because no extra close token needs to be added.

### Safety defaults

- Default token: `Fixes`.
- Never add a second close token if one already exists.
- Default mode is dry-run/preview; commit execution is only performed with `--execute`.
- Keep behavior repository-scoped and non-destructive unless explicitly executed.

## Star list selector policy

Goal: keep authenticated-user list targeting predictable across star and list flows.

### Resolution order

- Resolve `--list` by exact slug first.
- If no slug matches, resolve by exact name.
- If multiple exact name matches exist, require `--list-id`.
- If `--list-id` is provided, treat it as authoritative and do not fall back to name matching.

### Safety defaults

- Do not fuzzy match list selectors.
- Error on ambiguity instead of guessing.
- Treat list operations as authenticated-user scope and allow them outside a git checkout.

## Star list membership policy

Goal: preserve unrelated list memberships when adding or removing repositories from one list.

### Update semantics

- Read the repository's current list memberships first.
- Compute the full desired list id set after the add/remove request.
- Send the full desired set to `updateUserListsForItem`.
- Report per-repository `changed`, `noop`, `dry-run`, or `error` outcomes for batch runs.

### Safety defaults

- Batch assign and unassign flows are best-effort, not fail-fast.
- Assignment requires the repository to already be starred by the authenticated user.
- Unassigning a repository that is not starred is a no-op.

## Issue close evidence policy

Goal: close issues with traceable implementation proof.

### Required closure sequence

1. Verify issue is open.
2. Add a closure comment with implementation evidence.
3. Close the issue.

### Evidence format

- Commit evidence:
  - `Implemented in commit <short_sha> (<commit_url>).`
- PR evidence (when available):
  - `Implemented via PR <pr_url>.`
- Prefer both links when available.

### JSON field behavior note

- For issue metadata in `gh issue view --json`, do not use `projects`.
- Use `projectItems` and `projectCards`.
