#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: issues_view.sh --issue <number> [--summary] [--repo <owner/repo>] [--allow-non-project]
EOF
}

ISSUE=""
SUMMARY=0
REPO=""
ALLOW_NON_PROJECT=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --issue)
      ISSUE="${2:-}"
      if [[ -z "$ISSUE" ]]; then
        echo "Missing value for --issue" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --summary)
      SUMMARY=1
      shift
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

if [[ -z "$ISSUE" ]]; then
  echo "Missing required --issue" >&2
  usage >&2
  exit 64
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/github_lib.sh"

if [[ -n "$REPO" ]]; then
  github_require_repo_reference "$REPO"
fi

github_require_issue_number "$ISSUE"
TARGET_REPO="$(github_resolve_repo "$SCRIPT_DIR" "$REPO" "$ALLOW_NON_PROJECT")"

PAYLOAD="$(gh issue view "$ISSUE" --repo "$TARGET_REPO" --json number,title,state,labels,assignees,body,createdAt,updatedAt,url,author,comments --jq '.')"

if [[ "$SUMMARY" -eq 0 ]]; then
  printf '%s\n' "$PAYLOAD"
  exit 0
fi

GITHUB_PAYLOAD="$PAYLOAD" python3 - "$TARGET_REPO" <<'PY'
import json
import os
import sys

repo = sys.argv[1]
data = json.loads(os.environ["GITHUB_PAYLOAD"])

def names(items, key):
    values = []
    for item in items or []:
        if isinstance(item, dict):
            value = item.get(key, "")
            if value:
                values.append(value)
    return ", ".join(values) if values else "none"

body = (data.get("body") or "").replace("\r\n", "\n").replace("\n", " ").strip()
if len(body) > 220:
    body = body[:217] + "..."

author = ""
if isinstance(data.get("author"), dict):
    author = data["author"].get("login", "")

print(f"Issue: {repo}#{data.get('number')} {data.get('title', '')}")
print(f"State: {data.get('state', '')}")
print(f"Author: {author or 'unknown'}")
print(f"Assignees: {names(data.get('assignees') or [], 'login')}")
print(f"Labels: {names(data.get('labels') or [], 'name')}")
print(f"Updated: {data.get('updatedAt', '')}")
print(f"URL: {data.get('url', '')}")
print(f"Body: {body or '(empty)'}")
PY
