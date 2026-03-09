# GitHub workflow templates

Use this section for copy-paste, branch-safe operational flows.

Note (2026-03): cross-repo issue transfers now use dedicated helper scripts so the repo context and source-closure behavior stay consistent.

## release-or-tag-create

Purpose: create a release-backed tag or a tag-only ref without guessing the target branch or commit.

### Preconditions

- `gh` installed and authenticated.
- Repository scope is known.
- If you are operating from a local clone, run `scripts/preflight_gh.sh --expect-repo <owner/repo>` from that repo root before mutation.
- For tag-only creation with `git tag`, work from a local clone of the target repository.

### Operator policy

- Decide whether the request is for a GitHub release or a tag only.
- Never assume `main`; resolve the repository default branch.
- When the user does not provide a target branch or commit, propose the default branch HEAD commit and confirm it before creating anything.
- For releases, choose the notes strategy before publishing:
  - option 1: infer notes by diffing since the last published release tag,
  - option 2: keep the release notes blank,
  - option 3: use user-provided notes.
- If the user does not specify a notes strategy, offer those three options and recommend option 1.
- For option 1, resolve the latest published release tag when one exists and generate proposed notes from that tag to the confirmed target.
- If the user wants a different target, choose branch first, then commit.
- Even after default-target confirmation, prefer `gh release create <tag> --target <branch-or-sha>` so the target is explicit.

### Paste and run (Phase 1): resolve the default target and show it for confirmation

```bash
#!/usr/bin/env bash
set -euo pipefail

REPO="{repo}"
TARGET_BRANCH="{target_branch}"

if ! gh auth status >/tmp/gh-release-workflow-auth.txt 2>&1; then
  cat /tmp/gh-release-workflow-auth.txt
  echo "Run: gh auth login"
  exit 2
fi

if [[ "$REPO" == "{repo}" || -z "$REPO" ]]; then
  REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
fi

DEFAULT_BRANCH="$(gh repo view "$REPO" --json defaultBranchRef -q .defaultBranchRef.name)"
if [[ "$TARGET_BRANCH" == "{target_branch}" || -z "$TARGET_BRANCH" ]]; then
  TARGET_BRANCH="$DEFAULT_BRANCH"
fi

TARGET_SHA="$(gh api "repos/$REPO/commits/$TARGET_BRANCH" --jq '.sha')"
TARGET_SUBJECT="$(gh api "repos/$REPO/commits/$TARGET_BRANCH" --jq '.commit.message | split("\n")[0]')"

echo "Repository:      $REPO"
echo "Default branch:  $DEFAULT_BRANCH"
echo "Target branch:   $TARGET_BRANCH"
echo "Target commit:   ${TARGET_SHA:0:7} $TARGET_SUBJECT"
echo
echo "If this is not the target you want, choose a branch first and then a specific commit on that branch."
echo "Recent commits on $TARGET_BRANCH:"
gh api "repos/$REPO/commits?sha=$TARGET_BRANCH&per_page=10" \
  --jq '.[] | "  \(.sha[0:7]) \(.commit.message | split("\n")[0])"'
```

### Paste and run (Phase 1B, option 1): prepare inferred release notes since the last published release tag

```bash
#!/usr/bin/env bash
set -euo pipefail

REPO="{repo}"
NEW_TAG="{new_tag}"
TARGET_REF="{target_ref}"
WORKDIR="${TMPDIR:-/tmp}/gh-release-notes-${RANDOM}"

if [[ "$REPO" == "{repo}" || -z "$REPO" ]]; then
  REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
fi
if [[ "$NEW_TAG" == "{new_tag}" || -z "$NEW_TAG" ]]; then
  echo "Replace {new_tag} with the new release tag."
  exit 1
fi
if [[ "$TARGET_REF" == "{target_ref}" || -z "$TARGET_REF" ]]; then
  echo "Replace {target_ref} with the confirmed branch or commit SHA."
  exit 1
fi

mkdir -p "$WORKDIR"
PREVIOUS_TAG="$(gh release list --repo "$REPO" --exclude-drafts --exclude-pre-releases --json tagName --limit 1 --jq '.[0].tagName' || true)"

API_ARGS=(
  "repos/$REPO/releases/generate-notes"
  -X POST
  -f "tag_name=$NEW_TAG"
  -f "target_commitish=$TARGET_REF"
)
if [[ -n "$PREVIOUS_TAG" && "$PREVIOUS_TAG" != "null" ]]; then
  API_ARGS+=(-f "previous_tag_name=$PREVIOUS_TAG")
fi

gh api "${API_ARGS[@]}" --jq '.name' > "$WORKDIR/release_title.txt"
gh api "${API_ARGS[@]}" --jq '.body' > "$WORKDIR/release_notes.md"

echo "Repository:      $REPO"
if [[ -n "$PREVIOUS_TAG" && "$PREVIOUS_TAG" != "null" ]]; then
  echo "Previous tag:    $PREVIOUS_TAG"
else
  echo "Previous tag:    <none found; treating as first published release>"
fi
echo "Draft title:     $(cat "$WORKDIR/release_title.txt")"
echo "Draft notes:     $WORKDIR/release_notes.md"
echo
sed -n '1,80p' "$WORKDIR/release_notes.md"
```

