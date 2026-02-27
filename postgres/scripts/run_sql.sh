#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  cat <<'EOF'
Usage:
  run_sql.sh -c "select 1;"
  run_sql.sh -f ./query.sql
  run_sql.sh < query.sql
  run_sql.sh -- -v myvar=123

Notes:
  - Exactly one of -c/--command or -f/--file may be used.
  - If neither is provided, SQL is read from stdin.
  - Additional args after -- are forwarded to psql.
EOF
}

missing_option_value() {
  local option="$1"
  echo "Missing value for ${option}." >&2
  usage >&2
  exit 1
}

sql_cmd=""
sql_file=""
passthrough=()
psql_args=(
  -v ON_ERROR_STOP=1
)

while [[ $# -gt 0 ]]; do
  case "$1" in
    -c|--command)
      if [[ $# -lt 2 ]]; then
        missing_option_value "$1"
      fi
      case "$2" in
        -c|--command|-f|--file|-h|--help|--)
          missing_option_value "$1"
          ;;
      esac
      sql_cmd="${2:-}"
      shift
      ;;
    -f|--file)
      if [[ $# -lt 2 ]]; then
        missing_option_value "$1"
      fi
      case "$2" in
        -c|--command|-f|--file|-h|--help|--)
          missing_option_value "$1"
          ;;
      esac
      sql_file="${2:-}"
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    --)
      shift
      passthrough+=("$@")
      break
      ;;
    *)
      passthrough+=("$1")
      ;;
  esac
  shift
done

if [[ -n "$sql_cmd" && -n "$sql_file" ]]; then
  echo "Use either -c/--command or -f/--file, not both." >&2
  usage
  exit 1
fi

if [[ -n "$sql_file" && ! -f "$sql_file" ]]; then
  echo "SQL file not found: $sql_file" >&2
  exit 1
fi

if (( ${#passthrough[@]} > 0 )); then
  psql_args+=("${passthrough[@]}")
fi

if [[ -n "$sql_cmd" ]]; then
  "$SCRIPT_DIR/psql_with_ssl_fallback.sh" \
    "${psql_args[@]}" \
    -c "$sql_cmd"
  exit 0
fi

if [[ -n "$sql_file" ]]; then
  "$SCRIPT_DIR/psql_with_ssl_fallback.sh" \
    "${psql_args[@]}" \
    -f "$sql_file"
  exit 0
fi

if [[ -t 0 ]]; then
  echo "No SQL provided. Pass -c, -f, or pipe SQL through stdin." >&2
  usage
  exit 1
fi

"$SCRIPT_DIR/psql_with_ssl_fallback.sh" \
  "${psql_args[@]}" \
  -f -
