#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  cat <<'EOF'
Usage: find_objects.sh <pattern> [--types type1,type2]

Examples:
  DB_PROFILE=local ./scripts/find_objects.sh users
  DB_PROFILE=local ./scripts/find_objects.sh auth --types table,column,view

Optional env:
  DB_FIND_OBJECT_TYPES=table,column,view
EOF
}

pattern=""
types="${DB_FIND_OBJECT_TYPES:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    -t|--types)
      if [[ $# -lt 2 ]]; then
        echo "Error: --types requires a comma-separated value." >&2
        usage >&2
        exit 1
      fi
      types="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      echo "Error: unknown option '$1'." >&2
      usage >&2
      exit 1
      ;;
    *)
      if [[ -n "$pattern" ]]; then
        echo "Error: unexpected extra argument '$1'." >&2
        usage >&2
        exit 1
      fi
      pattern="$1"
      shift
      ;;
  esac
done

if [[ -z "$pattern" ]]; then
  usage >&2
  exit 1
fi

# If the user didn't pass an explicit ILIKE wildcard, make it a contains match.
if [[ "$pattern" != *"%"* && "$pattern" != *"_"* ]]; then
  pattern="%${pattern}%"
fi

"$SCRIPT_DIR/psql_with_ssl_fallback.sh" \
  -q \
  -v ON_ERROR_STOP=1 \
  -v "pattern=$pattern" \
  -v "types=$types" \
  -f "$SCRIPT_DIR/find_objects.sql"