### Paste and run (Phase 2A): create a release and create the tag if it is missing

```bash
#!/usr/bin/env bash
set -euo pipefail

REPO="{repo}"
TAG="{tag}"
TARGET_REF="{target_ref}"
NOTES_MODE="{infer|blank|user}"
NOTES_FILE="{notes_file}"
TITLE_FILE="{title_file}"
PREVIOUS_TAG="{previous_tag}"
NOTES_TEXT="{notes_text}"

if [[ "$REPO" == "{repo}" || -z "$REPO" ]]; then
  REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
fi
if [[ "$TAG" == "{tag}" || -z "$TAG" ]]; then
  echo "Replace {tag} with the release tag to create."
  exit 1
fi
if [[ "$TARGET_REF" == "{target_ref}" || -z "$TARGET_REF" ]]; then
  echo "Replace {target_ref} with the confirmed branch or commit SHA."
  exit 1
fi
if [[ "$NOTES_MODE" == "{infer|blank|user}" || -z "$NOTES_MODE" ]]; then
  echo "Replace {infer|blank|user} with infer, blank, or user."
  exit 1
fi

CMD=(gh release create "$TAG" --repo "$REPO" --target "$TARGET_REF" --fail-on-no-commits)
if [[ "$TITLE_FILE" != "{title_file}" && -n "$TITLE_FILE" ]]; then
  CMD+=(-t "$(cat "$TITLE_FILE")")
fi

case "$NOTES_MODE" in
  infer)
    if [[ "$NOTES_FILE" != "{notes_file}" && -n "$NOTES_FILE" ]]; then
      CMD+=(-F "$NOTES_FILE")
    elif [[ "$PREVIOUS_TAG" != "{previous_tag}" && -n "$PREVIOUS_TAG" ]]; then
      CMD+=(--generate-notes --notes-start-tag "$PREVIOUS_TAG")
    else
      CMD+=(--generate-notes)
    fi
    ;;
  blank)
    CMD+=(--notes "")
    ;;
  user)
    if [[ "$NOTES_FILE" != "{notes_file}" && -n "$NOTES_FILE" ]]; then
      CMD+=(-F "$NOTES_FILE")
    elif [[ "$NOTES_TEXT" != "{notes_text}" && -n "$NOTES_TEXT" ]]; then
      CMD+=(--notes "$NOTES_TEXT")
    else
      echo "For NOTES_MODE=user, provide either {notes_file} or {notes_text}."
      exit 1
    fi
    ;;
  *)
    echo "NOTES_MODE must be one of: infer, blank, user."
    exit 1
    ;;
esac

"${CMD[@]}"
gh release view "$TAG" --repo "$REPO" --json url,tagName,targetCommitish
```

### Paste and run (Phase 2B): create a tag only from a local clone

```bash
#!/usr/bin/env bash
set -euo pipefail

TAG="{tag}"
TARGET_SHA="{target_sha}"
ANNOTATION="{annotation}"

if [[ "$TAG" == "{tag}" || -z "$TAG" ]]; then
  echo "Replace {tag} with the tag to create."
  exit 1
fi
if [[ "$TARGET_SHA" == "{target_sha}" || -z "$TARGET_SHA" ]]; then
  echo "Replace {target_sha} with the confirmed commit SHA."
  exit 1
fi

if [[ "$ANNOTATION" == "{annotation}" || -z "$ANNOTATION" ]]; then
  git tag "$TAG" "$TARGET_SHA"
else
  git tag -a "$TAG" "$TARGET_SHA" -m "$ANNOTATION"
fi

git push origin "$TAG"
git rev-list -n 1 "$TAG"
```

### Notes

- `gh release create <tag>` auto-creates the tag when it is missing, but this workflow still resolves and confirms the target up front so the release does not accidentally point at the wrong commit.
- The release-notes API can generate a name and markdown body for the new release; GitHub documents that the body contains information such as the changes since the last release and contributors.
- Option 1 is the recommended default when the user asks to create a release without specifying how notes should be produced.
- Option 2 keeps the release notes blank on purpose.
- Option 3 is for text the user wants to supply directly or via a file.
- If you need a release from an annotated tag, create and push the annotated tag first, then run `gh release create <tag> --verify-tag --notes-from-tag`.
- For remote-only tag creation without a local clone, use `gh api` against the Git database endpoints only when the user explicitly wants that API-based path.

## issue-copy-or-move

Purpose: copy or move an issue between repositories without manually reassembling title/body text or improvising the source backlink behavior.

### Preconditions

- `gh` installed and authenticated.
- Source issue number is known.
- Source and target repositories are known in `owner/repo` format.
- If you are operating on the current repo manually, run preflight from that repo root and prefer `--expect-repo`.

