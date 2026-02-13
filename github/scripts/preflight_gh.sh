#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: preflight_gh.sh [--host <hostname>] [--min-version <version>] [--allow-non-project]

Run prerequisite checks before performing gh commands:
- verify gh is installed (optionally version-gated)
- verify gh authentication for the target host
- optionally allow running when not inside a git repository
EOF
}

HOST="github.com"
MIN_VERSION=""
REQUIRE_GIT_REPO=1
ALLOW_NON_PROJECT=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host)
      HOST="${2:-}"
      if [[ -z "$HOST" ]]; then
        echo "Missing value for --host" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --min-version)
      MIN_VERSION="${2:-}"
      if [[ -z "$MIN_VERSION" ]]; then
        echo "Missing value for --min-version" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --allow-non-project)
      ALLOW_NON_PROJECT=1
      REQUIRE_GIT_REPO=0
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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"$SCRIPT_DIR/check_gh_installed.sh" ${MIN_VERSION:+--min-version "$MIN_VERSION"}
"$SCRIPT_DIR/check_gh_authenticated.sh" --host "$HOST"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Current directory is a git repository."
  REMOTE="$(git remote get-url origin 2>/dev/null || true)"
  if [[ -n "$REMOTE" ]]; then
    echo "origin remote: $REMOTE"
  else
    echo "No origin remote configured."
  fi
elif [[ "$REQUIRE_GIT_REPO" -eq 1 ]]; then
  if [[ "$ALLOW_NON_PROJECT" -eq 1 ]]; then
    echo "Current directory is not a git repository. Proceeding with non-project operations."
  else
    echo "No git repository found in the current directory."
    echo "By default this skill is project-scoped."
    echo "Ask the user: create a git repository first or continue with non-project operations?"
    echo "Use --allow-non-project to explicitly permit non-project operations."
    exit 3
  fi
else
  echo "Current directory is not a git repository. Proceeding with non-project operations."
fi

echo "gh preflight checks passed."
