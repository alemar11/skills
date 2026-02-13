#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: issues_update.sh --issue <number> [--title <text>] [--body <text>] [--state open|closed] [--type bug|task|none] [--type-label-bug <name>] [--type-label-task <name>] [--milestone <name>|--milestone-id <number>] [--remove-milestone] [--add-labels <label1,label2>] [--remove-labels <label1,label2>] [--assignees <user1,user2>] [--remove-assignees <user1,user2>] [--repo <owner/repo>] [--allow-non-project]
EOF
}

ISSUE=""
TITLE=""
BODY=""
STATE=""
TYPE=""
MILESTONE=""
MILESTONE_ID=""
REMOVE_MILESTONE=0
ADD_LABELS=""
REMOVE_LABELS=""
ASSIGNEES=""
REMOVE_ASSIGNEES=""
TYPE_LABEL_BUG="bug"
TYPE_LABEL_TASK="task"
REPO=""
ALLOW_NON_PROJECT=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --issue)
      ISSUE="${2:-}"
      if [[ -z "$ISSUE" ]]; then
        echo "Missing value for --issue" >&2
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
    --state)
      STATE="${2:-}"
      if [[ -z "$STATE" ]]; then
        echo "Missing value for --state" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --type)
      TYPE="${2:-}"
      if [[ -z "$TYPE" ]]; then
        echo "Missing value for --type" >&2
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
    --milestone-id)
      MILESTONE_ID="${2:-}"
      if [[ -z "$MILESTONE_ID" ]]; then
        echo "Missing value for --milestone-id" >&2
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
    --assignees)
      ASSIGNEES="${2:-}"
      if [[ -z "$ASSIGNEES" ]]; then
        echo "Missing value for --assignees" >&2
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
    --type-label-bug)
      TYPE_LABEL_BUG="${2:-}"
      if [[ -z "$TYPE_LABEL_BUG" ]]; then
        echo "Missing value for --type-label-bug" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --type-label-task)
      TYPE_LABEL_TASK="${2:-}"
      if [[ -z "$TYPE_LABEL_TASK" ]]; then
        echo "Missing value for --type-label-task" >&2
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

if [[ -z "$ISSUE" ]]; then
  echo "Missing required --issue" >&2
  usage >&2
  exit 64
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/github_lib.sh"

if [[ -n "$REPO" ]]; then
  github_require_repo_reference "$REPO"
fi
github_require_issue_number "$ISSUE"

if [[ -z "$TITLE" && -z "$BODY" && -z "$STATE" && -z "$TYPE" && -z "$MILESTONE" && -z "$MILESTONE_ID" && "$REMOVE_MILESTONE" -eq 0 && -z "$ADD_LABELS" && -z "$REMOVE_LABELS" && -z "$ASSIGNEES" && -z "$REMOVE_ASSIGNEES" ]]; then
  echo "At least one update field is required: --title, --body, --state, --type, --milestone, --milestone-id, --remove-milestone, --add-labels, --remove-labels, --assignees, or --remove-assignees." >&2
  usage >&2
  exit 64
fi

if [[ -n "$STATE" ]]; then
  github_require_allowed_value "state" "$STATE" open closed
fi

if [[ -n "$TYPE" ]]; then
  github_require_allowed_value "type" "$TYPE" bug task none
fi

if [[ -n "$MILESTONE_ID" ]]; then
  github_require_positive_int "milestone-id" "$MILESTONE_ID"
fi

if [[ "$TYPE_LABEL_BUG" == "$TYPE_LABEL_TASK" ]]; then
  echo "--type-label-bug and --type-label-task must be different label names." >&2
  exit 64
fi

if [[ -n "$MILESTONE" && -n "$MILESTONE_ID" ]]; then
  echo "Use either --milestone or --milestone-id, not both." >&2
  exit 64
fi

if [[ -n "$MILESTONE" || -n "$MILESTONE_ID" ]] && [[ "$REMOVE_MILESTONE" -eq 1 ]]; then
  echo "Use either --milestone / --milestone-id or --remove-milestone, not both." >&2
  exit 64
fi

TARGET_REPO="$(github_resolve_repo "$SCRIPT_DIR" "$REPO" "$ALLOW_NON_PROJECT")"

CMD=(gh issue edit "$ISSUE" --repo "$TARGET_REPO")
if [[ -n "$TITLE" ]]; then
  CMD+=(--title "$TITLE")
fi
if [[ -n "$BODY" ]]; then
  CMD+=(--body "$BODY")
fi
if [[ -n "$STATE" ]]; then
  if [[ "$STATE" == "open" ]]; then
    CMD+=(--reopen)
  else
    CMD+=(--close)
  fi
fi
if [[ -n "$MILESTONE" ]]; then
  CMD+=(--milestone "$MILESTONE")
fi
if [[ -n "$MILESTONE_ID" ]]; then
  CMD+=(--milestone "$MILESTONE_ID")
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
if [[ -n "$ASSIGNEES" ]]; then
  CMD+=(--add-assignee "$ASSIGNEES")
fi
if [[ -n "$REMOVE_ASSIGNEES" ]]; then
  CMD+=(--remove-assignee "$REMOVE_ASSIGNEES")
fi

if [[ -n "$TYPE" ]]; then
  if [[ "$TYPE" == "none" ]]; then
    if [[ -n "$TYPE_LABEL_BUG" ]]; then
      CMD+=(--remove-label "$TYPE_LABEL_BUG")
    fi
    if [[ -n "$TYPE_LABEL_TASK" ]]; then
      CMD+=(--remove-label "$TYPE_LABEL_TASK")
    fi
  elif [[ "$TYPE" == "bug" ]]; then
    if [[ -n "$TYPE_LABEL_TASK" ]]; then
      CMD+=(--remove-label "$TYPE_LABEL_TASK")
    fi
    if [[ -n "$TYPE_LABEL_BUG" ]]; then
      CMD+=(--add-label "$TYPE_LABEL_BUG")
    fi
  else
    if [[ -n "$TYPE_LABEL_BUG" ]]; then
      CMD+=(--remove-label "$TYPE_LABEL_BUG")
    fi
    if [[ -n "$TYPE_LABEL_TASK" ]]; then
      CMD+=(--add-label "$TYPE_LABEL_TASK")
    fi
  fi
fi

"${CMD[@]}"
