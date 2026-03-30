#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: repos_view.sh [--repo <owner/repo>] [--json] [--allow-non-project]
EOF
}

REPO=""
JSON=0
ALLOW_NON_PROJECT=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      REPO="${2:-}"
      if [[ -z "$REPO" ]]; then
        echo "Missing value for --repo" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --json)
      JSON=1
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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/github_lib.sh"

if [[ -n "$REPO" ]]; then
  github_require_repo_reference "$REPO"
fi

TARGET_REPO="$(github_resolve_repo "$SCRIPT_DIR" "$REPO" "$ALLOW_NON_PROJECT")"
PAYLOAD="$(gh repo view "$TARGET_REPO" --json nameWithOwner,description,defaultBranchRef,visibility,isPrivate,isArchived,isFork,url --jq '.')"

GITHUB_PAYLOAD="$PAYLOAD" python3 - "$JSON" <<'PY'
import json
import os
import sys

json_mode = bool(int(sys.argv[1]))
data = json.loads(os.environ["GITHUB_PAYLOAD"])

visibility = data.get("visibility")
if not visibility:
    visibility = "private" if data.get("isPrivate") else "public"

normalized = {
    "repo": data.get("nameWithOwner", ""),
    "description": data.get("description") or "",
    "default_branch": ((data.get("defaultBranchRef") or {}).get("name") or ""),
    "visibility": visibility,
    "archived": bool(data.get("isArchived")),
    "fork": bool(data.get("isFork")),
    "url": data.get("url") or "",
}

if json_mode:
    print(json.dumps(normalized, indent=2))
    raise SystemExit(0)

print(f"Repository: {normalized['repo']}")
print(f"Description: {normalized['description'] or '(empty)'}")
print(f"Default branch: {normalized['default_branch'] or 'unknown'}")
print(f"Visibility: {normalized['visibility']}")
print(f"Archived: {'yes' if normalized['archived'] else 'no'}")
print(f"Fork: {'yes' if normalized['fork'] else 'no'}")
print(f"URL: {normalized['url']}")
PY
