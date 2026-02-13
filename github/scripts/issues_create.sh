#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: issues_create.sh --title <text> [--body <text>] [--labels <label1,label2>] [--assignees <user1,user2>] [--repo <owner/repo>] [--allow-non-project]
  --title     required
EOF
}

TITLE=""
BODY=""
LABELS=""
ASSIGNEES=""
REPO=""
ALLOW_NON_PROJECT=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --title)
      TITLE="${2:-}"
      if [[ -z "$TITLE" ]]; then
        echo "Missing value for --title" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --body)
      BODY="${2:-}"
      if [[ -z "$BODY" ]]; then
        echo "Missing value for --body" >&2
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
    --assignees)
      ASSIGNEES="${2:-}"
      if [[ -z "$ASSIGNEES" ]]; then
        echo "Missing value for --assignees" >&2
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

if [[ -z "$TITLE" ]]; then
  echo "Missing required --title" >&2
  usage >&2
  exit 64
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/github_lib.sh"

if [[ -n "$REPO" ]]; then
  github_require_repo_reference "$REPO"
fi
TARGET_REPO="$(github_resolve_repo "$SCRIPT_DIR" "$REPO" "$ALLOW_NON_PROJECT")"

CMD=(gh issue create --repo "$TARGET_REPO" --title "$TITLE")
if [[ -n "$BODY" ]]; then
  CMD+=(--body "$BODY")
fi
if [[ -n "$LABELS" ]]; then
  CMD+=(--label "$LABELS")
fi
if [[ -n "$ASSIGNEES" ]]; then
  CMD+=(--assignee "$ASSIGNEES")
fi

"${CMD[@]}"
