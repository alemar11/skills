#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: prs_checks.sh --pr <number> [--required] [--watch] [--interval <seconds>] [--fail-fast] [--json <fields>] [--repo <owner/repo>] [--allow-non-project]
EOF
}

PR=""
REQUIRED=0
WATCH=0
INTERVAL=""
FAIL_FAST=0
JSON=""
REPO=""
ALLOW_NON_PROJECT=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pr)
      PR="${2:-}"
      if [[ -z "$PR" ]]; then
        echo "Missing value for --pr" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --required)
      REQUIRED=1
      shift
      ;;
    --watch)
      WATCH=1
      shift
      ;;
    --interval)
      INTERVAL="${2:-}"
      if [[ -z "$INTERVAL" ]]; then
        echo "Missing value for --interval" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --fail-fast)
      FAIL_FAST=1
      shift
      ;;
    --json)
      JSON="${2:-}"
      if [[ -z "$JSON" ]]; then
        echo "Missing value for --json" >&2
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

if [[ -z "$PR" ]]; then
  echo "Missing required --pr" >&2
  usage >&2
  exit 64
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/github_lib.sh"

if [[ -n "$REPO" ]]; then
  github_require_repo_reference "$REPO"
fi
github_require_pr_number "$PR"
if [[ -n "$INTERVAL" ]]; then
  github_require_positive_int "interval" "$INTERVAL"
fi

TARGET_REPO="$(github_resolve_repo "$SCRIPT_DIR" "$REPO" "$ALLOW_NON_PROJECT")"

CMD=(gh pr checks "$PR" --repo "$TARGET_REPO")
if [[ "$REQUIRED" -eq 1 ]]; then
  CMD+=(--required)
fi
if [[ "$WATCH" -eq 1 ]]; then
  CMD+=(--watch)
fi
if [[ -n "$INTERVAL" ]]; then
  CMD+=(--interval "$INTERVAL")
fi
if [[ "$FAIL_FAST" -eq 1 ]]; then
  CMD+=(--fail-fast)
fi
if [[ -n "$JSON" ]]; then
  CMD+=(--json "$JSON")
fi

"${CMD[@]}"
