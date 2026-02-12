#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEFAULT_OUT="$REPO_ROOT/_tools/postgres_best_practices/top-postgres-skills.md"

usage() {
  cat >&2 <<'EOF'
Usage: postgres_best_practices_snapshot.sh <limit> [output_file]

Examples:
  ./_tools/postgres_best_practices_snapshot.sh 5
  ./_tools/postgres_best_practices_snapshot.sh 10 /tmp/top-postgres-skills.md
EOF
}

if [[ $# -lt 1 || $# -gt 2 ]]; then
  usage
  exit 1
fi

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

curl -fsSL "https://skills.sh/api/search?q=postgres&limit=${fetch_limit}" -o "$tmp_json"

python3 - "$tmp_json" "$limit" "$out_file" <<'PY'
import datetime
import json
import pathlib
import sys

json_path, limit_raw, out_path = sys.argv[1:4]
limit = int(limit_raw)

with open(json_path, "r", encoding="utf-8") as fh:
    payload = json.load(fh)

skills = payload.get("skills", [])
selected = []
for entry in skills:
    skill_id = str(entry.get("skillId", "")).strip()
    name = str(entry.get("name", "")).strip() or skill_id
    item_id = str(entry.get("id", "")).strip()
    source = str(entry.get("source", "")).strip()
    installs = int(entry.get("installs", 0) or 0)
    haystack = f"{skill_id} {name} {item_id}".lower()

    if "postgres" not in haystack:
        continue
    if not source or "/" not in source:
        continue
    if not item_id:
        continue

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
    if len(selected) >= limit:
        break

if not selected:
    raise SystemExit("No postgres-related skills found in the API response.")

generated_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
lines = [
    "# Top Postgres Skills (skills.sh)",
    "",
    f"Generated from skills.sh on {generated_at}.",
    "",
    "Query: `postgres`",
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
out.write_text("\n".join(lines) + "\n", encoding="utf-8")

for idx, skill in enumerate(selected, start=1):
    print(
        f"{idx}. {skill['name']} | installs={skill['installs']} | "
        f"repo={skill['repo_url']} | skill={skill['skill_url']}"
    )
print(f"Wrote {out}")
PY
