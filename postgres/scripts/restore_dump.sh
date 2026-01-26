#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/pg_env.sh"
eval "$("$SCRIPT_DIR/resolve_db_url.sh")"

input="${1:-}"
if [[ -z "$input" ]]; then
  echo "Usage: restore_dump.sh <dump_file>" >&2
  exit 1
fi
if [[ ! -f "$input" ]]; then
  echo "File not found: $input" >&2
  exit 1
fi

set_sslmode_in_url() {
  python3 - "$1" "$2" <<'PY'
import sys
import urllib.parse

url = sys.argv[1]
sslmode = sys.argv[2]
parsed = urllib.parse.urlparse(url)
query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
query["sslmode"] = [sslmode]
new_query = urllib.parse.urlencode(query, doseq=True)
print(urllib.parse.urlunparse(parsed._replace(query=new_query)))
PY
}

run_restore() {
  local url="$1"
  if [[ "$input" == *.sql ]]; then
    psql "$url" -v ON_ERROR_STOP=1 -f "$input"
  else
    pg_restore --no-owner --no-acl --dbname "$url" "$input"
  fi
}

set +e
run_restore "$DB_URL"
status=$?
set -e

if [[ $status -ne 0 && "$DB_SSLMODE" == "disable" ]]; then
  retry_url="$(set_sslmode_in_url "$DB_URL" "require")"
  echo "Retrying restore with sslmode=require for profile '${DB_PROFILE:-local}'..." >&2
  set +e
  run_restore "$retry_url"
  retry_status=$?
  set -e

  if [[ $retry_status -eq 0 && "$DB_URL_SOURCE" == "toml" ]]; then
    if [[ "${DB_AUTO_UPDATE_SSLMODE:-}" == "1" ]]; then
      "$SCRIPT_DIR/update_sslmode.sh" "$DB_PROFILE" "true" || true
      echo "Updated postgres.toml: [database.$DB_PROFILE] sslmode = true" >&2
    else
      echo "sslmode=require succeeded. To persist for profile '$DB_PROFILE', run:" >&2
      echo "  $SCRIPT_DIR/update_sslmode.sh \"$DB_PROFILE\" true" >&2
      echo "(Set DB_AUTO_UPDATE_SSLMODE=1 to auto-update.)" >&2
    fi
  fi

  status=$retry_status
fi

if [[ $status -ne 0 ]]; then
  exit $status
fi

echo "Restore complete."
