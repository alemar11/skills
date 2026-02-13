#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: repos_list.sh [--owner <owner>] [--type all|public|private|forks|archived|sources|member] [--all] [--limit N] [--allow-non-project]

List repositories.
- If --owner is omitted, list repositories for the authenticated user.
- If --owner is provided, list repositories visible to that user/org.
- --type controls visibility/membership scope.
- --all maps to 1000 results for repo listing.
EOF
}

OWNER=""
TYPE="all"
ALL=0
LIMIT=100
ALLOW_NON_PROJECT=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --owner)
      OWNER="${2:-}"
      if [[ -z "$OWNER" ]]; then
        echo "Missing value for --owner" >&2
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
    --all)
      ALL=1
      shift
      ;;
    --limit)
      LIMIT="${2:-}"
      if [[ -z "$LIMIT" ]]; then
        echo "Missing value for --limit" >&2
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

if [[ -n "$OWNER" ]]; then
  if [[ "$OWNER" == */* ]]; then
    echo "Invalid --owner value '$OWNER'. Use a plain owner name." >&2
    exit 64
  fi
fi

github_require_allowed_value "type" "$TYPE" all public private forks archived sources member
github_require_positive_int "limit" "$LIMIT"

if [[ "$ALL" -eq 1 ]]; then
  LIMIT=1000
fi

"$SCRIPT_DIR/preflight_gh.sh" ${ALLOW_NON_PROJECT:+--allow-non-project}

if [[ -n "$OWNER" ]]; then
  TARGET_ENDPOINT="users/$OWNER/repos"
  TARGET_TYPE="$TYPE"
  TARGET_FILTER='.'

  if gh api "orgs/$OWNER" >/dev/null 2>&1; then
    TARGET_ENDPOINT="orgs/$OWNER/repos"
  else
    case "$TYPE" in
      all|owner|member)
        TARGET_TYPE="$TYPE"
        ;;
      public|private|forks|sources|archived)
        TARGET_TYPE="all"
        ;;
    esac

    case "$TYPE" in
      public)
        TARGET_FILTER='select(.private == false)'
        ;;
      private)
        TARGET_FILTER='select(.private == true)'
        ;;
      forks)
        TARGET_FILTER='select(.fork == true)'
        ;;
      sources)
        TARGET_FILTER='select(.fork == false)'
        ;;
      archived)
        TARGET_FILTER='select(.archived == true)'
        ;;
    esac
  fi

  gh api "$TARGET_ENDPOINT" -X GET --paginate -F type="$TARGET_TYPE" -F per_page="$LIMIT" --jq ".[] | $TARGET_FILTER | {name: .name, full_name: .full_name, private: .private, visibility: .visibility, fork: .fork, archived: .archived, owner: .owner.login}"
else
  TARGET_ENDPOINT="user/repos"
  TARGET_TYPE="$TYPE"
  TARGET_FILTER='.'

  case "$TYPE" in
    all|owner|member)
      TARGET_TYPE="$TYPE"
      ;;
    public|private|forks|sources|archived)
      TARGET_TYPE="all"
      ;;
  esac

  case "$TYPE" in
    public)
      TARGET_FILTER='select(.private == false)'
      ;;
    private)
      TARGET_FILTER='select(.private == true)'
      ;;
    forks)
      TARGET_FILTER='select(.fork == true)'
      ;;
    sources)
      TARGET_FILTER='select(.fork == false)'
      ;;
    archived)
      TARGET_FILTER='select(.archived == true)'
      ;;
  esac

  gh api "$TARGET_ENDPOINT" -X GET --paginate -F type="$TARGET_TYPE" -F per_page="$LIMIT" --jq ".[] | $TARGET_FILTER | {name: .name, full_name: .full_name, private: .private, visibility: .visibility, fork: .fork, archived: .archived, owner: .owner.login}"
fi
