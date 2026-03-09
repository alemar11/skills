#!/usr/bin/env sh

set -eu

if [ "$(uname -s)" != "Darwin" ]; then
  echo "This script is intended for macOS only." >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEST_DIR="$HOME/.agents/skills"

mkdir -p "$DEST_DIR"

echo "Linking local skills from: $ROOT_DIR"
echo "Target directory: $DEST_DIR"
echo

count=0
skip_count=0

for skill_dir in "$ROOT_DIR"/*; do
  [ -d "$skill_dir" ] || continue
  [ -f "$skill_dir/SKILL.md" ] || continue

  skill_name="$(basename "$skill_dir")"
  target_path="$DEST_DIR/$skill_name"
  count=$((count + 1))

  if [ -L "$target_path" ]; then
    rm -f "$target_path"
  elif [ -e "$target_path" ]; then
    echo "$count) SKIP $skill_name -> $target_path already exists (not a symlink)"
    skip_count=$((skip_count + 1))
    continue
  fi

  ln -s "$skill_dir" "$target_path"
  echo "$count) LINK $skill_name -> $target_path"
done

echo
echo "Completed. created: $count, skipped: $skip_count"
