#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: preflight_gh.sh [--host <hostname>] [--min-version <version>] [--expect-repo <owner/repo>] [--allow-non-project]

Run prerequisite checks before performing gh commands:
- verify gh is installed (optionally version-gated)
- verify gh authentication for the target host
- optionally verify that the current working directory resolves to the expected owner/repo
- optionally allow running when not inside a git repository
EOF
}

HOST="github.com"
MIN_VERSION=""
EXPECT_REPO=""
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
    --expect-repo)
      EXPECT_REPO="${2:-}"
      if [[ -z "$EXPECT_REPO" ]]; then
        echo "Missing value for --expect-repo" >&2
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
source "$SCRIPT_DIR/github_lib.sh"

if [[ -n "$EXPECT_REPO" ]]; then
  github_require_repo_reference "$EXPECT_REPO"
fi

"$SCRIPT_DIR/check_gh_installed.sh" ${MIN_VERSION:+--min-version "$MIN_VERSION"}
"$SCRIPT_DIR/check_gh_authenticated.sh" --host "$HOST"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Current directory is a git repository."
  REMOTE="$(git remote get-url origin 2>/dev/null || true)"
  if [[ -n "$REMOTE" ]]; then
    echo "origin remote: $REMOTE"

    CURRENT_REPO="$(github_repo_from_remote_url "$REMOTE" || true)"

    if [[ -z "$CURRENT_REPO" ]]; then
      echo "Could not resolve owner/repo from git remote: $REMOTE" >&2
      exit 6
    fi

    if [[ -n "$EXPECT_REPO" && "$CURRENT_REPO" != "$EXPECT_REPO" ]]; then
      echo "Current directory resolves to $CURRENT_REPO, but --expect-repo requires $EXPECT_REPO." >&2
      echo "Run preflight from the target repository working directory, or use a helper script that accepts explicit repo arguments." >&2
      exit 6
    fi
  else
    echo "No origin remote configured."
    if [[ -n "$EXPECT_REPO" ]]; then
      echo "Cannot verify --expect-repo without an origin remote." >&2
      exit 6
    fi
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

if [[ -n "$EXPECT_REPO" ]]; then
  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "--expect-repo requires running from the target repository working directory." >&2
    exit 6
  fi
fi

echo "gh preflight checks passed."
