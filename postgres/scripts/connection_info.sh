#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"$SCRIPT_DIR/psql_with_ssl_fallback.sh" \
  -v ON_ERROR_STOP=1 \
  -Atc "
select 'database=' || current_database()
union all select 'user=' || current_user
union all select 'host=' || coalesce(inet_server_addr()::text, 'local')
union all select 'port=' || inet_server_port()
union all select 'server_version=' || current_setting('server_version')
union all select 'search_path=' || current_setting('search_path')
union all select 'default_transaction_read_only=' || current_setting('default_transaction_read_only')
union all select 'timezone=' || current_setting('TimeZone')
union all select 'application_name=' || current_setting('application_name');"
