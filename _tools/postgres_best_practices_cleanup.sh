#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ARTIFACT_DIR="$REPO_ROOT/_tools/postgres_best_practices"

artifacts=(
  "$ARTIFACT_DIR/top-postgres-skills.md"
  "$ARTIFACT_DIR/sources-reviewed.md"
  "$ARTIFACT_DIR/verification.md"
)

removed=0
for file in "${artifacts[@]}"; do
  if [[ -f "$file" ]]; then
    rm -f "$file"
    echo "Removed $file"
    removed=1
  fi
done

if [[ "$removed" -eq 0 ]]; then
  echo "No maintenance artifacts found to remove."
fi
