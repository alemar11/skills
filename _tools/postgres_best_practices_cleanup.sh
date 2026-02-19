#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
if command -v git >/dev/null 2>&1 && git -C "$SCRIPT_DIR" rev-parse --show-toplevel >/dev/null 2>&1; then
  REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
else
  REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd -P)"
fi
ARTIFACT_DIR="$REPO_ROOT/_tools/postgres_best_practices"
DRY_RUN=false

usage() {
  cat <<'EOF'
Usage: postgres_best_practices_cleanup.sh [--dry-run]

Options:
  --dry-run   Print files that would be deleted without deleting them.
  -h, --help  Show this help message.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=true
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Error: unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
  shift
done

artifacts=(
  "$ARTIFACT_DIR/top-postgres-skills.md"
  "$ARTIFACT_DIR/sources-reviewed.md"
  "$ARTIFACT_DIR/verification.md"
)

removed_count=0
for file in "${artifacts[@]}"; do
  if [[ -f "$file" ]]; then
    if $DRY_RUN; then
      echo "Would remove $file"
    else
      rm -f "$file"
      echo "Removed $file"
    fi
    (( removed_count += 1 ))
  fi
done

if [[ "$removed_count" -eq 0 ]]; then
  echo "No maintenance artifacts found to remove."
elif $DRY_RUN; then
  echo "Dry run complete. ${removed_count} artifact(s) matched."
fi
