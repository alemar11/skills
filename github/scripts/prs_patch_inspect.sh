#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: prs_patch_inspect.sh --pr <number> [--repo <owner/repo>] [--path <file>] [--include-patch] [--json] [--allow-non-project]
EOF
}

PR=""
REPO=""
PATH_FILTER=""
INCLUDE_PATCH=0
JSON=0
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
    --repo)
      REPO="${2:-}"
      if [[ -z "$REPO" ]]; then
        echo "Missing value for --repo" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --path)
      PATH_FILTER="${2:-}"
      if [[ -z "$PATH_FILTER" ]]; then
        echo "Missing value for --path" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --include-patch)
      INCLUDE_PATCH=1
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

python3 - "$TARGET_REPO" "$PR" "$PATH_FILTER" "$INCLUDE_PATCH" "$JSON" <<'PY'
import json
import subprocess
import sys

repo, pr, path_filter, include_patch_raw, json_mode_raw = sys.argv[1:6]
include_patch = bool(int(include_patch_raw))
json_mode = bool(int(json_mode_raw))

def gh_api_json(path: str, page: int) -> list[dict]:
    cmd = [
        "gh",
        "api",
        f"repos/{repo}/pulls/{pr}/files",
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
        print("Unexpected pull request files response shape.", file=sys.stderr)
        raise SystemExit(1)
    return payload

items = []
page = 1
while True:
    page_items = gh_api_json(repo, page)
    if not page_items:
        break
    items.extend(page_items)
    if len(page_items) < 100:
        break
    page += 1

normalized = []
for item in items:
    if not isinstance(item, dict):
        continue
    filename = item.get("filename") or ""
    if path_filter and filename != path_filter:
        continue
    entry = {
        "path": filename,
        "status": item.get("status") or "",
        "additions": int(item.get("additions") or 0),
        "deletions": int(item.get("deletions") or 0),
        "changes": int(item.get("changes") or 0),
        "blob_url": item.get("blob_url") or "",
    }
    if include_patch:
        entry["patch"] = item.get("patch") or ""
    normalized.append(entry)

if path_filter and not normalized:
    print(f"No changed file matched path '{path_filter}' in {repo}#{pr}.", file=sys.stderr)
    raise SystemExit(1)

if json_mode:
    print(json.dumps(normalized, indent=2))
    raise SystemExit(0)

print(f"Pull request files: {repo}#{pr}")
print(f"Files returned: {len(normalized)}")
for item in normalized:
    print(
        f"- {item['path']} [{item['status']}] +{item['additions']} -{item['deletions']} ({item['changes']})"
    )
    print(f"  URL: {item['blob_url'] or '(none)'}")
    if include_patch:
        patch = item.get("patch") or ""
        print("  Patch:")
        if patch:
            for line in patch.splitlines():
                print(f"    {line}")
        else:
            print("    (no patch available)")
PY
