# GitHub workflow templates

Use this section for copy-paste, branch-safe operational flows.

## pr-comment-address

Purpose: process pull-request comments for the PR associated with the current branch:
open PR resolution, fetch conversation/review/thread context, summarize with selection, apply selected follow-ups.

### Preconditions

- `gh` installed and authenticated.
- Repository scope resolves (`gh repo view` works).
- Current branch has an open PR unless `{pr_number}` is explicitly provided.
- Optional: `jq` if you want to inspect generated JSON manually.

## Paste and run (Phase 1): resolve context

```bash
#!/usr/bin/env bash
set -euo pipefail

REPO="{repo}"
PR_NUMBER="{pr_number}"

if ! gh auth status >/tmp/gh-pr-workflow-auth.txt 2>&1; then
  cat /tmp/gh-pr-workflow-auth.txt
  echo "Run: gh auth login"
  exit 2
fi

if [[ "$REPO" == "{repo}" || -z "${REPO}" ]]; then
  REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
fi

if [[ "$PR_NUMBER" == "{pr_number}" || -z "${PR_NUMBER}" ]]; then
  BRANCH="$(git rev-parse --abbrev-ref HEAD)"
  PR_NUMBER="$(gh pr list --repo "$REPO" --state open --head "$BRANCH" --json number --jq '.[0].number' || true)"
fi

if [[ -z "${PR_NUMBER}" || "$PR_NUMBER" == "null" ]]; then
  echo "No open PR found for branch '$BRANCH' in $REPO."
  echo "Supply {pr_number}, or run:"
  echo "  gh pr list --repo \"$REPO\" --state open"
  exit 1
fi

WORKDIR="/tmp/gh-pr-comment-workflow-${REPO//\//-}-${PR_NUMBER}"
mkdir -p "$WORKDIR"
{
  echo "REPO=$REPO"
  echo "PR_NUMBER=$PR_NUMBER"
  echo "WORKDIR=$WORKDIR"
} > "$WORKDIR/context.env"
echo "Context saved to $WORKDIR/context.env"
cat "$WORKDIR/context.env"
```

## Paste and run (Phase 2): fetch comment and thread context

```bash
#!/usr/bin/env bash
set -euo pipefail

WORKDIR="{workdir}"
if [[ "$WORKDIR" == "{workdir}" ]]; then
  echo "Replace {workdir} with the value printed by Phase 1."
  exit 1
fi
if [[ ! -f "$WORKDIR/context.env" ]]; then
  echo "Missing context file: $WORKDIR/context.env"
  exit 1
fi
source "$WORKDIR/context.env"

gh api "repos/$REPO/pulls/$PR_NUMBER/comments" --paginate --jq '.' > "$WORKDIR/review_comments.json"
gh api "repos/$REPO/issues/$PR_NUMBER/comments" --paginate --jq '.' > "$WORKDIR/conversation_comments.json"

OWNER="${REPO%%/*}"
REPO_NAME="${REPO##*/}"
cat > "$WORKDIR/review_threads.graphql" <<'GRAPHQL'
query($owner: String!, $repo: String!, $number: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          isOutdated
          path
          line
          startLine
          comments(first: 100) {
            nodes {
              id
              body
              createdAt
              updatedAt
              author { login }
            }
          }
        }
      }
    }
  }
}
GRAPHQL

gh api graphql \
  -f owner="$OWNER" \
  -f repo="$REPO_NAME" \
  -F number="$PR_NUMBER" \
  -f query="$(cat "$WORKDIR/review_threads.graphql")" \
  --jq '.data.repository.pullRequest.reviewThreads.nodes' \
  > "$WORKDIR/review_threads.json"
```

## Paste and run (Phase 3): build compact numbered digest

