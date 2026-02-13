#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: prs_merge.sh --pr <number> [--merge|--squash|--rebase] [--delete-branch] [--admin] [--auto] [--repo <owner/repo>] [--allow-non-project]
EOF
}

PR=""
METHOD=""
DELETE_BRANCH=0
ADMIN=0
AUTO=0
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
    --merge)
      METHOD="merge"
      shift
      ;;
    --squash)
      METHOD="squash"
      shift
      ;;
    --rebase)
      METHOD="rebase"
      shift
      ;;
    --delete-branch)
      DELETE_BRANCH=1
      shift
      ;;
    --admin)
      ADMIN=1
      shift
      ;;
    --auto)
      AUTO=1
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

if [[ -z "$PR" ]]; then
  echo "Missing required --pr" >&2
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

if [[ "$METHOD" == "merge" ]]; then
  METHOD_FLAG=(--merge)
elif [[ "$METHOD" == "squash" ]]; then
  METHOD_FLAG=(--squash)
elif [[ "$METHOD" == "rebase" ]]; then
  METHOD_FLAG=(--rebase)
else
  METHOD_FLAG=()
fi

CMD=(gh pr merge "$PR" --repo "$TARGET_REPO")
if [[ ${#METHOD_FLAG[@]} -gt 0 ]]; then
  CMD+=("${METHOD_FLAG[@]}")
fi
if [[ "$DELETE_BRANCH" -eq 1 ]]; then
  CMD+=(--delete-branch)
fi
if [[ "$ADMIN" -eq 1 ]]; then
  CMD+=(--admin)
fi
if [[ "$AUTO" -eq 1 ]]; then
  CMD+=(--auto)
fi

"${CMD[@]}"
