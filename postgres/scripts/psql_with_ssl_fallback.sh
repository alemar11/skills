#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/pg_env.sh"

eval "$("$SCRIPT_DIR/resolve_db_url.sh")"

set +e
psql "$DB_URL" "$@"
status=$?
set -e

if [[ $status -eq 0 ]]; then
  exit 0
fi

if [[ "$DB_SSLMODE" == "disable" ]]; then
  SSL_URL="$(
    python3 - "$DB_URL" <<'PY'
import sys
import urllib.parse

url = sys.argv[1]
parsed = urllib.parse.urlparse(url)
query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
query["sslmode"] = ["require"]
new_query = urllib.parse.urlencode(query, doseq=True)
print(urllib.parse.urlunparse(parsed._replace(query=new_query)))
PY
  )"

  echo "Retrying with sslmode=require for profile '$DB_PROFILE'..." >&2

  set +e
  psql "$SSL_URL" "$@"
  retry_status=$?
  set -e

  if [[ $retry_status -eq 0 && "$DB_URL_SOURCE" == "toml" ]]; then
    if [[ "${DB_AUTO_UPDATE_SSLMODE:-}" == "1" ]]; then
      "$SCRIPT_DIR/update_sslmode.sh" "$DB_PROFILE" "require" || true
      echo "Updated postgres.toml: [database.$DB_PROFILE] sslmode = \"require\"" >&2
    else
      echo "sslmode=require succeeded. To persist for profile '$DB_PROFILE', run:" >&2
      echo "  $SCRIPT_DIR/update_sslmode.sh \"$DB_PROFILE\" require" >&2
      echo "(Set DB_AUTO_UPDATE_SSLMODE=1 to auto-update.)" >&2
    fi
    exit 0
  fi

  exit $retry_status
fi

exit $status