```bash
#!/usr/bin/env bash
set -euo pipefail

WORKDIR="{workdir}"
if [[ "$WORKDIR" == "{workdir}" ]]; then
  echo "Replace {workdir} with the value printed by Phase 1."
  exit 1
fi
source "$WORKDIR/context.env"

python3 - "$WORKDIR" <<'PY'
import json, sys

workdir = sys.argv[1]

conversation = json.load(open(f"{workdir}/conversation_comments.json"))
review_comments = json.load(open(f"{workdir}/review_comments.json"))
review_threads = json.load(open(f"{workdir}/review_threads.json"))

entries = []
index = 1

def _author(item):
    if isinstance(item.get("user"), dict):
        return item["user"].get("login", "")
    if isinstance(item.get("author"), dict):
        return item["author"].get("login", "")
    return ""

def _snippet(text):
    text = (text or "").replace("\n", " ").strip()
    return text[:220] + ("..." if len(text) > 220 else "")

for item in conversation:
    entries.append({
        "index": index,
        "comment_id": item.get("id"),
        "type": "conversation_comment",
        "author": _author(item),
        "updated": item.get("updated_at") or item.get("updatedAt") or "",
        "body": _snippet(item.get("body")),
    })
    index += 1

for item in review_comments:
    entries.append({
        "index": index,
        "comment_id": item.get("id"),
        "type": "review_comment",
        "author": _author(item),
        "updated": item.get("updated_at") or item.get("updatedAt") or "",
        "body": _snippet(item.get("body")),
    })
    index += 1

for thread in review_threads:
    for item in thread.get("comments", {}).get("nodes", []):
        entries.append({
            "index": index,
            "comment_id": item.get("id"),
            "type": "review_thread_comment",
            "author": _author(item),
            "updated": item.get("updatedAt") or "",
            "body": _snippet(item.get("body")),
            "path": thread.get("path"),
            "line": thread.get("line"),
            "startLine": thread.get("startLine"),
            "is_resolved": thread.get("isResolved"),
            "is_outdated": thread.get("isOutdated"),
        })
        index += 1

with open(f"{workdir}/comment_rollup.json", "w", encoding="utf-8") as f:
    json.dump(entries, f, indent=2)

for item in entries:
    print(f"[{item['index']:>3}] {item['type']} id={item['comment_id']} author={item['author']} updated={item['updated']}")
    print(f"      {item['body']}")
    if item["type"] == "review_thread_comment":
        print(f"      file={item.get('path')} line={item.get('line')} startLine={item.get('startLine')} resolved={item.get('is_resolved')} outdated={item.get('is_outdated')}")
print()
print("Paste selected row numbers into {selection_input}, for example: 1,3,7")
PY
```

## Paste and run (Phase 4): apply selected follow-ups

```bash
#!/usr/bin/env bash
set -euo pipefail

WORKDIR="{workdir}"
if [[ "$WORKDIR" == "{workdir}" ]]; then
  echo "Replace {workdir} with the value printed by Phase 1."
  exit 1
fi
if [[ ! -f "$WORKDIR/context.env" ]]; then
  echo "Missing context file: $WORKDIR/context.env"
  exit 1
fi
source "$WORKDIR/context.env"

SELECTION_INPUT="{selection_input}"
COMMENT_IDS="{comment_ids}"
RESPONSE_BODY="${response_body:-"Thanks, I will fix this and update the PR."}"

if [[ "$COMMENT_IDS" == "{comment_ids}" || -z "$COMMENT_IDS" ]]; then
  if [[ "$SELECTION_INPUT" == "{selection_input}" || -z "$SELECTION_INPUT" ]]; then
    echo "Provide either {selection_input} (row numbers) or {comment_ids}."
    exit 1
  fi
  COMMENT_IDS="$(python3 - "$WORKDIR" "$SELECTION_INPUT" <<'PY'
import json, sys

workdir, raw = sys.argv[1], sys.argv[2]
idx_to_id = {str(item["index"]): item["comment_id"] for item in json.load(open(f"{workdir}/comment_rollup.json"))}
selected = [x.strip() for x in raw.replace(",", " ").split() if x.strip()]
ids = [idx_to_id[s] for s in selected if s in idx_to_id]
if not ids:
    raise SystemExit("No valid selection indices found.")
print(",".join(ids))
PY
)"
fi

for COMMENT_ID in ${COMMENT_IDS//,/ }; do
  KIND="$(python3 - "$WORKDIR" "$COMMENT_ID" <<'PY'
import json, sys
rows = json.load(open(f"{sys.argv[1]}/comment_rollup.json"))
target = sys.argv[2]
for item in rows:
    if item["comment_id"] == target:
        print(item["type"])
        break
PY
)"

  case "$KIND" in
    conversation_comment)
      # Follow-up only (safe default; does not require direct issue-comment patch permissions).
      gh pr comment "$PR_NUMBER" --repo "$REPO" --body "$RESPONSE_BODY (ref: $COMMENT_ID)"
      ;;
    review_comment|review_thread_comment)
      # Try thread reply endpoint first, fallback to PR-level follow-up.
      if ! gh api -X POST "repos/$REPO/pulls/comments/$COMMENT_ID/replies" -f body="$RESPONSE_BODY" >/dev/null; then
        gh pr comment "$PR_NUMBER" --repo "$REPO" --body "$RESPONSE_BODY (ref: $COMMENT_ID)"
      fi
      ;;
    *)
      echo "Unknown comment ID in rollup: $COMMENT_ID"
      ;;
  esac
done
```

