#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: prs_list.sh [--state open|closed|merged|all] [--author <user>] [--label <label>] [--base <branch>] [--head <branch>] [--search <query>] [--limit N] [--repo <owner/repo>] [--allow-non-project]
EOF
}

STATE="open"
AUTHOR=""
LABEL=""
BASE=""
HEAD=""
SEARCH=""
LIMIT=20
REPO=""
ALLOW_NON_PROJECT=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --state)
      STATE="${2:-}"
      if [[ -z "$STATE" ]]; then
        echo "Missing value for --state" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --author)
      AUTHOR="${2:-}"
      if [[ -z "$AUTHOR" ]]; then
        echo "Missing value for --author" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --label)
      LABEL="${2:-}"
      if [[ -z "$LABEL" ]]; then
        echo "Missing value for --label" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --base)
      BASE="${2:-}"
      if [[ -z "$BASE" ]]; then
        echo "Missing value for --base" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --head)
      HEAD="${2:-}"
      if [[ -z "$HEAD" ]]; then
        echo "Missing value for --head" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --search)
      SEARCH="${2:-}"
      if [[ -z "$SEARCH" ]]; then
        echo "Missing value for --search" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --limit)
      LIMIT="${2:-}"
      if [[ -z "$LIMIT" ]]; then
        echo "Missing value for --limit" >&2
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
github_require_allowed_value "state" "$STATE" open closed merged all
github_require_positive_int "limit" "$LIMIT"
TARGET_REPO="$(github_resolve_repo "$SCRIPT_DIR" "$REPO" "$ALLOW_NON_PROJECT")"

CMD=(gh pr list --repo "$TARGET_REPO" --state "$STATE" --limit "$LIMIT" --json number,title,state,author,baseRefName,headRefName,isDraft,mergeStateStatus,createdAt,updatedAt,url --jq '.')
if [[ -n "$AUTHOR" ]]; then
  CMD+=(--author "$AUTHOR")
fi
if [[ -n "$LABEL" ]]; then
  CMD+=(--label "$LABEL")
fi
if [[ -n "$BASE" ]]; then
  CMD+=(--base "$BASE")
fi
if [[ -n "$HEAD" ]]; then
  CMD+=(--head "$HEAD")
fi
if [[ -n "$SEARCH" ]]; then
  CMD+=(--search "$SEARCH")
fi

"${CMD[@]}"
