#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: publish_context.sh [--repo <owner/repo>] [--json] [--allow-non-project]

Show current repo, branch, upstream, change-count, and open-PR context for the
local checkout. This helper still requires a git repository even when
--allow-non-project is present; the flag is accepted for interface consistency
with the shared GitHub support scripts.
EOF
}

REPO=""
JSON=0
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
    --json)
      JSON=1
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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../core/github_lib.sh"

github_require_git_repo

if [[ -n "$REPO" ]]; then
  github_require_repo_reference "$REPO"
fi

LOCAL_REPO="$(github_resolve_repo "$SCRIPT_DIR" "" 0)"
TARGET_REPO="$LOCAL_REPO"
if [[ -n "$REPO" && "$REPO" != "$LOCAL_REPO" ]]; then
  echo "Cross-repo publish is not supported. Current checkout resolves to $LOCAL_REPO." >&2
  exit 2
fi

DEFAULT_BRANCH="$(gh repo view "$TARGET_REPO" --json defaultBranchRef -q .defaultBranchRef.name)"
HEAD_REF="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
DETACHED_HEAD=0
CURRENT_BRANCH="$HEAD_REF"

if [[ -z "$CURRENT_BRANCH" || "$CURRENT_BRANCH" == "HEAD" ]]; then
  DETACHED_HEAD=1
  CURRENT_BRANCH=""
fi

ON_DEFAULT_BRANCH=0
if [[ "$DETACHED_HEAD" -eq 0 && "$CURRENT_BRANCH" == "$DEFAULT_BRANCH" ]]; then
  ON_DEFAULT_BRANCH=1
fi

CURRENT_BRANCH_IS_LONG_LIVED=0
if [[ "$DETACHED_HEAD" -eq 0 ]] && github_branch_is_long_lived "$CURRENT_BRANCH"; then
  CURRENT_BRANCH_IS_LONG_LIVED=1
fi

UPSTREAM_REMOTE=""
UPSTREAM_BRANCH=""
UPSTREAM_CONFIGURED=0
SAME_NAME_REMOTE=0
AHEAD=0
BEHIND=0

if [[ "$DETACHED_HEAD" -eq 0 ]]; then
  UPSTREAM_REMOTE="$(github_tracking_remote_name "$CURRENT_BRANCH")"
  UPSTREAM_BRANCH="$(github_tracking_branch_name "$CURRENT_BRANCH")"

  if [[ -n "$UPSTREAM_REMOTE" && -n "$UPSTREAM_BRANCH" ]]; then
    UPSTREAM_CONFIGURED=1
    if [[ "$UPSTREAM_BRANCH" == "$CURRENT_BRANCH" ]]; then
      SAME_NAME_REMOTE=1
    fi

    if COUNTS="$(git rev-list --left-right --count HEAD...@{upstream} 2>/dev/null || true)"; then
      if [[ -n "$COUNTS" ]]; then
        read -r AHEAD BEHIND <<<"$COUNTS"
      fi
    fi
  fi
fi