### Workflow note

This is intentionally a template, not an all-in-one automation.
If you want to promote this into a script, the next iteration is a dedicated `scripts/prs_address_comments.sh` that accepts `--pr`, `--selection`, `--repo`, and optional `--comment-ids`.

## fix-ci

Purpose: inspect PR check failures, fetch run metadata/log snippets, and provide next actions.

### Preconditions

- `gh` installed and authenticated.
- Repository scope resolves (`gh repo view` works in the target repo path).
- Current branch has an open PR unless `{pr}` is explicitly provided.
- `{json}` can be set to `true` to force machine-readable output for automation.

### Paste and run (Phase 1): auth + PR resolution

```bash
#!/usr/bin/env bash
set -euo pipefail

# Replace placeholders:
# {skill_dir} : path to this skill folder (for example /path/to/.codex/skills/custom/github)
# {repo}      : optional repo path (defaults to current directory repo)
# {pr}        : optional PR number or URL
SCRIPT_PATH="{skill_dir}/scripts/inspect_pr_checks.py"
REPO="{repo}"
PR_INPUT="{pr}"

if [[ "$SCRIPT_PATH" == "{skill_dir}/scripts/inspect_pr_checks.py" ]]; then
  SCRIPT_PATH="scripts/inspect_pr_checks.py"
fi
if [[ "$REPO" == "{repo}" || -z "$REPO" ]]; then
  REPO="."
fi
if [[ "$PR_INPUT" == "{pr}" ]]; then
  PR_INPUT=""
fi

if ! gh auth status >/tmp/gh-fix-ci-auth.txt 2>&1; then
  cat /tmp/gh-fix-ci-auth.txt
  echo "Run: gh auth login"
  exit 2
fi

if [[ "$REPO" != "." ]]; then
  cd "$REPO"
fi

if ! gh repo view >/tmp/gh-fix-ci-repo.txt 2>&1; then
  echo "Error: repository context not resolvable from REPO path '$REPO'."
  echo "Resolve by running in a checked-out repository or passing a valid path to --repo."
  cat /tmp/gh-fix-ci-repo.txt 2>/dev/null || true
  exit 3
fi

if [[ -n "$PR_INPUT" ]]; then
  echo "Resolved PR override: $PR_INPUT"
else
  echo "Resolved PR: current branch (if an open PR exists)"
fi
echo "Repository: $(gh repo view --json nameWithOwner -q .nameWithOwner)"
```

### Paste and run (Phase 2): fetch checks + run metadata + logs

