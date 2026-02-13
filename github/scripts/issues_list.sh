#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: issues_list.sh [--state open|closed|all] [--labels <label1,label2>] [--limit N] [--repo <owner/repo>] [--allow-non-project]
EOF
}

STATE="open"
LABELS=""
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
    --labels)
      LABELS="${2:-}"
      if [[ -z "$LABELS" ]]; then
        echo "Missing value for --labels" >&2
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

github_require_allowed_value "state" "$STATE" open closed all
github_require_positive_int "limit" "$LIMIT"
TARGET_REPO="$(github_resolve_repo "$SCRIPT_DIR" "$REPO" "$ALLOW_NON_PROJECT")"

CMD=(gh issue list --repo "$TARGET_REPO" --state "$STATE" --json number,title,state,labels,assignees,url,updatedAt --jq '.')
if [[ -n "$LABELS" ]]; then
  CMD+=(--label "$LABELS")
fi
if [[ -n "$LIMIT" ]]; then
  CMD+=(--limit "$LIMIT")
fi

"${CMD[@]}"
