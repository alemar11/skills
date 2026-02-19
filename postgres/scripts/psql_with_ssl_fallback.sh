#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/pg_env.sh"

normalize_sslmode_from_url() {
  local url="$1"
  local query="${url#*\?}"
  local raw=""
  if [[ "$query" != "$url" ]]; then
    query="${query%%#*}"
    local pair
    IFS='&' read -r -a pairs <<< "$query"
    for pair in "${pairs[@]}"; do
      case "$pair" in
        sslmode=*)
          raw="${pair#sslmode=}"
          break
          ;;
      esac
    done
  fi
  if [[ -z "$raw" ]]; then
    echo "disable"
    return 0
  fi
  case "${raw,,}" in
    true|t|1|yes|y|on|enable|enabled|require|required|verify-ca|verify-full) echo "require" ;;
    false|f|0|no|n|off|disable|disabled) echo "disable" ;;
    *) echo "$raw" ;;
  esac
}

resolve_runtime_context() {
  if [[ -n "${DB_URL:-}" ]]; then
    DB_SSLMODE="${DB_SSLMODE:-$(normalize_sslmode_from_url "$DB_URL")}"
    DB_PROFILE="${DB_PROFILE:-local}"
    DB_URL_SOURCE="${DB_URL_SOURCE:-env}"
    DB_TOML_PATH="${DB_TOML_PATH:-}"
    export DB_SSLMODE DB_PROFILE DB_URL_SOURCE DB_TOML_PATH
    return 0
  fi
  local resolved
  if ! resolved="$("$SCRIPT_DIR/resolve_db_url.sh")"; then
    return 1
  fi
  eval "$resolved"
}

ssl_retry_enabled() {
  case "${DB_SSL_RETRY:-1}" in
    0|false|FALSE|False|off|OFF|Off|no|NO|No) return 1 ;;
    *) return 0 ;;
  esac
}

if ! resolve_runtime_context; then
  exit 1
fi

should_retry_with_ssl() {
  local err_file="$1"
  [[ -s "$err_file" ]] || return 1
  grep -Eiq \
    'SSL off|requires SSL|requires encryption|server requires|sslmode|TLS|certificate|no pg_hba\.conf entry.*SSL off' \
    "$err_file"
}

run_psql_with_stderr_capture() {
  local err_file="$1"
  shift
  set +e
  psql "$@" 2>"$err_file"
  local cmd_status=$?
  set -e
  if [[ -s "$err_file" ]]; then
    cat "$err_file" >&2
  fi
  return $cmd_status
}

first_err_file="$(mktemp)"
trap 'rm -f "$first_err_file" "${retry_err_file:-}"' EXIT

if [[ "${DB_SSLMODE:-}" != "disable" ]] || ! ssl_retry_enabled; then
  set +e
  psql "$DB_URL" "$@"
  status=$?
  set -e
  exit $status
fi

set +e
run_psql_with_stderr_capture "$first_err_file" "$DB_URL" "$@"
status=$?
set -e

if [[ $status -eq 0 ]]; then
  exit 0
fi

if [[ "${DB_SSLMODE:-}" == "disable" ]] && should_retry_with_ssl "$first_err_file"; then
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

  retry_err_file="$(mktemp)"
  set +e
  run_psql_with_stderr_capture "$retry_err_file" "$SSL_URL" "$@"
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
    exit 0
  fi

  exit $retry_status
fi

exit $status