```bash
#!/usr/bin/env bash
set -euo pipefail

# Replace placeholders:
# {skill_dir} : path to this skill folder (for example /path/to/.codex/skills/custom/github)
# {repo}      : optional repo path (defaults to current directory repo)
# {pr}        : optional PR number or URL
# {max_lines} : number of log lines in snippet (default: 160)
# {context}   : context lines around failure marker (default: 30)
# {json}      : true for machine output
SCRIPT_PATH="{skill_dir}/scripts/inspect_pr_checks.py"
REPO="{repo}"
PR_INPUT="{pr}"
MAX_LINES="{max_lines}"
CONTEXT="{context}"
JSON_MODE="{json}"
OUTPUT_PATH="/tmp/inspect-pr-checks.json"

if [[ "$SCRIPT_PATH" == "{skill_dir}/scripts/inspect_pr_checks.py" ]]; then
  SCRIPT_PATH="scripts/inspect_pr_checks.py"
fi
if [[ "$REPO" == "{repo}" || -z "$REPO" ]]; then
  REPO="."
fi
if [[ "$PR_INPUT" == "{pr}" ]]; then
  PR_INPUT=""
fi
if [[ "$MAX_LINES" == "{max_lines}" || -z "$MAX_LINES" ]]; then
  MAX_LINES=160
fi
if [[ "$CONTEXT" == "{context}" || -z "$CONTEXT" ]]; then
  CONTEXT=30
fi

SCRIPT_ARGS=(--repo "$REPO" --max-lines "$MAX_LINES" --context "$CONTEXT")
if [[ -n "$PR_INPUT" ]]; then
  SCRIPT_ARGS+=(--pr "$PR_INPUT")
fi

if [[ "$JSON_MODE" == "true" || "$JSON_MODE" == "1" ]]; then
  SCRIPT_ARGS+=(--json)
  python3 "$SCRIPT_PATH" "${SCRIPT_ARGS[@]}" | tee "$OUTPUT_PATH"
  echo "JSON saved to $OUTPUT_PATH"
else
  python3 "$SCRIPT_PATH" "${SCRIPT_ARGS[@]}"
fi
```

### Paste and run (Phase 3): summarize failing checks from JSON

```bash
#!/usr/bin/env bash
set -euo pipefail

OUTPUT_PATH="/tmp/inspect-pr-checks.json"
if [[ ! -f "$OUTPUT_PATH" ]]; then
  echo "Run phase 2 with {json}=true first, then return here."
  exit 1
fi

if command -v jq >/dev/null 2>&1; then
  echo "PR: $(jq -r '.pr' "$OUTPUT_PATH")"
  echo "Failing checks:"
  jq -r '.results[] | " - " + .name + " [" + (.status | tostring) + "] " + (.detailsUrl // "n/a")' "$OUTPUT_PATH"
  echo
  jq -r '.results[] | " - " + .name + " | note: " + (.note // "none") + " | error: " + (.error // "none")' "$OUTPUT_PATH"
else
  python3 -m json.tool "$OUTPUT_PATH"
fi
```

### Paste and run (Phase 4): inspect snippets and unavailable-log signals

```bash
#!/usr/bin/env bash
set -euo pipefail

OUTPUT_PATH="/tmp/inspect-pr-checks.json"
if [[ ! -f "$OUTPUT_PATH" ]]; then
  echo "Run phase 2 with {json}=true first, then return here."
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "Install jq to show one-line snippet diagnostics."
  exit 2
fi

echo "Checks with snippets:"
jq -r '.results[] | select(.status=="ok") | "\(.name):\n\(.logSnippet // "No snippet")\n"' "$OUTPUT_PATH"
echo
echo "Checks with missing/partial logs:"
jq -r '.results[] | select(.status != "ok") | "\(.name): \(.status) - \(.error // .note // "no detail")\n"' "$OUTPUT_PATH"
```

### Paste and run (Phase 5): decide next action

```bash
#!/usr/bin/env bash
set -euo pipefail

OUTPUT_PATH="/tmp/inspect-pr-checks.json"

if [[ ! -f "$OUTPUT_PATH" ]]; then
  echo "Run phase 2 with {json}=true first, then return here."
  exit 1
fi

if command -v jq >/dev/null 2>&1; then
  if [[ "$(jq '.results | length' "$OUTPUT_PATH")" -eq 0 ]]; then
    echo "No failing checks found. Re-run when CI has run additional jobs."
    exit 0
  fi
fi

echo "Next actions to execute manually:"
echo "- Confirm root cause from Failure snippet section (Phase 4)."
echo "- Apply local patch, rerun tests, then push commit to the PR branch."
echo "- Re-run this workflow after pushing to refresh run status."
```

### Workflow note

This workflow is template-first and intentionally conservative: it exposes copy/pasteable steps and clear fallback text, and can be promoted into a dedicated helper script after your preferred automated actions are agreed.

## issue-create-label-suggestions

Purpose: suggest repository labels from title/body signals before creating a new issue and only apply labels after explicit user confirmation.

### Preconditions

- `gh` installed and authenticated.
- `REPO` must resolve (or pass it explicitly as `owner/repo`).
- `issues_suggest_labels.sh` available in this skill.

### Paste and run (Phase 1): auth + repo + input capture

