#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: prs_review.sh --pr <number> [--approve|--request-changes|--comment] [--body <text>] [--repo <owner/repo>] [--allow-non-project]
EOF
}

PR=""
ACTION=""
BODY=""
REPO=""
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
    --approve)
      if [[ -n "$ACTION" ]]; then
        echo "Choose exactly one review action: --approve, --request-changes, or --comment." >&2
        usage >&2
        exit 64
      fi
      ACTION="approve"
      shift
      ;;
    --request-changes)
      if [[ -n "$ACTION" ]]; then
        echo "Choose exactly one review action: --approve, --request-changes, or --comment." >&2
        usage >&2
        exit 64
      fi
      ACTION="request-changes"
      shift
      ;;
    --comment)
      if [[ -n "$ACTION" ]]; then
        echo "Choose exactly one review action: --approve, --request-changes, or --comment." >&2
        usage >&2
        exit 64
      fi
      ACTION="comment"
      shift
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

if [[ -z "$PR" ]]; then
  echo "Missing required --pr" >&2
  usage >&2
  exit 64
fi

if [[ -z "$ACTION" ]]; then
  echo "Choose exactly one review action: --approve, --request-changes, or --comment." >&2
  usage >&2
  exit 64
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/github_lib.sh"

if [[ -n "$REPO" ]]; then
  github_require_repo_reference "$REPO"
fi
github_require_pr_number "$PR"
TARGET_REPO="$(github_resolve_repo "$SCRIPT_DIR" "$REPO" "$ALLOW_NON_PROJECT")"

CMD=(gh pr review "$PR" --repo "$TARGET_REPO")
if [[ "$ACTION" == "approve" ]]; then
  CMD+=(--approve)
elif [[ "$ACTION" == "request-changes" ]]; then
  CMD+=(--request-changes)
else
  CMD+=(--comment)
fi

if [[ -n "$BODY" ]]; then
  CMD+=(--body "$BODY")
fi

"${CMD[@]}"
