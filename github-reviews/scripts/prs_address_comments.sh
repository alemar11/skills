#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: prs_address_comments.sh --pr <number> [--repo <owner/repo>] [--include-resolved] [--json] [--selection <rows>] [--comment-ids <ids>] [--reply-body <text>] [--dry-run] [--allow-non-project]
EOF
}

PR=""
REPO=""
INCLUDE_RESOLVED=0
JSON=0
SELECTION=""
COMMENT_IDS=""
REPLY_BODY=""
DRY_RUN=0
ALLOW_NON_PROJECT=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pr)
      PR="${2:-}"
      if [[ -z "$PR" ]]; then
        echo "Missing value for --pr" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --repo)
      REPO="${2:-}"
      if [[ -z "$REPO" ]]; then
        echo "Missing value for --repo" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --include-resolved)
      INCLUDE_RESOLVED=1
      shift
      ;;
    --json)
      JSON=1
      shift
      ;;
    --selection)
      SELECTION="${2:-}"
      if [[ -z "$SELECTION" ]]; then
        echo "Missing value for --selection" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --comment-ids)
      COMMENT_IDS="${2:-}"
      if [[ -z "$COMMENT_IDS" ]]; then
        echo "Missing value for --comment-ids" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --reply-body)
      REPLY_BODY="${2:-}"
      if [[ -z "$REPLY_BODY" ]]; then
        echo "Missing value for --reply-body" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --allow-non-project)
      ALLOW_NON_PROJECT=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 64
      ;;
  esac
done

if [[ -z "$PR" ]]; then
  echo "Missing required --pr" >&2
  usage >&2
  exit 64
fi

if [[ -n "$REPLY_BODY" ]]; then
  if [[ -n "$SELECTION" && -n "$COMMENT_IDS" ]]; then
    echo "Use either --selection or --comment-ids with --reply-body, not both." >&2
    exit 64
  fi
  if [[ -z "$SELECTION" && -z "$COMMENT_IDS" ]]; then
    echo "--reply-body requires either --selection or --comment-ids." >&2
    exit 64
  fi
else
  if [[ -n "$SELECTION" || -n "$COMMENT_IDS" ]]; then
    echo "--selection and --comment-ids require --reply-body." >&2
    exit 64
  fi
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/github_lib.sh"

if [[ -n "$REPO" ]]; then
  github_require_repo_reference "$REPO"
fi
github_require_pr_number "$PR"
TARGET_REPO="$(github_resolve_repo "$SCRIPT_DIR" "$REPO" "$ALLOW_NON_PROJECT")"

python3 - "$TARGET_REPO" "$PR" "$INCLUDE_RESOLVED" "$JSON" "$SELECTION" "$COMMENT_IDS" "$REPLY_BODY" "$DRY_RUN" <<'PY'
import json
import subprocess
import sys

repo, pr, include_resolved_raw, json_mode_raw, selection_raw, comment_ids_raw, reply_body, dry_run_raw = sys.argv[1:9]
include_resolved = bool(int(include_resolved_raw))
json_mode = bool(int(json_mode_raw))
dry_run = bool(int(dry_run_raw))

def run_cmd(cmd):
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode != 0:
        message = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(message or "command failed")
    return proc.stdout

def gh_api_paginated(endpoint: str) -> list[dict]:
    page = 1
    items = []
    while True:
        cmd = [
            "gh",
            "api",
            endpoint,
            "-X",
            "GET",
            "-F",
            "per_page=100",
            "-F",
            f"page={page}",
            "-H",
            "Accept: application/vnd.github+json",
        ]
        proc = subprocess.run(cmd, text=True, capture_output=True)
        if proc.returncode != 0:
            message = (proc.stderr or proc.stdout or "").strip()
            raise RuntimeError(message or "gh api failed")
        payload = json.loads(proc.stdout or "[]")
        if not isinstance(payload, list):
            raise RuntimeError("Unexpected paginated response shape.")
        items.extend(item for item in payload if isinstance(item, dict))
        if len(payload) < 100:
            break
        page += 1
    return items