```bash
#!/usr/bin/env bash
set -euo pipefail

REPO="{repo}"
TITLE="{title}"
BODY="{body}"

if ! gh auth status >/tmp/gh-label-suggest-auth.txt 2>&1; then
  cat /tmp/gh-label-suggest-auth.txt
  echo "Run: gh auth login"
  exit 2
fi

if [[ "$REPO" == "{repo}" || -z "$REPO" ]]; then
  echo "Missing {repo}; replace with owner/repo or the current repo context."
  exit 1
fi
if [[ -z "$TITLE" ]]; then
  echo "Missing {title}; replace with the issue title."
  exit 1
fi
```

### Paste and run (Phase 2): fetch ranked label suggestions

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_PATH="{skill_dir}/scripts/issues_suggest_labels.sh"
REPO="{repo}"
TITLE="{title}"
BODY="{body}"
MAX_SUGGESTIONS="{max_suggestions}"
MIN_SCORE="{min_score}"
ALLOW_NEW_LABELS="{allow_new_labels}"
NEW_LABEL_COLOR="{new_label_color}"
NEW_LABEL_DESCRIPTION="{new_label_description}"
OUTPUT_JSON=true

if [[ "$SCRIPT_PATH" == "{skill_dir}/scripts/issues_suggest_labels.sh" ]]; then
  SCRIPT_PATH="scripts/issues_suggest_labels.sh"
fi
if [[ -z "$MAX_SUGGESTIONS" || "$MAX_SUGGESTIONS" == "{max_suggestions}" ]]; then
  MAX_SUGGESTIONS=5
fi
if [[ -z "$MIN_SCORE" || "$MIN_SCORE" == "{min_score}" ]]; then
  MIN_SCORE=0.2
fi

SCRIPT_ARGS=(--repo "$REPO" --title "$TITLE" --max-suggestions "$MAX_SUGGESTIONS" --min-score "$MIN_SCORE")
if [[ "$OUTPUT_JSON" == "true" || "$OUTPUT_JSON" == "1" ]]; then
  SCRIPT_ARGS+=(--json)
fi
if [[ "${ALLOW_NEW_LABELS,,}" == "true" || "${ALLOW_NEW_LABELS,,}" == "yes" || "${ALLOW_NEW_LABELS,,}" == "1" ]]; then
  SCRIPT_ARGS+=(--allow-new-label)
  if [[ -n "$NEW_LABEL_COLOR" && "$NEW_LABEL_COLOR" != "{new_label_color}" ]]; then
    SCRIPT_ARGS+=(--new-label-color "$NEW_LABEL_COLOR")
  fi
  if [[ -n "$NEW_LABEL_DESCRIPTION" && "$NEW_LABEL_DESCRIPTION" != "{new_label_description}" ]]; then
    SCRIPT_ARGS+=(--new-label-description "$NEW_LABEL_DESCRIPTION")
  fi
fi

"$SCRIPT_PATH" "${SCRIPT_ARGS[@]}"
```

### Paste and run (Phase 3): confirm suggestion selection with user

```bash
#!/usr/bin/env bash
set -euo pipefail

REPO="{repo}"
TITLE="{title}"
BODY="{body}"
SELECTED_LABELS="{selected_labels}"

if [[ "$SELECTED_LABELS" == "{selected_labels}" ]]; then
  echo "No labels selected. Re-run workflow only when user confirms selection."
  exit 0
fi
```

### Paste and run (Phase 4): create issue only after confirmation

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_PATH="{skill_dir}/scripts/issues_create.sh"
REPO="{repo}"
TITLE="{title}"
BODY="{body}"
SELECTED_LABELS="{selected_labels}"
ASSIGNEES="{assignees}"

if [[ "$SCRIPT_PATH" == "{skill_dir}/scripts/issues_create.sh" ]]; then
  SCRIPT_PATH="scripts/issues_create.sh"
fi

if [[ -z "$SELECTED_LABELS" ]]; then
  echo "No labels provided; create issue without labels."
  "$SCRIPT_PATH" --repo "$REPO" --title "$TITLE" --body "$BODY"
  exit 0
fi

if [[ -n "$ASSIGNEES" ]]; then
  "$SCRIPT_PATH" --repo "$REPO" --title "$TITLE" --body "$BODY" --labels "$SELECTED_LABELS" --assignees "$ASSIGNEES"
else
  "$SCRIPT_PATH" --repo "$REPO" --title "$TITLE" --body "$BODY" --labels "$SELECTED_LABELS"
fi
```

