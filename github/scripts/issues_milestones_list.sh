#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: issues_milestones_list.sh [--repo <owner/repo>] [--state open|closed|all] [--limit N] [--allow-non-project]
EOF
}

STATE="open"
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

if [[ "$STATE" == "all" ]]; then
  gh api "repos/$TARGET_REPO/milestones" -X GET --paginate -F per_page="$LIMIT" --jq '.[] | {number: .number, title: .title, state: .state, description: .description, dueOn: .due_on, closedAt: .closed_at}'
else
  gh api "repos/$TARGET_REPO/milestones" -X GET --paginate -F state="$STATE" -F per_page="$LIMIT" --jq '.[] | {number: .number, title: .title, state: .state, description: .description, dueOn: .due_on, closedAt: .closed_at}'
fi
