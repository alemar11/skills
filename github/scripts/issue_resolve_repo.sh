#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/github_lib.sh"

usage() {
  cat <<'EOF'
Usage: issue_resolve_repo.sh [--repo <owner/repo>] [--allow-non-project]

Output the target repository in owner/repo format.
Defaults from git remote origin in the current project.
EOF
}

REPO=""
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

if [[ -n "$REPO" ]]; then
  github_require_repo_reference "$REPO"
  echo "$REPO"
  exit 0
fi

if [[ "$ALLOW_NON_PROJECT" -eq 1 ]]; then
  echo "repo is required when using --allow-non-project." >&2
  exit 2
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "No git repository detected. Pass --repo <owner/repo> for non-project operations." >&2
  exit 3
fi

REMOTE="$(git remote get-url origin 2>/dev/null || true)"

if [[ -z "$REMOTE" ]]; then
  echo "No origin remote found. Pass --repo <owner/repo>." >&2
  exit 4
fi

REPO="$(printf '%s\n' "$REMOTE" \
  | sed -E 's#^git@[^:]+:##; s#^https?://[^/]+/##; s#^ssh://[^/]+/##; s#^git://[^/]+/##; s#\\.git$##; s#/$##')"

if [[ -z "$REPO" || "$REPO" != */* || "$REPO" == */ || "$REPO" == */*/* ]]; then
  echo "Could not resolve owner/repo from git remote: $REMOTE" >&2
  exit 5
fi

echo "$REPO"
