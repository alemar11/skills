#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: check_gh_installed.sh [--min-version <version>]

Check that the GitHub CLI is installed.
If --min-version is provided, verify gh version is at least that value.
EOF
}

MIN_VERSION=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --min-version)
      MIN_VERSION="${2:-}"
      if [[ -z "$MIN_VERSION" ]]; then
        echo "Missing value for --min-version" >&2
        usage >&2
        exit 64
      fi
      shift 2
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

if ! command -v gh >/dev/null 2>&1; then
  echo "gh is not installed." >&2
  echo "Install from: https://github.com/cli/cli#installation" >&2
  exit 2
fi

VERSION="$(gh --version | awk 'NR==1 {print $3}')"

if [[ -z "$VERSION" ]]; then
  echo "gh is installed, but version detection failed." >&2
  exit 3
fi

if [[ -n "$MIN_VERSION" ]]; then
  LOWEST="$(printf '%s\n%s\n' "$MIN_VERSION" "$VERSION" | sort -V | head -n1)"
  if [[ "$LOWEST" != "$MIN_VERSION" ]]; then
    echo "gh version $VERSION is older than required $MIN_VERSION." >&2
    exit 4
  fi
  echo "gh is installed: $VERSION (meets minimum $MIN_VERSION)."
else
  echo "gh is installed: $VERSION."
fi
