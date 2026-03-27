#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source-path=SCRIPTDIR
# shellcheck source=runtime_env.sh
source "$SCRIPT_DIR/runtime_env.sh"

usage() {
  cat <<'EOF'
Usage:
  release_migration.sh [options]

Options:
  --summary TEXT          Released changelog summary. If omitted, derive it
                          from the first bullet in the matching WIP subsection
                          when possible.
  --pending-file NAME     Pending migration file to release.
                          Default: prerelease.sql
  --migrations-path PATH  Override migrations path (absolute or project-root
                          relative).
  --slug TEXT             Collision slug for released filenames.
                          Default: project directory name or pending-file stem
  --timestamp TS          Override UTC timestamp (YYYYMMDDHHMMSS).
                          Mainly useful for deterministic tests
  --dry-run               Print the planned release result without writing
  -h, --help              Show this help text

Notes:
  - Migrations path resolution order:
    1) [database.<profile>].migrations_path from postgres.toml
    2) [migrations].path from postgres.toml
    3) DB_MIGRATIONS_PATH in project AGENTS.md
    4) db/migrations under the project root
  - DB_PROFILE controls profile-specific migrations_path resolution and
    defaults to local when unset.
EOF
}

die() {
  echo "$*" >&2
  exit 1
}

trim() {
  local value="$1"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "$value"
}

sanitize_slug() {
  local raw="$1"
  raw="$(printf '%s' "$raw" | tr '[:upper:]' '[:lower:]')"
  raw="$(printf '%s' "$raw" | sed -E 's/[^a-z0-9]+/_/g; s/^_+//; s/_+$//')"
  if [[ -z "$raw" ]]; then
    raw="migration"
  fi
  printf '%s' "$raw"
}

resolve_agents_migrations_path() {
  local agents_path="$1"
  if [[ ! -f "$agents_path" ]]; then
    return 0
  fi

  awk '
    match($0, /DB_MIGRATIONS_PATH=([^[:space:]]+)/, m) {
      print m[1]
      exit
    }
  ' "$agents_path"
}

resolve_toml_migrations_path() {
  local toml_path="$1"
  local profile="$2"

  if [[ ! -f "$toml_path" ]]; then
    return 0
  fi

  postgres_runtime_python_exec "$toml_path" - "$toml_path" "$profile" <<'PY'
import sys
import tomllib
from pathlib import Path

toml_path = Path(sys.argv[1])
profile = sys.argv[2]

with toml_path.open("rb") as handle:
    data = tomllib.load(handle)

value = ""
database = data.get("database")
if isinstance(database, dict):
    profile_data = database.get(profile)
    if isinstance(profile_data, dict):
        value = str(profile_data.get("migrations_path") or "")

if not value:
    migrations = data.get("migrations")
    if isinstance(migrations, dict):
        value = str(migrations.get("path") or "")

sys.stdout.write(value)
PY
}

