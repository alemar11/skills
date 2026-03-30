#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: prs_open_current_branch.sh --title <text> [--body <text>] [--base <branch>] [--draft] [--repo <owner/repo>] [--dry-run] [--allow-non-project]
EOF
}

TITLE=""
BODY=""
BASE=""
DRAFT=0
REPO=""
DRY_RUN=0
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
    --base)
      BASE="${2:-}"
      if [[ -z "$BASE" ]]; then
        echo "Missing value for --base" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --draft)
      DRAFT=1
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
    --dry-run)
      DRY_RUN=1
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

if [[ -z "$TITLE" ]]; then
  echo "Missing required --title" >&2
  usage >&2
  exit 64
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/github_lib.sh"

github_require_git_repo
CURRENT_BRANCH="$(github_current_branch)"

if [[ -n "$REPO" ]]; then
  github_require_repo_reference "$REPO"
fi

LOCAL_REPO="$(github_resolve_repo "$SCRIPT_DIR" "" 0)"
TARGET_REPO="$LOCAL_REPO"
if [[ -n "$REPO" && "$REPO" != "$LOCAL_REPO" ]]; then
  echo "Cross-repo PR creation is not supported by prs_open_current_branch.sh. Current checkout resolves to $LOCAL_REPO." >&2
  exit 2
fi

REMOTE_NAME="$(github_tracking_remote_name "$CURRENT_BRANCH")"
REMOTE_BRANCH="$(github_tracking_branch_name "$CURRENT_BRANCH")"

if [[ -z "$REMOTE_NAME" || -z "$REMOTE_BRANCH" ]]; then
  echo "Current branch '$CURRENT_BRANCH' has no configured upstream. Push it before opening a PR." >&2
  exit 5
fi

if [[ "$REMOTE_BRANCH" != "$CURRENT_BRANCH" ]]; then
  echo "Current branch '$CURRENT_BRANCH' tracks '$REMOTE_NAME/$REMOTE_BRANCH'. This helper only supports same-name remote branches." >&2
  exit 5
fi

if ! git ls-remote --exit-code --heads "$REMOTE_NAME" "$CURRENT_BRANCH" >/dev/null 2>&1; then
  echo "Current branch '$CURRENT_BRANCH' is not available on remote '$REMOTE_NAME'. Push it before opening a PR." >&2
  exit 5
fi

if [[ -z "$BASE" ]]; then
  BASE="$(gh repo view "$TARGET_REPO" --json defaultBranchRef -q .defaultBranchRef.name)"
fi

CMD=(gh pr create --repo "$TARGET_REPO" --title "$TITLE" --head "$CURRENT_BRANCH" --base "$BASE")
if [[ -n "$BODY" ]]; then
  CMD+=(--body "$BODY")
fi
if [[ "$DRAFT" -eq 1 ]]; then
  CMD+=(--draft)
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
  printf 'Dry run: would open a PR for %s in %s.\n' "$CURRENT_BRANCH" "$TARGET_REPO"
  printf 'Base: %s\n' "$BASE"
  printf 'Title: %s\n' "$TITLE"
  if [[ -n "$BODY" ]]; then
    printf 'Body: %s\n' "$BODY"
  else
    printf 'Body: (empty)\n'
  fi
  printf 'Draft: %s\n' "$([[ "$DRAFT" -eq 1 ]] && echo yes || echo no)"
  printf 'Command:'
  printf ' %q' "${CMD[@]}"
  printf '\n'
  exit 0
fi

"${CMD[@]}"
