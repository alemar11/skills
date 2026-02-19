#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
if command -v git >/dev/null 2>&1 && git -C "$SCRIPT_DIR" rev-parse --show-toplevel >/dev/null 2>&1; then
  REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
else
  REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd -P)"
fi
DEFAULT_OUT="$REPO_ROOT/_tools/postgres_best_practices/top-postgres-skills.md"
API_URL_BASE="${SKILLS_API_URL:-https://skills.sh/api/search}"

usage() {
  cat >&2 <<'EOF'
Usage: postgres_best_practices_snapshot.sh <limit> [output_file]

Examples:
  ./_tools/postgres_best_practices_snapshot.sh 5
  ./_tools/postgres_best_practices_snapshot.sh 10 /tmp/top-postgres-skills.md
EOF
}

require_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Error: required command not found: $cmd" >&2
    exit 1
  fi
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -lt 1 || $# -gt 2 ]]; then
  usage
  exit 1
fi

require_cmd curl
require_cmd python3

limit="$1"
if ! [[ "$limit" =~ ^[0-9]+$ ]] || (( limit <= 0 )); then
  echo "Error: <limit> must be a positive integer." >&2
  usage
  exit 1
fi

out_file="${2:-$DEFAULT_OUT}"
fetch_limit="$limit"
if (( fetch_limit < 50 )); then
  fetch_limit=50
fi

tmp_json="$(mktemp)"
trap 'rm -f "$tmp_json"' EXIT

curl \
  --fail \
  --silent \
  --show-error \
  --location \
  --retry 3 \
  --retry-delay 2 \
  --retry-connrefused \
  --max-time 30 \
  "${API_URL_BASE}?q=postgres&limit=${fetch_limit}" \
  -o "$tmp_json"

python3 - "$tmp_json" "$limit" "$out_file" <<'PY'
import json
import pathlib
import re
import sys

json_path, limit_raw, out_path = sys.argv[1:4]
limit = int(limit_raw)

try:
    payload = json.loads(pathlib.Path(json_path).read_text(encoding="utf-8"))
except json.JSONDecodeError as exc:
    raise SystemExit(f"Failed to parse skills.sh API response: {exc}")

skills = payload.get("skills", [])
if not isinstance(skills, list):
    raise SystemExit("Invalid skills.sh API response: 'skills' is not a list.")

repo_pattern = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

def safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0

selected = []
seen_ids = set()
for entry in skills:
    skill_id = str(entry.get("skillId", "")).strip()
    name = str(entry.get("name", "")).strip() or skill_id
    item_id = str(entry.get("id", "")).strip()
    source = str(entry.get("source", "")).strip()
    installs = safe_int(entry.get("installs", 0) or 0)
    haystack = f"{skill_id} {name} {item_id}".lower()

    if "postgres" not in haystack:
        continue
    if not source or not repo_pattern.match(source):
        continue
    if not item_id:
        continue
    if item_id in seen_ids:
        continue
    seen_ids.add(item_id)

    selected.append(
        {
            "name": name,
            "id": item_id,
            "source": source,
            "installs": installs,
            "skill_url": f"https://skills.sh/{item_id}",
            "repo_url": f"https://github.com/{source}",
        }
    )

selected.sort(key=lambda s: (-s["installs"], s["id"].lower()))
selected = selected[:limit]

if not selected:
    raise SystemExit("No postgres-related skills found in the API response.")

lines = [
    "# Top Postgres Skills (skills.sh)",
    "",
    "Snapshot of skills matching `postgres` from skills.sh.",
    f"Limit: `{limit}`",
    "",
    "| Rank | Skill | Installs | Source Repo |",
    "| --- | --- | ---: | --- |",
]

for idx, skill in enumerate(selected, start=1):
    lines.append(
        f"| {idx} | [{skill['name']}]({skill['skill_url']}) | "
        f"{skill['installs']} | [{skill['source']}]({skill['repo_url']}) |"
    )

out = pathlib.Path(out_path)
out.parent.mkdir(parents=True, exist_ok=True)
rendered = "\n".join(lines) + "\n"

if out.exists() and out.read_text(encoding="utf-8") == rendered:
    print(f"No snapshot content changes; left unchanged: {out}")
else:
    out.write_text(rendered, encoding="utf-8")
    print(f"Wrote {out}")

for idx, skill in enumerate(selected, start=1):
    print(
        f"{idx}. {skill['name']} | installs={skill['installs']} | "
        f"repo={skill['repo_url']} | skill={skill['skill_url']}"
    )
PY
