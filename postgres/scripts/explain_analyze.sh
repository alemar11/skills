#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/pg_env.sh"

eval "$("$SCRIPT_DIR/resolve_db_url.sh")"

mode="analyze"
query=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -n|--no-analyze)
      mode="plan"
      shift
      ;;
    -h|--help)
      cat <<'USAGE'
Usage:
  explain_analyze.sh [--no-analyze] "<sql>"

Options:
  --no-analyze   Run EXPLAIN (no ANALYZE). Safer for write queries.
USAGE
      exit 0
      ;;
    *)
      query="$1"
      shift
      ;;
  esac
done

if [[ -z "$query" ]]; then
  echo "Usage: explain_analyze.sh [--no-analyze] \"<sql>\"" >&2
  exit 1
fi

if [[ "$mode" == "plan" ]]; then
  psql "$DB_URL" -v ON_ERROR_STOP=1 -X \
    -c "EXPLAIN (BUFFERS) $query"
else
  psql "$DB_URL" -v ON_ERROR_STOP=1 -X \
    -c "EXPLAIN (ANALYZE, BUFFERS) $query"
fi
