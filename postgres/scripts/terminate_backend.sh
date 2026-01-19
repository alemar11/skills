#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID="${1:-}"

if [[ -z "$PID" || ! "$PID" =~ ^[0-9]+$ ]]; then
  echo "Usage: terminate_backend.sh <pid>" >&2
  exit 1
fi

confirm="${DB_CONFIRM:-}"
if [[ "$confirm" != "YES" ]]; then
  if [[ -t 0 ]]; then
    read -r -p "Terminate backend PID ${PID}? Type YES to confirm: " confirm
  fi
fi

if [[ "$confirm" != "YES" ]]; then
  echo "Aborted. Set DB_CONFIRM=YES to skip prompt." >&2
  exit 1
fi

"$SCRIPT_DIR/psql_with_ssl_fallback.sh" \
  -v ON_ERROR_STOP=1 \
  -Atc "select pg_terminate_backend(${PID});"
