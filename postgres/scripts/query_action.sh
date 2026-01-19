#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  cat <<'EOF'
Usage:
  query_action.sh <cancel|terminate> --query "<substring>" [--user "<name>"] [--limit N]
  query_action.sh <cancel|terminate> --user "<name>" [--limit N]

Examples:
  ./scripts/query_action.sh cancel --query "select * from events"
  ./scripts/query_action.sh terminate --user app_user --limit 10
EOF
}

action=""
pattern=""
user=""
limit=20

while [[ $# -gt 0 ]]; do
  case "$1" in
    cancel|terminate)
      action="$1"
      ;;
    --query)
      pattern="${2:-}"
      shift
      ;;
    --user)
      user="${2:-}"
      shift
      ;;
    --limit)
      limit="${2:-}"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
  shift
done

if [[ -z "$action" || ( -z "$pattern" && -z "$user" ) ]]; then
  usage
  exit 1
fi

if ! [[ "$limit" =~ ^[0-9]+$ ]]; then
  echo "Invalid limit: $limit" >&2
  exit 1
fi

sql_filter="state <> 'idle' and pid <> pg_backend_pid()"
if [[ -n "$pattern" ]]; then
  sql_filter+=" and query ilike '%' || :'pattern' || '%'"
fi
if [[ -n "$user" ]]; then
  sql_filter+=" and usename = :'user'"
fi

rows="$("$SCRIPT_DIR/psql_with_ssl_fallback.sh" \
  -v ON_ERROR_STOP=1 \
  -v "pattern=${pattern}" \
  -v "user=${user}" \
  -F $'\t' -At \
  -c "
select
  pid,
  usename,
  datname,
  state,
  now() - query_start as query_age,
  left(query, 200) as query
from pg_stat_activity
where ${sql_filter}
order by query_start desc nulls last
limit ${limit};")"

if [[ -z "$rows" ]]; then
  echo "No matching active queries."
  exit 0
fi

echo "Candidates:"
printf "%-8s %-16s %-16s %-10s %-12s %s\n" "PID" "USER" "DB" "STATE" "AGE" "QUERY"
while IFS=$'\t' read -r pid ruser db state age query; do
  printf "%-8s %-16s %-16s %-10s %-12s %s\n" "$pid" "$ruser" "$db" "$state" "$age" "$query"
done <<<"$rows"

read -r -p "Enter PID(s) to ${action} (space-separated), or empty to abort: " pids_input || true
if [[ -z "$pids_input" ]]; then
  echo "Aborted."
  exit 1
fi

valid_pids=()
for pid in $pids_input; do
  if [[ "$pid" =~ ^[0-9]+$ ]]; then
    valid_pids+=("$pid")
  else
    echo "Invalid PID: $pid" >&2
    exit 1
  fi
done

confirm="${DB_CONFIRM:-}"
if [[ "$confirm" != "YES" ]]; then
  if [[ -t 0 ]]; then
    read -r -p "Type YES to ${action} PID(s): ${valid_pids[*]}: " confirm
  fi
fi

if [[ "$confirm" != "YES" ]]; then
  echo "Aborted. Set DB_CONFIRM=YES to skip prompt." >&2
  exit 1
fi

pid_list="$(IFS=,; echo "${valid_pids[*]}")"
if [[ "$action" == "cancel" ]]; then
  "$SCRIPT_DIR/psql_with_ssl_fallback.sh" -v ON_ERROR_STOP=1 -Atc \
    "select pid, pg_cancel_backend(pid) from unnest(array[${pid_list}]) as pid;"
else
  "$SCRIPT_DIR/psql_with_ssl_fallback.sh" -v ON_ERROR_STOP=1 -Atc \
    "select pid, pg_terminate_backend(pid) from unnest(array[${pid_list}]) as pid;"
fi
