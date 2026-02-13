#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: issues_labels_create.sh --name <label> [--color <rrggbb>] [--description <text>] [--repo <owner/repo>] [--allow-non-project]
EOF
}

NAME=""
COLOR=""
DESCRIPTION=""
REPO=""
ALLOW_NON_PROJECT=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name)
      NAME="${2:-}"
      if [[ -z "$NAME" ]]; then
        echo "Missing value for --name" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --color)
      COLOR="${2:-}"
      if [[ -z "$COLOR" ]]; then
        echo "Missing value for --color" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --description)
      DESCRIPTION="${2:-}"
      if [[ -z "$DESCRIPTION" ]]; then
        echo "Missing value for --description" >&2
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

if [[ -z "$NAME" ]]; then
  echo "Missing required --name" >&2
  usage >&2
  exit 64
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/github_lib.sh"

if [[ -n "$REPO" ]]; then
  github_require_repo_reference "$REPO"
fi

if [[ -n "$COLOR" ]]; then
  COLOR="$(github_normalize_hex_color "$COLOR")"
fi

TARGET_REPO="$(github_resolve_repo "$SCRIPT_DIR" "$REPO" "$ALLOW_NON_PROJECT")"

CMD=(gh label create --repo "$TARGET_REPO" --name "$NAME")
if [[ -n "$COLOR" ]]; then
  CMD+=(--color "$COLOR")
fi
if [[ -n "$DESCRIPTION" ]]; then
  CMD+=(--description "$DESCRIPTION")
fi

"${CMD[@]}"