### Fallbacks

- no labels available: confirm labels exist in repo with `gh label list --repo "$REPO"` and retry
- no high-confidence reusable matches: either add stronger context terms or enable fallback labels with curated reusable candidates.
- new label fallback: when `ALLOW_NEW_LABELS` is set, suggestions are created at repo scope with `gh label create --repo`; keep fallback candidates generic (`bug`, `enhancement`, `documentation`, etc.) so they stay reusable.
- no auth: run `gh auth login`
- empty candidate list: use threshold controls (`--min-score`) or pass clearer title/body context

## commit-with-issue-close

Purpose: infer issue linkage from branch/context and propose `Fixes #<number>` (or chosen token) with explicit user approval before commit.

### Preconditions

- `git` and `gh` installed.
- Current directory is a git repo, unless `--repo` is provided as a valid local path.
- `commit_issue_linker.sh` is available in this skill.

### Paste and run (Phase 1): capture message/context and infer candidates

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_PATH="{skill_dir}/scripts/commit_issue_linker.sh"
MESSAGE="{message}"
CONTEXT="{context}"
BRANCH="{branch}"
REPO="{repo}"
ISSUE_NUMBER="{issue_number}"
TOKEN="{token}"
JSON_MODE="{json}"

if [[ "$SCRIPT_PATH" == "{skill_dir}/scripts/commit_issue_linker.sh" ]]; then
  SCRIPT_PATH="scripts/commit_issue_linker.sh"
fi
if [[ "$TOKEN" == "{token}" || -z "$TOKEN" ]]; then
  TOKEN="fixes"
fi

if [[ "$JSON_MODE" == "true" || "$JSON_MODE" == "1" ]]; then
  "$SCRIPT_PATH" \
    --message "$MESSAGE" \
    --context "$CONTEXT" \
    ${BRANCH:+--branch "$BRANCH"} \
    ${REPO:+--repo "$REPO"} \
    ${ISSUE_NUMBER:+--issue-number "$ISSUE_NUMBER"} \
    --token "$TOKEN" \
    --json
else
  "$SCRIPT_PATH" \
    --message "$MESSAGE" \
    --context "$CONTEXT" \
    ${BRANCH:+--branch "$BRANCH"} \
    ${REPO:+--repo "$REPO"} \
    ${ISSUE_NUMBER:+--issue-number "$ISSUE_NUMBER"} \
    --token "$TOKEN"
fi
```

### Paste and run (Phase 2): review decision and user choice

```bash
#!/usr/bin/env bash
set -euo pipefail

DECISION_STATE="{decision_state}"
PROPOSED_MESSAGE="{proposed_message}"

case "$DECISION_STATE" in
  no_candidate)
    echo "No issue candidate found; commit without close token or add context explicitly."
    ;;
  ambiguous)
    echo "Multiple candidates detected; pick one candidate and rerun with --issue-number <n>."
    ;;
  already_linked)
    echo "Message already includes a close token; commit as-is."
    ;;
  single_candidate)
    echo "Suggested commit message:"
    echo "$PROPOSED_MESSAGE"
    ;;
esac
```

### Paste and run (Phase 3): commit only after approval

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_PATH="{skill_dir}/scripts/commit_issue_linker.sh"
REPO="{repo}"
MESSAGE="{proposed_message}"
APPROVE="{approve}"

if [[ "$SCRIPT_PATH" == "{skill_dir}/scripts/commit_issue_linker.sh" ]]; then
  SCRIPT_PATH="scripts/commit_issue_linker.sh"
fi

if [[ "$APPROVE" != "yes" ]]; then
  echo "Execution blocked. Confirm with APPROVE=yes before running --execute."
  exit 1
fi

"$SCRIPT_PATH" \
  --message "$MESSAGE" \
  --repo "$REPO" \
  --execute

```

### Fallbacks

- no auth: run `gh auth login`
- not on a git repo: run inside the repo path and pass `--repo .` if needed
- ambiguous/no candidate: ask the user for `{issue_number}` and rerun
- commit context already has a close token: the workflow keeps it and does not add duplicates
