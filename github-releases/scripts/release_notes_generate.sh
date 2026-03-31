#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: release_notes_generate.sh --tag <tag> --target-ref <branch-or-sha> [--repo <owner/repo>] [--previous-tag <tag>] [--workdir <path>] [--title-file <path>] [--notes-file <path>] [--allow-non-project]

Generate draft release title and notes through the GitHub release-notes API.
If --previous-tag is omitted, the latest published release tag is used when available.
EOF
}

TAG=""
TARGET_REF=""
REPO=""
PREVIOUS_TAG=""
WORKDIR=""
TITLE_FILE=""
NOTES_FILE=""
ALLOW_NON_PROJECT=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tag)
      TAG="${2:-}"
      if [[ -z "$TAG" ]]; then
        echo "Missing value for --tag" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --target-ref)
      TARGET_REF="${2:-}"
      if [[ -z "$TARGET_REF" ]]; then
        echo "Missing value for --target-ref" >&2
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
    --previous-tag)
      PREVIOUS_TAG="${2:-}"
      if [[ -z "$PREVIOUS_TAG" ]]; then
        echo "Missing value for --previous-tag" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --workdir)
      WORKDIR="${2:-}"
      if [[ -z "$WORKDIR" ]]; then
        echo "Missing value for --workdir" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --title-file)
      TITLE_FILE="${2:-}"
      if [[ -z "$TITLE_FILE" ]]; then
        echo "Missing value for --title-file" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --notes-file)
      NOTES_FILE="${2:-}"
      if [[ -z "$NOTES_FILE" ]]; then
        echo "Missing value for --notes-file" >&2
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

if [[ -z "$TAG" || -z "$TARGET_REF" ]]; then
  echo "Missing required arguments: --tag and --target-ref are required." >&2
  usage >&2
  exit 64
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/github_lib.sh"

if [[ -n "$REPO" ]]; then
  github_require_repo_reference "$REPO"
fi

TARGET_REPO="$(github_resolve_repo "$SCRIPT_DIR" "$REPO" "$ALLOW_NON_PROJECT")"

if [[ -z "$PREVIOUS_TAG" ]]; then
  PREVIOUS_TAG="$(gh release list --repo "$TARGET_REPO" --exclude-drafts --exclude-pre-releases --json tagName --limit 1 --jq '.[0].tagName' || true)"
  if [[ "$PREVIOUS_TAG" == "null" ]]; then
    PREVIOUS_TAG=""
  fi
fi

if [[ -z "$WORKDIR" && ( -z "$TITLE_FILE" || -z "$NOTES_FILE" ) ]]; then
  WORKDIR="${TMPDIR:-/tmp}/gh-release-notes-${RANDOM}"
fi

if [[ -n "$WORKDIR" ]]; then
  mkdir -p "$WORKDIR"
fi

if [[ -z "$TITLE_FILE" ]]; then
  TITLE_FILE="$WORKDIR/release_title.txt"
fi
if [[ -z "$NOTES_FILE" ]]; then
  NOTES_FILE="$WORKDIR/release_notes.md"
fi

mkdir -p "$(dirname "$TITLE_FILE")" "$(dirname "$NOTES_FILE")"

PAYLOAD_FILE="$(mktemp)"
trap 'rm -f "$PAYLOAD_FILE"' EXIT

API_CMD=(
  gh api "repos/$TARGET_REPO/releases/generate-notes"
  -X POST
  -f "tag_name=$TAG"
  -f "target_commitish=$TARGET_REF"
)
if [[ -n "$PREVIOUS_TAG" ]]; then
  API_CMD+=(-f "previous_tag_name=$PREVIOUS_TAG")
fi

"${API_CMD[@]}" >"$PAYLOAD_FILE"

python3 - "$PAYLOAD_FILE" "$TITLE_FILE" "$NOTES_FILE" <<'PY'
import json
import sys
from pathlib import Path

payload_path = Path(sys.argv[1])
title_path = Path(sys.argv[2])
notes_path = Path(sys.argv[3])

with payload_path.open() as fh:
    payload = json.load(fh)

title = (payload.get("name") or "").strip()
body = payload.get("body") or ""

title_path.write_text(title + ("\n" if title else ""), encoding="utf-8")
notes_path.write_text(body, encoding="utf-8")
PY

echo "Repository:   $TARGET_REPO"
echo "Tag:          $TAG"
echo "Target ref:   $TARGET_REF"
if [[ -n "$PREVIOUS_TAG" ]]; then
  echo "Previous tag: $PREVIOUS_TAG"
else
  echo "Previous tag: <none found>"
fi
echo "Title file:   $TITLE_FILE"
echo "Notes file:   $NOTES_FILE"
echo
echo "Draft title:"
cat "$TITLE_FILE"
echo
echo "Draft notes preview:"
sed -n '1,80p' "$NOTES_FILE"
