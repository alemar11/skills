#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: release_plan.sh [--repo <owner/repo>] [--target-branch <branch>] [--allow-non-project]

Resolve the repository default branch, target branch, target HEAD commit,
and latest published release tag before creating a release.
EOF
}

REPO=""
TARGET_BRANCH=""
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
    --target-branch)
      TARGET_BRANCH="${2:-}"
      if [[ -z "$TARGET_BRANCH" ]]; then
        echo "Missing value for --target-branch" >&2
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

TARGET_REPO="$(github_resolve_repo "$SCRIPT_DIR" "$REPO" "$ALLOW_NON_PROJECT")"
DEFAULT_BRANCH="$(gh repo view "$TARGET_REPO" --json defaultBranchRef -q .defaultBranchRef.name)"

if [[ -z "$TARGET_BRANCH" ]]; then
  TARGET_BRANCH="$DEFAULT_BRANCH"
fi

TARGET_SHA="$(gh api "repos/$TARGET_REPO/commits/$TARGET_BRANCH" --jq '.sha')"
TARGET_SUBJECT="$(gh api "repos/$TARGET_REPO/commits/$TARGET_BRANCH" --jq '.commit.message | split("\n")[0]')"
PREVIOUS_TAG="$(gh release list --repo "$TARGET_REPO" --exclude-drafts --exclude-pre-releases --json tagName --limit 1 --jq '.[0].tagName' || true)"

echo "Repository:      $TARGET_REPO"
echo "Default branch:  $DEFAULT_BRANCH"
echo "Target branch:   $TARGET_BRANCH"
echo "Target commit:   ${TARGET_SHA:0:7} $TARGET_SUBJECT"
if [[ -n "$PREVIOUS_TAG" && "$PREVIOUS_TAG" != "null" ]]; then
  echo "Previous tag:    $PREVIOUS_TAG"
else
  echo "Previous tag:    <none found>"
fi