def gh_graphql_threads() -> list[dict]:
    owner, repo_name = repo.split("/", 1)
    query = """
query($owner: String!, $repo: String!, $number: Int!, $after: String) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      reviewThreads(first: 50, after: $after) {
        pageInfo { hasNextPage endCursor }
        nodes {
          isResolved
          isOutdated
          path
          line
          startLine
          comments(first: 100) {
            nodes {
              databaseId
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
""".strip()
    items = []
    after = None
    while True:
        cmd = [
            "gh",
            "api",
            "graphql",
            "-f",
            f"owner={owner}",
            "-f",
            f"repo={repo_name}",
            "-F",
            f"number={pr}",
            "-f",
            f"query={query}",
        ]
        if after:
            cmd.extend(["-f", f"after={after}"])
        proc = subprocess.run(cmd, text=True, capture_output=True)
        if proc.returncode != 0:
            message = (proc.stderr or proc.stdout or "").strip()
            raise RuntimeError(message or "gh api graphql failed")
        payload = json.loads(proc.stdout or "{}")
        threads = (
            ((payload.get("data") or {}).get("repository") or {})
            .get("pullRequest", {})
            .get("reviewThreads", {})
        )
        nodes = threads.get("nodes") or []
        items.extend(node for node in nodes if isinstance(node, dict))
        page_info = threads.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        after = page_info.get("endCursor")
        if not after:
            break
    return items

def snippet(text: str) -> str:
    compact = (text or "").replace("\r\n", "\n").replace("\n", " ").strip()
    if len(compact) > 220:
        return compact[:217] + "..."
    return compact

conversation_comments = gh_api_paginated(f"repos/{repo}/issues/{pr}/comments")
review_comments = gh_api_paginated(f"repos/{repo}/pulls/{pr}/comments")
threads = gh_graphql_threads()

active_thread_entries = []
other_thread_entries = []
thread_comment_ids = set()

for thread in threads:
    resolved = bool(thread.get("isResolved"))
    outdated = bool(thread.get("isOutdated"))
    is_active = (not resolved) and (not outdated)
    if not include_resolved and not is_active:
        continue
    bucket = active_thread_entries if is_active else other_thread_entries
    for comment in ((thread.get("comments") or {}).get("nodes") or []):
        if not isinstance(comment, dict):
            continue
        comment_id = comment.get("databaseId")
        if not comment_id:
            continue
        thread_comment_ids.add(int(comment_id))
        bucket.append(
            {
                "type": "review_thread_comment",
                "comment_id": int(comment_id),
                "author": ((comment.get("author") or {}).get("login") or ""),
                "updated": comment.get("updatedAt") or comment.get("createdAt") or "",
                "body": comment.get("body") or "",
                "body_preview": snippet(comment.get("body") or ""),
                "path": thread.get("path") or "",
                "line": thread.get("line"),
                "start_line": thread.get("startLine"),
                "is_resolved": resolved,
                "is_outdated": outdated,
            }
        )

orphan_review_entries = []
for comment in review_comments:
    comment_id = comment.get("id")
    if not comment_id or int(comment_id) in thread_comment_ids:
        continue
    orphan_review_entries.append(
        {
            "type": "review_comment",
            "comment_id": int(comment_id),
            "author": ((comment.get("user") or {}).get("login") or ""),
            "updated": comment.get("updated_at") or comment.get("created_at") or "",
            "body": comment.get("body") or "",
            "body_preview": snippet(comment.get("body") or ""),
            "path": comment.get("path") or "",
            "line": comment.get("line"),
            "start_line": comment.get("start_line"),
            "is_resolved": None,
            "is_outdated": None,
        }
    )

conversation_entries = []
for comment in conversation_comments:
    comment_id = comment.get("id")
    if not comment_id:
        continue
    conversation_entries.append(
        {
            "type": "conversation_comment",
            "comment_id": int(comment_id),
            "author": ((comment.get("user") or {}).get("login") or ""),
            "updated": comment.get("updated_at") or comment.get("created_at") or "",
            "body": comment.get("body") or "",
            "body_preview": snippet(comment.get("body") or ""),
            "path": "",
            "line": None,
            "start_line": None,
            "is_resolved": None,
            "is_outdated": None,
        }
    )

