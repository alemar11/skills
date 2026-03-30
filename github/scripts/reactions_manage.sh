#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: reactions_manage.sh --resource pr|issue|issue-comment|pr-review-comment --repo <owner/repo> [--number <n>|--comment-id <id>] [--list|--add <reaction>|--remove <reaction-id>] [--dry-run] [--json] [--allow-non-project]
EOF
}

RESOURCE=""
REPO=""
NUMBER=""
COMMENT_ID=""
LIST=0
ADD=""
REMOVE_ID=""
DRY_RUN=0
JSON=0
ALLOW_NON_PROJECT=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --resource)
      RESOURCE="${2:-}"
      if [[ -z "$RESOURCE" ]]; then
        echo "Missing value for --resource" >&2
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
    --number)
      NUMBER="${2:-}"
      if [[ -z "$NUMBER" ]]; then
        echo "Missing value for --number" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --comment-id)
      COMMENT_ID="${2:-}"
      if [[ -z "$COMMENT_ID" ]]; then
        echo "Missing value for --comment-id" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --list)
      LIST=1
      shift
      ;;
    --add)
      ADD="${2:-}"
      if [[ -z "$ADD" ]]; then
        echo "Missing value for --add" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --remove)
      REMOVE_ID="${2:-}"
      if [[ -z "$REMOVE_ID" ]]; then
        echo "Missing value for --remove" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
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

if [[ -z "$RESOURCE" || -z "$REPO" ]]; then
  echo "Both --resource and --repo are required." >&2
  usage >&2
  exit 64
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/github_lib.sh"

github_require_repo_reference "$REPO"
github_require_allowed_value "resource" "$RESOURCE" pr issue issue-comment pr-review-comment

ACTION_COUNT=0
if [[ "$LIST" -eq 1 ]]; then
  ACTION_COUNT=$((ACTION_COUNT + 1))
fi
if [[ -n "$ADD" ]]; then
  ACTION_COUNT=$((ACTION_COUNT + 1))
fi
if [[ -n "$REMOVE_ID" ]]; then
  ACTION_COUNT=$((ACTION_COUNT + 1))
fi

if [[ "$ACTION_COUNT" -ne 1 ]]; then
  echo "Choose exactly one of --list, --add, or --remove." >&2
  exit 64
fi

if [[ "$RESOURCE" == "pr" || "$RESOURCE" == "issue" ]]; then
  if [[ -z "$NUMBER" || -n "$COMMENT_ID" ]]; then
    echo "--resource $RESOURCE requires --number and does not accept --comment-id." >&2
    exit 64
  fi
  github_require_positive_int "number" "$NUMBER"
else
  if [[ -z "$COMMENT_ID" || -n "$NUMBER" ]]; then
    echo "--resource $RESOURCE requires --comment-id and does not accept --number." >&2
    exit 64
  fi
  github_require_positive_int "comment-id" "$COMMENT_ID"
fi

if [[ -n "$ADD" ]]; then
  github_require_allowed_value "add" "$ADD" +1 -1 laugh confused heart hooray rocket eyes
fi
if [[ -n "$REMOVE_ID" ]]; then
  github_require_positive_int "remove" "$REMOVE_ID"
fi

TARGET_REPO="$(github_resolve_repo "$SCRIPT_DIR" "$REPO" "$ALLOW_NON_PROJECT")"

case "$RESOURCE" in
  pr|issue)
    BASE_ENDPOINT="repos/$TARGET_REPO/issues/$NUMBER/reactions"
    TARGET_LABEL="$RESOURCE $TARGET_REPO#$NUMBER"
    ;;
  issue-comment)
    BASE_ENDPOINT="repos/$TARGET_REPO/issues/comments/$COMMENT_ID/reactions"
    TARGET_LABEL="$RESOURCE $TARGET_REPO comment $COMMENT_ID"
    ;;
  pr-review-comment)
    BASE_ENDPOINT="repos/$TARGET_REPO/pulls/comments/$COMMENT_ID/reactions"
    TARGET_LABEL="$RESOURCE $TARGET_REPO comment $COMMENT_ID"
    ;;
