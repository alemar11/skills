#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: prs_update.sh --pr <number> [--title <text>] [--body <text>] [--base <branch>] [--milestone <name>] [--remove-milestone] [--add-labels <label1,label2>] [--remove-labels <label1,label2>] [--add-assignees <user1,user2>] [--remove-assignees <user1,user2>] [--add-reviewers <user1,user2>] [--remove-reviewers <user1,user2>] [--repo <owner/repo>] [--allow-non-project]
EOF
}

PR=""
TITLE=""
BODY=""
BASE=""
MILESTONE=""
REMOVE_MILESTONE=0
ADD_LABELS=""
REMOVE_LABELS=""
ADD_ASSIGNEES=""
REMOVE_ASSIGNEES=""
ADD_REVIEWERS=""
REMOVE_REVIEWERS=""
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
    --milestone)
      MILESTONE="${2:-}"
      if [[ -z "$MILESTONE" ]]; then
        echo "Missing value for --milestone" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --remove-milestone)
      REMOVE_MILESTONE=1
      shift
      ;;
    --add-labels)
      ADD_LABELS="${2:-}"
      if [[ -z "$ADD_LABELS" ]]; then
        echo "Missing value for --add-labels" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --remove-labels)
      REMOVE_LABELS="${2:-}"
      if [[ -z "$REMOVE_LABELS" ]]; then
        echo "Missing value for --remove-labels" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --add-assignees)
      ADD_ASSIGNEES="${2:-}"
      if [[ -z "$ADD_ASSIGNEES" ]]; then
        echo "Missing value for --add-assignees" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --remove-assignees)
      REMOVE_ASSIGNEES="${2:-}"
      if [[ -z "$REMOVE_ASSIGNEES" ]]; then
        echo "Missing value for --remove-assignees" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --add-reviewers)
      ADD_REVIEWERS="${2:-}"
      if [[ -z "$ADD_REVIEWERS" ]]; then
        echo "Missing value for --add-reviewers" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --remove-reviewers)
      REMOVE_REVIEWERS="${2:-}"
      if [[ -z "$REMOVE_REVIEWERS" ]]; then
        echo "Missing value for --remove-reviewers" >&2
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

if [[ -z "$TITLE" && -z "$BODY" && -z "$BASE" && -z "$MILESTONE" && "$REMOVE_MILESTONE" -eq 0 && -z "$ADD_LABELS" && -z "$REMOVE_LABELS" && -z "$ADD_ASSIGNEES" && -z "$REMOVE_ASSIGNEES" && -z "$ADD_REVIEWERS" && -z "$REMOVE_REVIEWERS" ]]; then
  echo "At least one update field is required: --title, --body, --base, --milestone, --remove-milestone, --add-labels, --remove-labels, --add-assignees, --remove-assignees, --add-reviewers, or --remove-reviewers." >&2
  usage >&2
  exit 64
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/github_lib.sh"

if [[ -n "$REPO" ]]; then
  github_require_repo_reference "$REPO"
fi
github_require_pr_number "$PR"

if [[ -n "$MILESTONE" && "$REMOVE_MILESTONE" -eq 1 ]]; then
  echo "Use either --milestone or --remove-milestone, not both." >&2
  exit 64
fi

TARGET_REPO="$(github_resolve_repo "$SCRIPT_DIR" "$REPO" "$ALLOW_NON_PROJECT")"

CMD=(gh pr edit "$PR" --repo "$TARGET_REPO")
if [[ -n "$TITLE" ]]; then
  CMD+=(--title "$TITLE")
fi
if [[ -n "$BODY" ]]; then
  CMD+=(--body "$BODY")
fi
if [[ -n "$BASE" ]]; then
  CMD+=(--base "$BASE")
fi
if [[ -n "$MILESTONE" ]]; then
  CMD+=(--milestone "$MILESTONE")
fi
if [[ "$REMOVE_MILESTONE" -eq 1 ]]; then
  CMD+=(--remove-milestone)
fi
if [[ -n "$ADD_LABELS" ]]; then
  CMD+=(--add-label "$ADD_LABELS")
fi
if [[ -n "$REMOVE_LABELS" ]]; then
  CMD+=(--remove-label "$REMOVE_LABELS")
fi
if [[ -n "$ADD_ASSIGNEES" ]]; then
  CMD+=(--add-assignee "$ADD_ASSIGNEES")
fi
if [[ -n "$REMOVE_ASSIGNEES" ]]; then
  CMD+=(--remove-assignee "$REMOVE_ASSIGNEES")
fi
if [[ -n "$ADD_REVIEWERS" ]]; then
  CMD+=(--add-reviewer "$ADD_REVIEWERS")
fi
if [[ -n "$REMOVE_REVIEWERS" ]]; then
  CMD+=(--remove-reviewer "$REMOVE_REVIEWERS")
fi

"${CMD[@]}"
