#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"$SCRIPT_DIR/psql_with_ssl_fallback.sh" -v ON_ERROR_STOP=1 -f "$SCRIPT_DIR/roles_overview.sql"
