#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

args=(-v ON_ERROR_STOP=1)
if [[ -n "${DB_VIEW_DEF_TRUNC:-}" ]]; then
  args+=(-v "view_def_trunc=${DB_VIEW_DEF_TRUNC}")
fi
if [[ -n "${DB_FUNC_DEF_TRUNC:-}" ]]; then
  args+=(-v "func_def_trunc=${DB_FUNC_DEF_TRUNC}")
fi

"$SCRIPT_DIR/psql_with_ssl_fallback.sh" "${args[@]}" -f "$SCRIPT_DIR/schema_introspect.sql"