resolve_migrations_path() {
  local project_root="$1"
  local profile="$2"
  local override="$3"
  local toml_path="$4"
  local raw="$override"
  local agents_path

  if [[ -z "$raw" ]]; then
    raw="$(resolve_toml_migrations_path "$toml_path" "$profile")"
  fi

  if [[ -z "$raw" ]]; then
    agents_path="${project_root}/AGENTS.md"
    raw="$(resolve_agents_migrations_path "$agents_path")"
  fi

  if [[ -z "$raw" ]]; then
    raw="db/migrations"
  fi

  if [[ "$raw" == /* ]]; then
    printf '%s' "$raw"
    return 0
  fi

  printf '%s/%s' "$project_root" "$raw"
}

pick_release_target() {
  local released_dir="$1"
  local timestamp="$2"
  local slug="$3"
  local target="${released_dir}/${timestamp}.sql"
  local n=1

  if [[ ! -e "$target" ]]; then
    printf '%s' "$target"
    return 0
  fi

  target="${released_dir}/${timestamp}_${slug}.sql"
  while [[ -e "$target" ]]; do
    target="${released_dir}/${timestamp}_${slug}_$(printf '%02d' "$n").sql"
    n=$((n + 1))
  done

  printf '%s' "$target"
}

summary=""
pending_file="prerelease.sql"
migrations_path_override=""
slug=""
timestamp_override=""
dry_run=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --summary)
      [[ $# -ge 2 ]] || die "Missing value for --summary."
      summary="${2:-}"
      shift
      ;;
    --pending-file)
      [[ $# -ge 2 ]] || die "Missing value for --pending-file."
      pending_file="${2:-}"
      shift
      ;;
    --migrations-path)
      [[ $# -ge 2 ]] || die "Missing value for --migrations-path."
      migrations_path_override="${2:-}"
      shift
      ;;
    --slug)
      [[ $# -ge 2 ]] || die "Missing value for --slug."
      slug="${2:-}"
      shift
      ;;
    --timestamp)
      [[ $# -ge 2 ]] || die "Missing value for --timestamp."
      timestamp_override="${2:-}"
      shift
      ;;
    --dry-run)
      dry_run=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage >&2
      die "Unknown option: $1"
      ;;
  esac
  shift
done

project_root="$(postgres_runtime_resolve_project_root)"
if [[ -z "$project_root" ]]; then
  die "Unable to resolve the target project root. Run from the target repo or set DB_PROJECT_ROOT."
fi

profile="${DB_PROFILE:-local}"
toml_path="$(postgres_runtime_resolve_toml_path "$project_root")"
migrations_path="$(resolve_migrations_path "$project_root" "$profile" "$migrations_path_override" "$toml_path")"

released_dir="${migrations_path}/released"
pending_path="${migrations_path}/${pending_file}"
changelog_path="${migrations_path}/CHANGELOG.md"

[[ -f "$pending_path" ]] || die "Pending migration file not found: $pending_path"
if [[ ! -s "$pending_path" ]]; then
  die "Pending migration file is empty: $pending_path"
fi

if [[ -n "$timestamp_override" ]]; then
  [[ "$timestamp_override" =~ ^[0-9]{14}$ ]] || die "--timestamp must use YYYYMMDDHHMMSS."
  timestamp="$timestamp_override"
else
  timestamp="$(date -u +%Y%m%d%H%M%S)"
fi

if [[ -z "$slug" ]]; then
  project_slug="$(basename "$project_root")"
  if [[ "$pending_file" != "prerelease.sql" ]]; then
    project_slug="${pending_file%.*}"
  fi
  slug="$(sanitize_slug "$project_slug")"
else
  slug="$(sanitize_slug "$slug")"
fi

release_target="$(pick_release_target "$released_dir" "$timestamp" "$slug")"
released_filename="$(basename "$release_target")"
release_date="${timestamp:0:4}-${timestamp:4:2}-${timestamp:6:2}"

summary="$(trim "$summary")"
export CHANGELOG_PATH="$changelog_path"
export PENDING_FILE="$pending_file"
export RELEASE_DATE="$release_date"
export RELEASED_FILENAME="$released_filename"
export RELEASE_SUMMARY="$summary"

updated_changelog="$(
  postgres_runtime_python_exec "$toml_path" - <<'PY'
import os
import re
import sys
from pathlib import Path

changelog_path = Path(os.environ["CHANGELOG_PATH"])
pending_file = os.environ["PENDING_FILE"]
release_date = os.environ["RELEASE_DATE"]
released_filename = os.environ["RELEASED_FILENAME"]
release_summary = os.environ["RELEASE_SUMMARY"].strip()

release_heading = f"### {release_date} — `{released_filename}`\n"

if changelog_path.exists():
    text = changelog_path.read_text(encoding="utf-8")
else:
    text = ""

def extract_first_bullet(section_lines, pending_name):
    in_target = False
    for line in section_lines:
        stripped = line.strip()
        if stripped.startswith("### "):
            in_target = stripped == f"### {pending_name}"
            continue
        if in_target and stripped.startswith("- "):
            return stripped[2:].strip()
    return ""

def remove_pending_subsection(section_lines, pending_name):
    new_lines = []
    skipping = False
    for line in section_lines:
        stripped = line.strip()
        if stripped.startswith("### "):
            if skipping:
                skipping = False
            if stripped == f"### {pending_name}":
                skipping = True
                continue
        if skipping:
            continue
        new_lines.append(line)
    while new_lines and not new_lines[-1].strip():
        new_lines.pop()
    return new_lines

if not text.strip():
    wip_lines = []
    released_lines = []
    other_sections = []
else:
    lines = text.splitlines(keepends=True)
    heading_indexes = [
        idx for idx, line in enumerate(lines)
        if re.match(r"^## [^\n]+", line)
    ]
    if any(line.strip() for line in lines[: heading_indexes[0] if heading_indexes else 0]):
        raise SystemExit(
            "CHANGELOG.md contains content before the first top-level section. "
            "Migrate it to the WIP/RELEASED template before running release_migration.sh."
        )

    sections = []
    for pos, start in enumerate(heading_indexes):
        end = heading_indexes[pos + 1] if pos + 1 < len(heading_indexes) else len(lines)
        heading = lines[start]
        title = heading[3:].strip()
        content = lines[start + 1:end]
        sections.append((title, heading, content))

    titles = {title for title, _, _ in sections}
    if "WIP" not in titles or "RELEASED" not in titles:
        raise SystemExit(
            "CHANGELOG.md must use top-level ## WIP and ## RELEASED sections "
            "before running release_migration.sh."
        )

    wip_lines = []
    released_lines = []
    other_sections = []
    for title, heading, content in sections:
        if title == "WIP":
            wip_lines = content
        elif title == "RELEASED":
            released_lines = content
        else:
            other_sections.append((heading, content))

if not release_summary:
    release_summary = extract_first_bullet(wip_lines, pending_file)
if not release_summary:
    release_summary = f"Release {pending_file}."

wip_lines = remove_pending_subsection(wip_lines, pending_file)
release_block = [
    release_heading,
    f"- {release_summary}\n",
    "\n",
]
released_lines = release_block + released_lines

output = []
output.append("## WIP\n")
output.append("\n")
output.extend(wip_lines)
if wip_lines and output[-1] != "\n":
    output.append("\n")
output.append("\n")
output.append("## RELEASED\n")
output.append("\n")
output.extend(released_lines)
if released_lines and output[-1] != "\n":
    output.append("\n")

for heading, content in other_sections:
    if output[-1] != "\n":
      output.append("\n")
    output.append(heading)
    output.extend(content)
    if content and output[-1] != "\n":
      output.append("\n")

result = "".join(output)
result = re.sub(r"\n{3,}", "\n\n", result).rstrip() + "\n"
sys.stdout.write(result)
PY
)"

release_summary="$(
  RELEASE_SUMMARY="$summary" \
  CHANGELOG_PATH="$changelog_path" \
  PENDING_FILE="$pending_file" \
  postgres_runtime_python_exec "$toml_path" - <<'PY'
import os
import re
from pathlib import Path

summary = os.environ["RELEASE_SUMMARY"].strip()
changelog_path = Path(os.environ["CHANGELOG_PATH"])
pending_file = os.environ["PENDING_FILE"]

if summary:
    print(summary, end="")
else:
    derived = ""
    if changelog_path.exists():
        text = changelog_path.read_text(encoding="utf-8")
        in_wip = False
        in_target = False
        for line in text.splitlines():
            stripped = line.strip()
            if re.match(r"^## ", stripped):
                in_wip = stripped == "## WIP"
                in_target = False
                continue
            if not in_wip:
                continue
            if stripped.startswith("### "):
                in_target = stripped == f"### {pending_file}"
                continue
            if in_target and stripped.startswith("- "):
                derived = stripped[2:].strip()
                break
    print(derived or f"Release {pending_file}.", end="")
PY
)"

if [[ "$dry_run" == "1" ]]; then
  cat <<EOF
Project root: $project_root
Profile: $profile
Migrations path: $migrations_path
Pending file: $pending_path
Released file: $release_target
Changelog: $changelog_path
Summary: ${summary:-$release_summary}
Mode: dry-run
EOF
  exit 0
fi

mkdir -p "$released_dir"
mv "$pending_path" "$release_target"
: > "$pending_path"
printf '%s' "$updated_changelog" >"$changelog_path"

cat <<EOF
Released migration file: $release_target
Recreated pending file: $pending_path
Updated changelog: $changelog_path
Summary: ${summary:-$release_summary}
EOF