read -r STAGED_COUNT UNSTAGED_COUNT UNTRACKED_COUNT TOTAL_PATHS <<EOF
$(git status --porcelain=v1 | awk '
BEGIN { staged=0; unstaged=0; untracked=0; total=0 }
{
  total++
  if (substr($0, 1, 2) == "??") {
    untracked++
    next
  }
  if (substr($0, 1, 1) != " ") {
    staged++
  }
  if (substr($0, 2, 1) != " ") {
    unstaged++
  }
}
END {
  printf "%d %d %d %d\n", staged, unstaged, untracked, total
}')
EOF

TRACKED_COUNT=$((TOTAL_PATHS - UNTRACKED_COUNT))

PR_NUMBER=""
PR_URL=""
PR_TITLE=""
PR_BASE=""
PR_HEAD=""
PR_DRAFT=""
OPEN_PR=0
RECOMMENDED_PR_BASE=""

if [[ "$DETACHED_HEAD" -eq 0 ]]; then
  PR_ROW="$(gh pr list \
    --repo "$TARGET_REPO" \
    --head "$CURRENT_BRANCH" \
    --state open \
    --json number,url,title,baseRefName,headRefName,isDraft \
    --limit 1 \
    --jq '.[] | [.number, .url, .title, .baseRefName, .headRefName, (.isDraft|tostring)] | @tsv' \
    2>/dev/null || true)"

  if [[ -n "$PR_ROW" ]]; then
    IFS=$'\t' read -r PR_NUMBER PR_URL PR_TITLE PR_BASE PR_HEAD PR_DRAFT <<<"$PR_ROW"
    OPEN_PR=1
  fi
fi

RECOMMENDED_STEP="Keep the current branch, push, then open or reuse the draft PR."
if [[ "$DETACHED_HEAD" -eq 1 ]]; then
  RECOMMENDED_STEP="Create a new short-lived branch before staging because the checkout is detached."
elif [[ "$ON_DEFAULT_BRANCH" -eq 1 ]]; then
  RECOMMENDED_PR_BASE="$DEFAULT_BRANCH"
  RECOMMENDED_STEP="Create a new short-lived branch before staging because the current branch is the default branch, and open the PR against $DEFAULT_BRANCH."
elif [[ "$CURRENT_BRANCH_IS_LONG_LIVED" -eq 1 ]]; then
  RECOMMENDED_PR_BASE="$CURRENT_BRANCH"
  RECOMMENDED_STEP="Create a new short-lived branch from $CURRENT_BRANCH before staging, and open the PR against $CURRENT_BRANCH."
elif [[ "$OPEN_PR" -eq 1 ]]; then
  RECOMMENDED_STEP="Keep the current branch, push the next commit, and reuse the existing PR."
elif [[ "$UPSTREAM_CONFIGURED" -eq 0 ]]; then
  RECOMMENDED_STEP="Keep the current branch, then push with git push -u origin $CURRENT_BRANCH before opening the PR."
fi

if [[ "$JSON" -eq 1 ]]; then
  REPO="$TARGET_REPO" \
  DEFAULT_BRANCH="$DEFAULT_BRANCH" \
  CURRENT_BRANCH="$CURRENT_BRANCH" \
  DETACHED_HEAD="$DETACHED_HEAD" \
  ON_DEFAULT_BRANCH="$ON_DEFAULT_BRANCH" \
  CURRENT_BRANCH_IS_LONG_LIVED="$CURRENT_BRANCH_IS_LONG_LIVED" \
  UPSTREAM_REMOTE="$UPSTREAM_REMOTE" \
  UPSTREAM_BRANCH="$UPSTREAM_BRANCH" \
  UPSTREAM_CONFIGURED="$UPSTREAM_CONFIGURED" \
  SAME_NAME_REMOTE="$SAME_NAME_REMOTE" \
  AHEAD="$AHEAD" \
  BEHIND="$BEHIND" \
  STAGED_COUNT="$STAGED_COUNT" \
  UNSTAGED_COUNT="$UNSTAGED_COUNT" \
  UNTRACKED_COUNT="$UNTRACKED_COUNT" \
  TRACKED_COUNT="$TRACKED_COUNT" \
  TOTAL_PATHS="$TOTAL_PATHS" \
  OPEN_PR="$OPEN_PR" \
  PR_NUMBER="$PR_NUMBER" \
  PR_URL="$PR_URL" \
  PR_TITLE="$PR_TITLE" \
  PR_BASE="$PR_BASE" \
  PR_HEAD="$PR_HEAD" \
  PR_DRAFT="$PR_DRAFT" \
  RECOMMENDED_PR_BASE="$RECOMMENDED_PR_BASE" \
  RECOMMENDED_STEP="$RECOMMENDED_STEP" \
  python3 - <<'PY'
import json
import os

def as_bool(name: str) -> bool:
    return os.environ[name] == "1"

def as_int(name: str) -> int:
    return int(os.environ[name])

data = {
    "repo": os.environ["REPO"],
    "default_branch": os.environ["DEFAULT_BRANCH"],
    "current_branch": os.environ["CURRENT_BRANCH"] or None,
    "detached_head": as_bool("DETACHED_HEAD"),
    "on_default_branch": as_bool("ON_DEFAULT_BRANCH"),
    "current_branch_is_long_lived": as_bool("CURRENT_BRANCH_IS_LONG_LIVED"),
    "upstream": {
        "configured": as_bool("UPSTREAM_CONFIGURED"),
        "remote": os.environ["UPSTREAM_REMOTE"] or None,
        "branch": os.environ["UPSTREAM_BRANCH"] or None,
        "same_name_remote": as_bool("SAME_NAME_REMOTE"),
        "ahead": as_int("AHEAD"),
        "behind": as_int("BEHIND"),
    },
    "changes": {
        "tracked": as_int("TRACKED_COUNT"),
        "staged": as_int("STAGED_COUNT"),
        "unstaged": as_int("UNSTAGED_COUNT"),
        "untracked": as_int("UNTRACKED_COUNT"),
        "total_paths": as_int("TOTAL_PATHS"),
    },
    "open_pr": {
        "exists": as_bool("OPEN_PR"),
        "number": int(os.environ["PR_NUMBER"]) if os.environ["PR_NUMBER"] else None,
        "url": os.environ["PR_URL"] or None,
        "title": os.environ["PR_TITLE"] or None,
        "base": os.environ["PR_BASE"] or None,
        "head": os.environ["PR_HEAD"] or None,
        "is_draft": (os.environ["PR_DRAFT"] == "true") if os.environ["PR_DRAFT"] else None,
    },
    "recommended_pr_base": os.environ["RECOMMENDED_PR_BASE"] or None,
    "recommended_next_step": os.environ["RECOMMENDED_STEP"],
}

print(json.dumps(data, indent=2))
PY
  exit 0
fi

echo "Repo: $TARGET_REPO"
echo "Default branch: $DEFAULT_BRANCH"
if [[ "$DETACHED_HEAD" -eq 1 ]]; then
  echo "Current branch: (detached HEAD)"
else
  echo "Current branch: $CURRENT_BRANCH"
fi
echo "On default branch: $([[ "$ON_DEFAULT_BRANCH" -eq 1 ]] && echo yes || echo no)"
echo "Current branch is long-lived: $([[ "$CURRENT_BRANCH_IS_LONG_LIVED" -eq 1 ]] && echo yes || echo no)"
if [[ "$UPSTREAM_CONFIGURED" -eq 1 ]]; then
  echo "Upstream: $UPSTREAM_REMOTE/$UPSTREAM_BRANCH (ahead $AHEAD, behind $BEHIND)"
else
  echo "Upstream: (none)"
fi
echo "Same-name remote branch: $([[ "$SAME_NAME_REMOTE" -eq 1 ]] && echo yes || echo no)"
echo "Changes: $TOTAL_PATHS path(s) total; staged $STAGED_COUNT, unstaged $UNSTAGED_COUNT, untracked $UNTRACKED_COUNT"
if [[ "$OPEN_PR" -eq 1 ]]; then
  echo "Open PR: #$PR_NUMBER $PR_TITLE"
  echo "PR URL: $PR_URL"
else
  echo "Open PR: none"
fi
if [[ -n "$RECOMMENDED_PR_BASE" ]]; then
  echo "Recommended PR base: $RECOMMENDED_PR_BASE"
fi
echo "Recommended next step: $RECOMMENDED_STEP"
