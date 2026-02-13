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

### Safety defaults

- Default token: `Fixes`.
- Never add a second close token if one already exists.
- Default mode is dry-run/preview; commit execution is only performed with `--execute`.
- Keep behavior repository-scoped and non-destructive unless explicitly executed.