### Standard notes

- Copy target note: `Copied from <source_repo>#<issue> (<source_url>).`
- Move target note: `Moved from <source_repo>#<issue> (<source_url>).`
- Move source note: `Moved to <target_repo>#<new_issue> (<new_url>). Continuing work there.`

### Paste and run: copy an issue across repositories

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_PATH="{skill_dir}/scripts/issues_copy.sh"
SOURCE_REPO="{source_repo}"
TARGET_REPO="{target_repo}"
ISSUE="{issue_number}"

if [[ "$SCRIPT_PATH" == "{skill_dir}/scripts/issues_copy.sh" ]]; then
  SCRIPT_PATH="scripts/issues_copy.sh"
fi
if [[ "$SOURCE_REPO" == "{source_repo}" || -z "$SOURCE_REPO" ]]; then
  echo "Replace {source_repo} with the source owner/repo."
  exit 1
fi
if [[ "$TARGET_REPO" == "{target_repo}" || -z "$TARGET_REPO" ]]; then
  echo "Replace {target_repo} with the target owner/repo."
  exit 1
fi
if [[ "$ISSUE" == "{issue_number}" || -z "$ISSUE" ]]; then
  echo "Replace {issue_number} with the source issue number."
  exit 1
fi

"$SCRIPT_PATH" --issue "$ISSUE" --source-repo "$SOURCE_REPO" --target-repo "$TARGET_REPO"
```

### Paste and run: move an issue across repositories

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_PATH="{skill_dir}/scripts/issues_move.sh"
SOURCE_REPO="{source_repo}"
TARGET_REPO="{target_repo}"
ISSUE="{issue_number}"

if [[ "$SCRIPT_PATH" == "{skill_dir}/scripts/issues_move.sh" ]]; then
  SCRIPT_PATH="scripts/issues_move.sh"
fi
if [[ "$SOURCE_REPO" == "{source_repo}" || -z "$SOURCE_REPO" ]]; then
  echo "Replace {source_repo} with the source owner/repo."
  exit 1
fi
if [[ "$TARGET_REPO" == "{target_repo}" || -z "$TARGET_REPO" ]]; then
  echo "Replace {target_repo} with the target owner/repo."
  exit 1
fi
if [[ "$ISSUE" == "{issue_number}" || -z "$ISSUE" ]]; then
  echo "Replace {issue_number} with the source issue number."
  exit 1
fi

"$SCRIPT_PATH" --issue "$ISSUE" --source-repo "$SOURCE_REPO" --target-repo "$TARGET_REPO"
```

## issue-close-with-evidence

Purpose: close an issue safely with explicit state verification and implementation evidence links using the dedicated helper script.

### Preconditions

- `gh` installed and authenticated.
- Issue number is known.
- Commit SHA is known.

### Paste and run: close with evidence script

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_PATH="{skill_dir}/scripts/issues_close_with_evidence.sh"
REPO="{repo}"
ISSUE="{issue_number}"
COMMIT_SHA="{commit_sha}"
COMMIT_URL="{commit_url}"
PR_URL="{pr_url}"

if [[ "$SCRIPT_PATH" == "{skill_dir}/scripts/issues_close_with_evidence.sh" ]]; then
  SCRIPT_PATH="scripts/issues_close_with_evidence.sh"
fi
if [[ "$REPO" == "{repo}" ]]; then
  REPO=""
fi
if [[ "$COMMIT_URL" == "{commit_url}" ]]; then
  COMMIT_URL=""
fi
if [[ "$PR_URL" == "{pr_url}" ]]; then
  PR_URL=""
fi
if [[ "$ISSUE" == "{issue_number}" || -z "$ISSUE" ]]; then
  echo "Replace {issue_number} with the target issue number."
  exit 1
fi
if [[ "$COMMIT_SHA" == "{commit_sha}" || -z "$COMMIT_SHA" ]]; then
  echo "Replace {commit_sha} with the implementation commit SHA."
  exit 1
fi

SCRIPT_ARGS=(--issue "$ISSUE" --commit-sha "$COMMIT_SHA")
if [[ -n "$REPO" ]]; then
  SCRIPT_ARGS+=(--repo "$REPO" --allow-non-project)
fi
if [[ -n "$COMMIT_URL" ]]; then
  SCRIPT_ARGS+=(--commit-url "$COMMIT_URL")
fi
if [[ -n "$PR_URL" ]]; then
  SCRIPT_ARGS+=(--pr-url "$PR_URL")
fi

"$SCRIPT_PATH" "${SCRIPT_ARGS[@]}"
```

### Fallbacks

- auth failures: run `gh auth login`, then rerun preflight
- repo resolution failures: run in repo root or pass explicit `owner/repo` (the template automatically enables non-project mode when `REPO` is set)

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
If you want to promote this into a script, the next iteration is a dedicated `prs_address_comments.sh` helper that accepts `--pr`, `--selection`, `--repo`, and optional `--comment-ids`.

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
