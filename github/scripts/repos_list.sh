#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: repos_list.sh [--owner <owner>] [--type all|owner|member|public|private|forks|archived|sources] [--all] [--limit N] [--allow-non-project]

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

github_require_allowed_value "type" "$TYPE" all owner member public private forks archived sources
github_require_positive_int "limit" "$LIMIT"

if [[ "$ALL" -eq 1 ]]; then
  LIMIT=1000
fi

if [[ "$ALLOW_NON_PROJECT" -eq 1 ]]; then
  "$SCRIPT_DIR/preflight_gh.sh" --allow-non-project >&2
else
  "$SCRIPT_DIR/preflight_gh.sh" >&2
fi

ENDPOINT=""
API_TYPE="$TYPE"
FILTER_MODE="$TYPE"
SERVER_FILTERED=1
ENDPOINT_KIND="self"

if [[ -n "$OWNER" ]]; then
  ENDPOINT="users/$OWNER/repos"

  if gh api "orgs/$OWNER" --silent >/dev/null 2>&1; then
    ENDPOINT="orgs/$OWNER/repos"
    ENDPOINT_KIND="org"
  else
    ENDPOINT_KIND="user"
  fi
else
  ENDPOINT="user/repos"
fi

case "$ENDPOINT_KIND:$TYPE" in
  self:public|self:private|self:forks|self:sources|self:archived|user:public|user:private|user:forks|user:sources|user:archived|org:archived)
    API_TYPE="all"
    SERVER_FILTERED=0
    ;;
esac

python3 - "$LIMIT" "$FILTER_MODE" "$ENDPOINT" "$API_TYPE" "$SERVER_FILTERED" <<'PY'
import json
import subprocess
import sys

limit = int(sys.argv[1])
filter_mode = sys.argv[2]
endpoint = sys.argv[3]
api_type = sys.argv[4]
server_filtered = bool(int(sys.argv[5]))

def fetch_page(page: int, per_page: int) -> list[dict]:
    cmd = [
        "gh",
        "api",
        endpoint,
        "-X",
        "GET",
        "-F",
        f"per_page={per_page}",
        "-F",
        f"page={page}",
    ]
    if api_type:
        cmd.extend(["-F", f"type={api_type}"])
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
        print("Unexpected gh api response shape.", file=sys.stderr)
        raise SystemExit(1)
    return payload

def matches(repo):
    if filter_mode == "all":
        return True
    if filter_mode == "owner":
        return True
    if filter_mode == "public":
        return not repo.get("private", False)
    if filter_mode == "private":
        return bool(repo.get("private", False))
    if filter_mode == "forks":
        return bool(repo.get("fork", False))
    if filter_mode == "sources":
        return not repo.get("fork", False)
    if filter_mode == "archived":
        return bool(repo.get("archived", False))
    if filter_mode == "member":
        return True
    return True

per_page = min(limit, 100) if server_filtered else 100

count = 0
page = 1
while count < limit:
    items = fetch_page(page, per_page)
    if not items:
        break
    for repo in items:
        if not isinstance(repo, dict) or not matches(repo):
            continue
        payload = {
            "name": repo.get("name"),
            "full_name": repo.get("full_name"),
            "private": repo.get("private"),
            "visibility": repo.get("visibility"),
            "fork": repo.get("fork"),
            "archived": repo.get("archived"),
            "owner": ((repo.get("owner") or {}).get("login")),
        }
        print(json.dumps(payload, separators=(",", ":")))
        count += 1
        if count >= limit:
            break
    if len(items) < per_page:
        break
    page += 1
PY
