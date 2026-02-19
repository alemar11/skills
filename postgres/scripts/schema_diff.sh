#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/pg_env.sh"

usage() {
  cat <<'EOF'
Usage:
  schema_diff.sh <profile_a> <profile_b>

Or via env:
  DB_PROFILE_A=local DB_PROFILE_B=staging ./scripts/schema_diff.sh

Optional overrides:
  DB_URL_A / DB_URL_B (full connection URLs)
EOF
}

require_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Missing required command: $cmd" >&2
    exit 1
  fi
}

get_sslmode_from_url() {
  python3 - "$1" <<'PY'
import sys
import urllib.parse

url = sys.argv[1]
parsed = urllib.parse.urlparse(url)
query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
raw = query.get("sslmode", ["disable"])[0] or "disable"
lower = str(raw).strip().lower()
if lower in {"true", "t", "1", "yes", "y", "on", "enable", "enabled", "require", "required", "verify-ca", "verify-full"}:
    print("require")
elif lower in {"false", "f", "0", "no", "n", "off", "disable", "disabled"}:
    print("disable")
else:
    print(raw)
PY
}

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

load_profile() {
  local label="$1"
  local profile="$2"
  local out
  out="$(DB_PROFILE="$profile" "$SCRIPT_DIR/resolve_db_url.sh")"
  eval "$out"
  printf -v "DB_URL_${label}" '%s' "$DB_URL"
  printf -v "DB_SSLMODE_${label}" '%s' "$DB_SSLMODE"
  printf -v "DB_PROFILE_${label}" '%s' "$DB_PROFILE"
  printf -v "DB_URL_SOURCE_${label}" '%s' "$DB_URL_SOURCE"
}

set_url_override() {
  local label="$1"
  local url="$2"
  local profile="${3:-custom}"
  local sslmode
  sslmode="$(get_sslmode_from_url "$url")"
  printf -v "DB_URL_${label}" '%s' "$url"
  printf -v "DB_SSLMODE_${label}" '%s' "$sslmode"
  printf -v "DB_PROFILE_${label}" '%s' "$profile"
  printf -v "DB_URL_SOURCE_${label}" '%s' "env"
}

dump_schema() {
  local label="$1"
  local out_file="$2"
  local url_var="DB_URL_${label}"
  local ssl_var="DB_SSLMODE_${label}"
  local source_var="DB_URL_SOURCE_${label}"
  local profile_var="DB_PROFILE_${label}"
  local url="${!url_var}"
  local sslmode="${!ssl_var}"
  local source="${!source_var}"
  local profile="${!profile_var}"

  if pg_dump --schema-only --no-owner --no-acl --no-comments "$url" >"$out_file"; then
    return 0
  fi

  if [[ "$sslmode" == "disable" ]]; then
    local retry_url
    retry_url="$(set_sslmode_in_url "$url" "require")"
    if pg_dump --schema-only --no-owner --no-acl --no-comments "$retry_url" >"$out_file"; then
      if [[ "$source" == "toml" ]]; then
        if [[ "${DB_AUTO_UPDATE_SSLMODE:-}" == "1" ]]; then
          "$SCRIPT_DIR/update_sslmode.sh" "$profile" "true" || true
          echo "Updated postgres.toml: [database.$profile] sslmode = true" >&2
        else
          echo "sslmode=require succeeded for profile '$profile'. To persist, run:" >&2
          echo "  $SCRIPT_DIR/update_sslmode.sh \"$profile\" true" >&2
          echo "(Set DB_AUTO_UPDATE_SSLMODE=1 to auto-update.)" >&2
        fi
      fi
      return 0
    fi
  fi

  echo "Failed to dump schema for profile '$profile'." >&2
  return 1
}

require_cmd python3
require_cmd pg_dump
require_cmd diff

PROFILE_A="${1:-${DB_PROFILE_A:-}}"
PROFILE_B="${2:-${DB_PROFILE_B:-}}"

if [[ -z "${DB_URL_A:-}" && -z "$PROFILE_A" ]]; then
  usage
  exit 1
fi

if [[ -z "${DB_URL_B:-}" && -z "$PROFILE_B" ]]; then
  usage
  exit 1
fi

if [[ -n "${DB_URL_A:-}" ]]; then
  set_url_override "A" "$DB_URL_A" "${PROFILE_A:-custom_a}"
else
  load_profile "A" "$PROFILE_A"
fi

if [[ -n "${DB_URL_B:-}" ]]; then
  set_url_override "B" "$DB_URL_B" "${PROFILE_B:-custom_b}"
else
  load_profile "B" "$PROFILE_B"
fi

tmp_a="$(mktemp)"
tmp_b="$(mktemp)"
cleanup() {
  rm -f "$tmp_a" "$tmp_b"
}
trap cleanup EXIT

dump_schema "A" "$tmp_a" &
pid_a=$!
dump_schema "B" "$tmp_b" &
pid_b=$!

set +e
wait "$pid_a"
status_a=$?
wait "$pid_b"
status_b=$?
set -e

if [[ $status_a -ne 0 || $status_b -ne 0 ]]; then
  exit 1
fi

if diff -u "$tmp_a" "$tmp_b"; then
  echo "No structural differences."
  exit 0
fi
