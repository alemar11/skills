#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: prs_checkout.sh --pr <number> [--branch <name>] [--detach] [--force] [--recurse-submodules] [--repo <owner/repo>] [--allow-non-project]
EOF
}

PR=""
BRANCH=""
DETACH=0
FORCE=0
RECURSE_SUBMODULES=0
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
    --branch)
      BRANCH="${2:-}"
      if [[ -z "$BRANCH" ]]; then
        echo "Missing value for --branch" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --detach)
      DETACH=1
      shift
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --recurse-submodules)
      RECURSE_SUBMODULES=1
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

CMD=(gh pr checkout "$PR" --repo "$TARGET_REPO")
if [[ -n "$BRANCH" ]]; then
  CMD+=(--branch "$BRANCH")
fi
if [[ "$DETACH" -eq 1 ]]; then
  CMD+=(--detach)
fi
if [[ "$FORCE" -eq 1 ]]; then
  CMD+=(--force)
fi
if [[ "$RECURSE_SUBMODULES" -eq 1 ]]; then
  CMD+=(--recurse-submodules)
fi

"${CMD[@]}"
