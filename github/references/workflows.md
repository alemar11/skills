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