esac

if [[ "$LIST" -eq 1 ]]; then
  python3 - "$BASE_ENDPOINT" "$TARGET_LABEL" "$JSON" <<'PY'
import json
import subprocess
import sys

endpoint, target_label, json_mode_raw = sys.argv[1:4]
json_mode = bool(int(json_mode_raw))

def fetch_page(page: int) -> list[dict]:
    cmd = [
        "gh",
        "api",
        endpoint,
        "-X",
        "GET",
        "-F",
        "per_page=100",
        "-F",
        f"page={page}",
        "-H",
        "Accept: application/vnd.github+json",
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode != 0:
        message = (proc.stderr or proc.stdout or "").strip()
        print(message or "gh api failed", file=sys.stderr)
        raise SystemExit(proc.returncode)
    try:
        payload = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError as exc:
        print(f"Failed to parse gh api output: {exc}", file=sys.stderr)
        raise SystemExit(1)
    if not isinstance(payload, list):
        print("Unexpected reactions response shape.", file=sys.stderr)
        raise SystemExit(1)
    return payload

items = []
page = 1
while True:
    page_items = fetch_page(page)
    if not page_items:
        break
    for item in page_items:
        if not isinstance(item, dict):
            continue
        items.append(
            {
                "id": item.get("id"),
                "content": item.get("content") or "",
                "user": ((item.get("user") or {}).get("login") or ""),
            }
        )
    if len(page_items) < 100:
        break
    page += 1

if json_mode:
    print(json.dumps(items, indent=2))
    raise SystemExit(0)

print(f"Reactions: {target_label}")
print(f"Count: {len(items)}")
for item in items:
    print(f"- id={item['id']} {item['content']} by {item['user'] or 'unknown'}")
PY
  exit 0
fi

if [[ -n "$ADD" ]]; then
  if [[ "$DRY_RUN" -eq 1 ]]; then
    if [[ "$JSON" -eq 1 ]]; then
      printf '{\n  "action": "add",\n  "target": "%s",\n  "content": "%s"\n}\n' "$TARGET_LABEL" "$ADD"
    else
      printf 'Dry run: would add reaction %s to %s.\n' "$ADD" "$TARGET_LABEL"
    fi
    exit 0
  fi

  RESPONSE="$(gh api -X POST "$BASE_ENDPOINT" -H "Accept: application/vnd.github+json" -f content="$ADD")"
  if [[ "$JSON" -eq 1 ]]; then
    printf '%s\n' "$RESPONSE"
  else
    printf 'Added reaction %s to %s.\n' "$ADD" "$TARGET_LABEL"
  fi
  exit 0
fi

DELETE_ENDPOINT="$BASE_ENDPOINT/$REMOVE_ID"
if [[ "$DRY_RUN" -eq 1 ]]; then
  if [[ "$JSON" -eq 1 ]]; then
    printf '{\n  "action": "remove",\n  "target": "%s",\n  "reaction_id": %s\n}\n' "$TARGET_LABEL" "$REMOVE_ID"
  else
    printf 'Dry run: would remove reaction %s from %s.\n' "$REMOVE_ID" "$TARGET_LABEL"
  fi
  exit 0
fi

gh api -X DELETE "$DELETE_ENDPOINT" -H "Accept: application/vnd.github+json" >/dev/null
if [[ "$JSON" -eq 1 ]]; then
  printf '{\n  "action": "remove",\n  "target": "%s",\n  "reaction_id": %s,\n  "status": "deleted"\n}\n' "$TARGET_LABEL" "$REMOVE_ID"
else
  printf 'Removed reaction %s from %s.\n' "$REMOVE_ID" "$TARGET_LABEL"
fi
