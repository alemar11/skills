#!/usr/bin/env bash
set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This script is intended for macOS only." >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
TARGET_DIR="$HOME/Developer"
TARGET_LINK="$TARGET_DIR/Skills"

mkdir -p "$TARGET_DIR"

realpath_py() {
  python3 - <<'PY' "$1"
import os
import sys
print(os.path.realpath(sys.argv[1]))
PY
}

if [[ -L "$TARGET_LINK" ]]; then
  existing_target="$(readlink "$TARGET_LINK")"
  existing_real="$(realpath_py "$existing_target")"
  root_real="$(realpath_py "$ROOT_DIR")"
  if [[ "$existing_real" == "$root_real" ]]; then
    echo "Symlink already set: $TARGET_LINK -> $ROOT_DIR"
    exit 0
  fi
  echo "Symlink already exists and points elsewhere: $TARGET_LINK -> $existing_target" >&2
  echo "Remove it or choose a different target." >&2
  exit 1
fi

if [[ -d "$TARGET_LINK" && ! -L "$TARGET_LINK" ]]; then
  if [[ -z "$(ls -A "$TARGET_LINK")" ]]; then
    rmdir "$TARGET_LINK"
  else
    echo "Target path exists as a non-empty directory: $TARGET_LINK" >&2
    echo "Move or remove it before running this script." >&2
    exit 1
  fi
elif [[ -e "$TARGET_LINK" ]]; then
  echo "Target path exists and is not a symlink: $TARGET_LINK" >&2
  echo "Move or remove it before running this script." >&2
  exit 1
fi

ln -s "$ROOT_DIR" "$TARGET_LINK"
echo "Created symlink: $TARGET_LINK -> $ROOT_DIR"
