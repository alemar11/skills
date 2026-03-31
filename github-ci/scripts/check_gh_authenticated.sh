#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: check_gh_authenticated.sh [--host <hostname>]

Check that gh is authenticated against the target host.
Defaults to github.com if --host is omitted.
EOF
}

HOST="github.com"

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
  echo "gh is not installed. Run: gh auth status requires the GitHub CLI." >&2
  echo "Install from: https://github.com/cli/cli#installation" >&2
  exit 2
fi

STATUS="$(gh auth status --hostname "$HOST" 2>&1 || true)"

if echo "$STATUS" | grep -q "Logged in to"; then
  USER="$(echo "$STATUS" | awk -F ' as ' '/Logged in to/ {print $2}')"
  echo "Authenticated to $HOST as ${USER:-<unknown>}."
  echo "$STATUS"
  exit 0
fi

echo "gh is not authenticated for $HOST." >&2
echo "Run: gh auth login --hostname $HOST" >&2
exit 2
