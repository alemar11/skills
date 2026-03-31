#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: release_create.sh --tag <tag> --target-ref <branch-or-sha> --notes-mode <infer|blank|user> [options]

Create a GitHub release with an explicit target and explicit notes strategy.

Options:
  --repo <owner/repo>        operate on a specific repository
  --title <text>             set the release title directly
  --title-file <path>        read the release title from a file
  --notes-file <path>        read release notes from a file
  --notes-text <text>        use inline release notes text
  --previous-tag <tag>       explicit previous tag when notes-mode=infer
  --allow-non-project        allow running outside a git repository

This helper intentionally requires --notes-mode.
Do not treat omitted notes strategy as delegation.
EOF
}

TAG=""
TARGET_REF=""
NOTES_MODE=""
REPO=""
TITLE=""
TITLE_FILE=""
NOTES_FILE=""
NOTES_TEXT=""
PREVIOUS_TAG=""
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
    --notes-mode)
      NOTES_MODE="${2:-}"
      if [[ -z "$NOTES_MODE" ]]; then
        echo "Missing value for --notes-mode" >&2
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
    --title)
      TITLE="${2:-}"
      if [[ -z "$TITLE" ]]; then
        echo "Missing value for --title" >&2
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
    --notes-text)
      NOTES_TEXT="${2:-}"
      if [[ -z "$NOTES_TEXT" ]]; then
        echo "Missing value for --notes-text" >&2
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

if [[ -z "$TAG" || -z "$TARGET_REF" || -z "$NOTES_MODE" ]]; then
  echo "Missing required arguments: --tag, --target-ref, and --notes-mode are required." >&2
  usage >&2
  exit 64
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/github_lib.sh"

if [[ -n "$REPO" ]]; then
  github_require_repo_reference "$REPO"
fi
github_require_allowed_value "notes-mode" "$NOTES_MODE" infer blank user

if [[ -n "$TITLE" && -n "$TITLE_FILE" ]]; then
  echo "Use either --title or --title-file, not both." >&2
  exit 64
fi

TARGET_REPO="$(github_resolve_repo "$SCRIPT_DIR" "$REPO" "$ALLOW_NON_PROJECT")"

CMD=(gh release create "$TAG" --repo "$TARGET_REPO" --target "$TARGET_REF" --fail-on-no-commits)

if [[ -n "$TITLE" ]]; then
  CMD+=(-t "$TITLE")
elif [[ -n "$TITLE_FILE" ]]; then
  CMD+=(-t "$(cat "$TITLE_FILE")")
fi

case "$NOTES_MODE" in
  infer)
    if [[ -n "$NOTES_FILE" ]]; then
      CMD+=(-F "$NOTES_FILE")
    elif [[ -n "$PREVIOUS_TAG" ]]; then
      CMD+=(--generate-notes --notes-start-tag "$PREVIOUS_TAG")
    else
      CMD+=(--generate-notes)
    fi
    ;;
  blank)
    if [[ -n "$NOTES_FILE" || -n "$NOTES_TEXT" ]]; then
      echo "--notes-file/--notes-text are not valid with --notes-mode blank." >&2
      exit 64
    fi
    CMD+=(--notes "")
    ;;
  user)
    if [[ -n "$NOTES_FILE" ]]; then
      CMD+=(-F "$NOTES_FILE")
    elif [[ -n "$NOTES_TEXT" ]]; then
      CMD+=(--notes "$NOTES_TEXT")
    else
      echo "For --notes-mode user, provide either --notes-file or --notes-text." >&2
      exit 64
    fi
    ;;
esac

"${CMD[@]}"
gh release view "$TAG" --repo "$TARGET_REPO" --json url,tagName,targetCommitish,name