entries = active_thread_entries + other_thread_entries + orphan_review_entries + conversation_entries
for index, item in enumerate(entries, start=1):
    item["index"] = index

reply_mode = bool(reply_body)
entries_by_index = {str(item["index"]): item for item in entries}
entries_by_comment_id = {str(item["comment_id"]): item for item in entries}

selected_entries = []
if reply_mode:
    if selection_raw:
        parts = [part.strip() for part in selection_raw.replace(",", " ").split() if part.strip()]
        if not parts:
            raise RuntimeError("No valid selection indices were provided.")
        for part in parts:
            if part not in entries_by_index:
                raise RuntimeError(f"Selection index '{part}' was not found.")
            selected_entries.append(entries_by_index[part])
    elif comment_ids_raw:
        parts = [part.strip() for part in comment_ids_raw.replace(",", " ").split() if part.strip()]
        if not parts:
            raise RuntimeError("No valid comment IDs were provided.")
        for part in parts:
            if part not in entries_by_comment_id:
                raise RuntimeError(f"Comment ID '{part}' was not found in the fetched context.")
            selected_entries.append(entries_by_comment_id[part])

actions = []
if reply_mode:
    for item in selected_entries:
        action = {
            "comment_id": item["comment_id"],
            "type": item["type"],
            "status": "dry-run" if dry_run else "pending",
        }
        if item["type"] == "conversation_comment":
            command = [
                "gh",
                "pr",
                "comment",
                str(pr),
                "--repo",
                repo,
                "--body",
                f"{reply_body} (ref: {item['comment_id']})",
            ]
            action["transport"] = "gh pr comment"
            action["command"] = command
            if not dry_run:
                run_cmd(command)
                action["status"] = "posted"
        else:
            endpoint = f"repos/{repo}/pulls/comments/{item['comment_id']}/replies"
            action["transport"] = "gh api"
            action["endpoint"] = endpoint
            action["body"] = reply_body
            if not dry_run:
                cmd = [
                    "gh",
                    "api",
                    "-X",
                    "POST",
                    endpoint,
                    "-H",
                    "Accept: application/vnd.github+json",
                    "-f",
                    f"body={reply_body}",
                ]
                proc = subprocess.run(cmd, text=True, capture_output=True)
                if proc.returncode == 0:
                    action["status"] = "replied"
                else:
                    fallback = [
                        "gh",
                        "pr",
                        "comment",
                        str(pr),
                        "--repo",
                        repo,
                        "--body",
                        f"{reply_body} (ref: {item['comment_id']})",
                    ]
                    run_cmd(fallback)
                    action["status"] = "fallback-pr-comment"
                    action["fallback_command"] = fallback
        actions.append(action)

if json_mode:
    payload = {"entries": entries}
    if reply_mode:
        payload["actions"] = actions
    print(json.dumps(payload, indent=2))
    raise SystemExit(0)

if entries:
    for item in entries:
        print(
            f"[{item['index']:>3}] {item['type']} id={item['comment_id']} author={item['author'] or 'unknown'} updated={item['updated']}"
        )
        print(f"      {item['body_preview'] or '(empty)'}")
        if item["path"]:
            print(
                f"      file={item['path']} line={item['line']} startLine={item['start_line']} resolved={item['is_resolved']} outdated={item['is_outdated']}"
            )
else:
    print(f"No comment context found for {repo}#{pr}.")

if reply_mode:
    print()
    print("Reply actions:")
    for action in actions:
        if action["type"] == "conversation_comment":
            print(
                f"- comment {action['comment_id']} via {action['transport']}: {action['status']}"
            )
        else:
            print(
                f"- comment {action['comment_id']} via {action['transport']}: {action['status']}"
            )
PY
