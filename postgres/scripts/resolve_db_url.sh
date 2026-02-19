#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEFAULT_PROFILE="local"
CACHE_VERSION="2"

check_unsupported_env() {
  local key="$1"
  local replacement="$2"
  if [[ -n "${!key+x}" ]]; then
    echo "Unsupported environment variable '$key'. Use '$replacement' instead." >&2
    exit 1
  fi
}

resolve_debug() {
  if [[ "${DB_DEBUG:-0}" == "1" ]]; then
    echo "[resolve_db_url] $*" >&2
  fi
}

resolve_cache_enabled() {
  case "${DB_RESOLVE_CACHE:-1}" in
    0|false|FALSE|False|off|OFF|Off|no|NO|No)
      return 1
      ;;
    *)
      return 0
      ;;
  esac
}

resolve_cache_dir() {
  local runtime_dir="${XDG_RUNTIME_DIR:-${TMPDIR:-/tmp}}"
  local uid="${UID:-$(id -u 2>/dev/null || echo 0)}"
  printf '%s/codex-postgres-resolve-%s' "$runtime_dir" "$uid"
}

resolve_file_mtime() {
  local path="$1"
  if [[ ! -f "$path" ]]; then
    echo "missing"
    return 0
  fi
  if stat -f %m "$path" >/dev/null 2>&1; then
    stat -f %m "$path"
    return 0
  fi
  if stat -c %Y "$path" >/dev/null 2>&1; then
    stat -c %Y "$path"
    return 0
  fi
  # Fallback: hash content if mtime is unavailable.
  if command -v shasum >/dev/null 2>&1; then
    shasum "$path" | awk '{print $1}'
    return 0
  fi
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$path" | awk '{print $1}'
    return 0
  fi
  echo "unknown"
}

resolve_signature() {
  local mode="$1"
  shift
  local raw
  raw="${CACHE_VERSION}|${mode}|$*"
  if command -v cksum >/dev/null 2>&1; then
    local checksum length _
    read -r checksum length _ <<<"$(printf '%s' "$raw" | cksum)"
    printf '%s-%s' "$checksum" "$length"
    return 0
  fi
  printf '%s' "$raw" | tr -cs '[:alnum:]_-' '_'
}

print_resolved() {
  printf 'DB_URL=%q\n' "$1"
  printf 'DB_SSLMODE=%q\n' "$2"
  printf 'DB_PROFILE=%q\n' "$3"
  printf 'DB_URL_SOURCE=%q\n' "$4"
  printf 'DB_TOML_PATH=%q\n' "$5"
}

resolve_cache_load() {
  local signature="$1"
  local cache_dir cache_file
  cache_dir="$(resolve_cache_dir)"
  cache_file="$cache_dir/${signature}.env"

  if [[ ! -r "$cache_file" ]]; then
    return 1
  fi

  local cached_signature=""
  local cached_db_url=""
  local cached_db_sslmode=""
  local cached_db_profile=""
  local cached_db_url_source=""
  local cached_db_toml_path=""

  # shellcheck disable=SC1090
  source "$cache_file" || return 1

  cached_signature="${CACHE_SIGNATURE:-}"
  cached_db_url="${CACHE_DB_URL:-}"
  cached_db_sslmode="${CACHE_DB_SSLMODE:-}"
  cached_db_profile="${CACHE_DB_PROFILE:-}"
  cached_db_url_source="${CACHE_DB_URL_SOURCE:-}"
  cached_db_toml_path="${CACHE_DB_TOML_PATH:-}"

  if [[ "$cached_signature" != "$signature" ]]; then
    return 1
  fi

  if [[ -z "$cached_db_url" || -z "$cached_db_sslmode" || -z "$cached_db_profile" || -z "$cached_db_url_source" ]]; then
    return 1
  fi

  resolve_debug "cache hit"
  touch "$cache_file" 2>/dev/null || true
  print_resolved "$cached_db_url" "$cached_db_sslmode" "$cached_db_profile" "$cached_db_url_source" "$cached_db_toml_path"
  return 0
}

resolve_cache_prune() {
  local cache_dir="$1"
  local max_entries="${DB_RESOLVE_CACHE_MAX_ENTRIES:-32}"
  if ! [[ "$max_entries" =~ ^[0-9]+$ ]] || [[ "$max_entries" -lt 1 ]]; then
    max_entries=32
  fi

  local entries=()
  local entry
  while IFS= read -r entry; do
    entries+=("$entry")
  done < <(ls -1t "$cache_dir"/*.env 2>/dev/null || true)

  local i
  for ((i=max_entries; i<${#entries[@]}; i++)); do
    rm -f "${entries[$i]}"
  done
}

resolve_cache_save() {
  local signature="$1"
  local db_url="$2"
  local db_sslmode="$3"
  local db_profile="$4"
  local db_url_source="$5"
  local db_toml_path="$6"

  local cache_dir cache_file tmp_file
  cache_dir="$(resolve_cache_dir)"
  mkdir -p "$cache_dir" 2>/dev/null || return 0
  cache_file="$cache_dir/${signature}.env"
  tmp_file="$(mktemp)" || return 0

  {
    printf 'CACHE_SIGNATURE=%q\n' "$signature"
    printf 'CACHE_DB_URL=%q\n' "$db_url"
    printf 'CACHE_DB_SSLMODE=%q\n' "$db_sslmode"
    printf 'CACHE_DB_PROFILE=%q\n' "$db_profile"
    printf 'CACHE_DB_URL_SOURCE=%q\n' "$db_url_source"
    printf 'CACHE_DB_TOML_PATH=%q\n' "$db_toml_path"
  } >"$tmp_file"

  if mv "$tmp_file" "$cache_file" 2>/dev/null; then
    resolve_cache_prune "$cache_dir"
    resolve_debug "cache save"
  else
    rm -f "$tmp_file"
  fi
}

resolve_gitignore_marker_file() {
  local runtime_dir="${XDG_RUNTIME_DIR:-${TMPDIR:-/tmp}}"
  local uid="${UID:-$(id -u 2>/dev/null || echo 0)}"
  printf '%s/codex-postgres-gitignore-%s.env' "$runtime_dir" "$uid"
}

resolve_gitignore_seen() {
  local project_root="$1"
  local marker_file marker_sig marker_project marker_toml
  marker_file="$(resolve_gitignore_marker_file)"
  marker_sig="$(resolve_signature "gitignore" "$project_root")"
  if [[ ! -r "$marker_file" ]]; then
    return 1
  fi
  # shellcheck disable=SC1090
  source "$marker_file" || return 1
  marker_project="${GITIGNORE_LAST_PROJECT:-}"
  marker_toml="${GITIGNORE_LAST_TOML_PATH:-}"
  [[ "$GITIGNORE_LAST_SIG" == "$marker_sig" ]] || return 1
  [[ "$marker_project" == "$project_root" ]] || return 1
  [[ "$marker_toml" == "$TOML_PATH" ]] || return 1
}

resolve_gitignore_mark_seen() {
  local project_root="$1"
  local marker_file tmp_file marker_sig
  marker_file="$(resolve_gitignore_marker_file)"
  tmp_file="$(mktemp)" || return 0
  marker_sig="$(resolve_signature "gitignore" "$project_root")"
  {
    printf 'GITIGNORE_LAST_SIG=%q\n' "$marker_sig"
    printf 'GITIGNORE_LAST_PROJECT=%q\n' "$project_root"
    printf 'GITIGNORE_LAST_TOML_PATH=%q\n' "$TOML_PATH"
  } >"$tmp_file"
  mv "$tmp_file" "$marker_file" 2>/dev/null || rm -f "$tmp_file"
}

maybe_check_toml_gitignored() {
  local project_root="$1"
  if [[ "${DB_GITIGNORE_CHECK:-1}" == "0" ]]; then
    return 0
  fi
  if [[ ! -x "$SCRIPT_DIR/check_toml_gitignored.sh" ]]; then
    return 0
  fi
  if resolve_gitignore_seen "$project_root"; then
    return 0
  fi
  "$SCRIPT_DIR/check_toml_gitignored.sh" "$project_root" || true
  resolve_gitignore_mark_seen "$project_root"
}

parse_resolved_output() {
  local output="$1"
  eval "$output"

  RES_DB_URL="${DB_URL:-}"
  RES_DB_SSLMODE="${DB_SSLMODE:-}"
  RES_DB_PROFILE="${DB_PROFILE:-}"
  RES_DB_URL_SOURCE="${DB_URL_SOURCE:-}"
  RES_DB_TOML_PATH="${DB_TOML_PATH:-}"

  if [[ -z "$RES_DB_URL" || -z "$RES_DB_SSLMODE" || -z "$RES_DB_PROFILE" || -z "$RES_DB_URL_SOURCE" ]]; then
    echo "resolve_db_url.sh failed to produce required output values." >&2
    exit 1
  fi
}

normalize_sslmode_from_env_url() {
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

  local lower
  lower="$(printf '%s' "$raw" | tr '[:upper:]' '[:lower:]')"
  case "$lower" in
    true|t|1|yes|y|on|enable|enabled|require|required|verify-ca|verify-full)
      echo "require"
      ;;
    false|f|0|no|n|off|disable|disabled)
      echo "disable"
      ;;
    *)
      echo "$raw"
      ;;
  esac
}

require_python3() {
  if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 is required to parse postgres.toml profiles. Install Python 3.11+ or set DB_URL for a one-off connection." >&2
    exit 1
  fi
}

check_unsupported_env "PROJECT_ROOT" "DB_PROJECT_ROOT"
check_unsupported_env "DATABASE_URL" "DB_URL"
check_unsupported_env "POSTGRES_URL" "DB_URL"
check_unsupported_env "POSTGRESQL_URL" "DB_URL"
check_unsupported_env "PGHOST" "DB_URL"
check_unsupported_env "PGPORT" "DB_URL"
check_unsupported_env "PGDATABASE" "DB_URL"
check_unsupported_env "PGUSER" "DB_URL"
check_unsupported_env "PGPASSWORD" "DB_URL"
check_unsupported_env "PGSSLMODE" "DB_URL"
check_unsupported_env "DB_HOST" "DB_URL"
check_unsupported_env "DB_PORT" "DB_URL"
check_unsupported_env "DB_NAME" "DB_URL"
check_unsupported_env "DB_DATABASE" "DB_URL"
check_unsupported_env "DB_USER" "DB_URL"
check_unsupported_env "DB_PASSWORD" "DB_URL"

PROFILE="${DB_PROFILE:-}"
if [[ -n "$PROFILE" && ! "$PROFILE" =~ ^[a-z0-9_-]+$ ]]; then
  echo "Invalid DB_PROFILE. Use lowercase letters, digits, underscores, and hyphens only (e.g. local, db-test-1)." >&2
  exit 1
fi

if [[ -n "${DB_URL:-}" ]]; then
  db_sslmode="$(normalize_sslmode_from_env_url "$DB_URL")"
  resolved_profile="${PROFILE:-$DEFAULT_PROFILE}"

  if resolve_cache_enabled; then
    cache_sig="$(resolve_signature "env" "$DB_URL" "$db_sslmode" "$resolved_profile")"
    if resolve_cache_load "$cache_sig"; then
      exit 0
    fi
    resolve_cache_save "$cache_sig" "$DB_URL" "$db_sslmode" "$resolved_profile" "env" ""
  fi

  print_resolved "$DB_URL" "$db_sslmode" "$resolved_profile" "env" ""
  exit 0
fi

ROOT_OVERRIDE="${DB_PROJECT_ROOT:-}"
PROJECT_ROOT="$ROOT_OVERRIDE"
if [[ -z "$PROJECT_ROOT" && -x "$(command -v git)" ]]; then
  PROJECT_ROOT="$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null || true)"
fi
if [[ -z "$PROJECT_ROOT" ]]; then
  PROJECT_ROOT="$PWD"
fi
if [[ -z "$ROOT_OVERRIDE" ]]; then
  case "$PROJECT_ROOT" in
    "$SKILL_ROOT"|"$SKILL_ROOT"/*)
      echo "Project root resolved to the postgres skill directory: $SKILL_ROOT" >&2
      echo "Run this from the postgres skill directory with DB_PROJECT_ROOT set (or run from your project root)." >&2
      exit 1
      ;;
  esac
fi

TOML_PATH="$PROJECT_ROOT/.skills/postgres/postgres.toml"
TOML_MTIME="$(resolve_file_mtime "$TOML_PATH")"

CACHE_SIG=""
if resolve_cache_enabled; then
  CACHE_SIG="$(resolve_signature "toml" "$PROFILE" "$ROOT_OVERRIDE" "$PROJECT_ROOT" "$PWD" "$TOML_PATH" "$TOML_MTIME")"
  if resolve_cache_load "$CACHE_SIG"; then
    exit 0
  fi
fi

maybe_check_toml_gitignored "$PROJECT_ROOT"

require_python3

resolved_output="$(python3 - "$TOML_PATH" "$PROFILE" "$DEFAULT_PROFILE" "$PROJECT_ROOT" "$PWD" <<'PY'
import os
import re
import shlex
import sys
import urllib.parse

try:
    import tomllib
except Exception:
    print(
        "python3>=3.11 is required to parse postgres.toml profiles (tomllib). "
        "Update python3 or set DB_URL for a one-off connection.",
        file=sys.stderr,
    )
    sys.exit(1)

LATEST_SCHEMA = 1


def shell_print(key: str, value: str) -> None:
    if value is None:
        value = ""
    print(f"{key}={shlex.quote(str(value))}")


def sslmode_from_url(url: str) -> str | None:
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception:
        return None
    query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    return query.get("sslmode", [None])[0]


def add_or_replace_sslmode(url: str, sslmode: str) -> str:
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    query["sslmode"] = [sslmode]
    new_query = urllib.parse.urlencode(query, doseq=True)
    return urllib.parse.urlunparse(parsed._replace(query=new_query))


def normalize_sslmode(value) -> str | None:
    # For URL query parsing (env DB_URL or [database.<profile>].url), preserve
    # explicit sslmode strings; only normalize common bool-ish values.
    if value is None:
        return None
    if isinstance(value, bool):
        return "require" if value else "disable"
    text = str(value).strip()
    if not text:
        return None
    lower = text.lower()
    if lower in {
        "true",
        "t",
        "1",
        "yes",
        "y",
        "on",
        "enable",
        "enabled",
    }:
        return "require"
    if lower in {"false", "f", "0", "no", "n", "off"}:
        return "disable"
    return text


def normalize_sslmode_from_toml(value) -> str | None:
    # Strict: sslmode in postgres.toml must be boolean only.
    if value is None:
        return None
    if isinstance(value, bool):
        return "require" if value else "disable"
    if isinstance(value, int) and value in (0, 1):
        return "require" if bool(value) else "disable"
    die(
        "Invalid sslmode type in postgres.toml. "
        "In schema v1, [database].sslmode and [database.<profile>].sslmode must be boolean (true/false). "
        "Run ./scripts/migrate_toml_schema.sh or fix the value manually."
    )
    return None


def die(message: str) -> None:
    print(message, file=sys.stderr)
    sys.exit(1)


def parse_schema_version(value) -> int:
    if value is None:
        return 0
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if text.isdigit():
        return int(text)
    die(f"Invalid schema_version in postgres.toml: {value!r}")
    return 0


toml_path = sys.argv[1]
profile_arg = sys.argv[2]
default_profile = sys.argv[3]
project_root = sys.argv[4]
cwd = sys.argv[5]

explicit_profile = profile_arg or None
if explicit_profile and not re.match(r"^[a-z0-9_-]+$", explicit_profile):
    die(
        "Invalid DB_PROFILE. Use lowercase letters, digits, underscores, and hyphens only "
        "(e.g. local, db-test-1)."
    )

if not os.path.exists(toml_path):
    die(
        f"Missing postgres.toml at {toml_path}. "
        "Create a [database.<profile>] entry first."
    )

with open(toml_path, "rb") as f:
    data = tomllib.load(f)

config = data.get("configuration")
if not isinstance(config, dict):
    die(
        "postgres.toml is missing [configuration].schema_version; "
        "run ./scripts/migrate_toml_schema.sh before using TOML profiles."
    )

current_schema = parse_schema_version(config.get("schema_version"))
if current_schema == 0:
    die(
        "postgres.toml is missing [configuration].schema_version; "
        "run ./scripts/migrate_toml_schema.sh before using TOML profiles."
    )
if current_schema < LATEST_SCHEMA:
    die(
        "postgres.toml schema_version is outdated "
        f"({current_schema} < {LATEST_SCHEMA}). "
        "Run ./scripts/migrate_toml_schema.sh first."
    )
if current_schema > LATEST_SCHEMA:
    die(
        "postgres.toml schema_version is newer than this skill supports "
        f"({current_schema} > {LATEST_SCHEMA})."
    )

db = data.get("database")
if not isinstance(db, dict):
    die("postgres.toml is missing a [database] table.")

defaults = {k: v for k, v in db.items() if not isinstance(v, dict)}
profiles = {k: v for k, v in db.items() if isinstance(v, dict)}


def infer_project(root: str, path: str) -> str:
    try:
        rel = os.path.relpath(path, root)
    except ValueError:
        return ""
    if rel == ".":
        return os.path.basename(root.rstrip(os.sep)) or "project"
    if rel.startswith(".."):
        return ""
    parts = [p for p in rel.split(os.sep) if p]
    if not parts:
        return ""
    markers = {"apps", "packages", "services", "modules", "projects"}
    is_monorepo = any(os.path.isdir(os.path.join(root, m)) for m in markers)
    if not is_monorepo:
        return os.path.basename(root.rstrip(os.sep)) or "project"
    if parts[0] in markers and len(parts) >= 2:
        return parts[1]
    return parts[0]


def profile_description(profile_data: dict) -> str:
    value = profile_data.get("description")
    if isinstance(value, str):
        text = value.strip()
        if text:
            return text
    return "(no description)"


def suggest_profile(profiles: dict, project_root: str, cwd: str) -> str:
    if not profiles:
        return default_profile

    project_slug = infer_project(project_root, cwd)
    if project_slug:
        matches = [
            name
            for name, data in profiles.items()
            if isinstance(data.get("project"), str)
            and data.get("project").strip() == project_slug
        ]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            return matches[0]

    global_profiles = [
        name
        for name, data in profiles.items()
        if not (isinstance(data.get("project"), str) and data.get("project").strip())
    ]
    if len(global_profiles) == 1:
        return global_profiles[0]
    if default_profile in profiles:
        return default_profile
    return next(iter(profiles.keys()))


def render_profiles_summary(profiles: dict, suggested: str) -> str:
    lines = ["Available profiles (name: description):"]
    for name, cfg in profiles.items():
        marker = " (default)" if name == suggested else ""
        lines.append(f"- {name}: {profile_description(cfg)}{marker}")
    return "\n".join(lines)


def ask_profile_choice(profiles: dict, suggested: str) -> str:
    summary = render_profiles_summary(profiles, suggested)
    if not sys.stdin.isatty():
        die(
            "Multiple profiles found and DB_PROFILE is not set.\n"
            f"{summary}\n"
            f"Suggested default from current context: {suggested}\n"
            "Set DB_PROFILE to the profile you want."
        )

    print(
        "Multiple profiles found in postgres.toml. Select one before running queries.",
        file=sys.stderr,
    )
    print(summary, file=sys.stderr)
    print(
        f"Suggested default from current context: {suggested}",
        file=sys.stderr,
    )

    while True:
        sys.stderr.write(f"Profile to use [{suggested}]: ")
        sys.stderr.flush()
        raw = sys.stdin.readline()
        if raw == "":
            return suggested
        choice = raw.strip() or suggested
        if choice in profiles:
            return choice
        print(
            "Invalid profile name. Choose one of: "
            + ", ".join(profiles.keys()),
            file=sys.stderr,
        )


def pick_profile(
    profile_hint: str | None, profiles: dict, project_root: str, cwd: str
) -> str:
    if profile_hint:
        return profile_hint
    if not profiles:
        die("postgres.toml has no [database.<profile>] entries.")
    if len(profiles) == 1:
        return next(iter(profiles.keys()))
    suggested = suggest_profile(profiles, project_root, cwd)
    return ask_profile_choice(profiles, suggested)


profile = pick_profile(explicit_profile, profiles, project_root, cwd)
if not re.match(r"^[a-z0-9_-]+$", profile):
    die(
        "Invalid DB_PROFILE. Use lowercase letters, digits, underscores, and hyphens only "
        "(e.g. local, db-test-1)."
    )

profile_data = db.get(profile)
if not isinstance(profile_data, dict):
    die(
        f"Profile '{profile}' not found in postgres.toml. "
        "Add a [database.<profile>] section first."
    )

cfg = {**defaults, **profile_data}

url = cfg.get("url")
sslmode = normalize_sslmode_from_toml(cfg.get("sslmode"))

if url:
    url = str(url)
    if sslmode is None:
        sslmode = normalize_sslmode(sslmode_from_url(url))
    if sslmode is None:
        sslmode = "disable"
    url = add_or_replace_sslmode(url, sslmode)
else:
    required = ["host", "port", "database", "user", "password"]
    missing = [key for key in required if not cfg.get(key)]
    if missing:
        die(
            "Missing required fields in postgres.toml for profile "
            f"'{profile}': {', '.join(missing)}"
        )

    sslmode = sslmode or "disable"
    user = urllib.parse.quote(str(cfg["user"]))
    password = urllib.parse.quote(str(cfg["password"]))
    host = str(cfg["host"])
    port = str(cfg["port"])
    database = urllib.parse.quote(str(cfg["database"]))

    netloc = f"{user}:{password}@{host}:{port}"
    path = f"/{database}"
    query = urllib.parse.urlencode({"sslmode": sslmode})
    url = urllib.parse.urlunparse(("postgresql", netloc, path, "", query, ""))

shell_print("DB_URL", url)
shell_print("DB_SSLMODE", sslmode)
shell_print("DB_PROFILE", profile)
shell_print("DB_URL_SOURCE", "toml")
shell_print("DB_TOML_PATH", toml_path)
PY
)"

parse_resolved_output "$resolved_output"

if [[ -n "$CACHE_SIG" ]]; then
  resolve_cache_save "$CACHE_SIG" "$RES_DB_URL" "$RES_DB_SSLMODE" "$RES_DB_PROFILE" "$RES_DB_URL_SOURCE" "$RES_DB_TOML_PATH"
fi

print_resolved "$RES_DB_URL" "$RES_DB_SSLMODE" "$RES_DB_PROFILE" "$RES_DB_URL_SOURCE" "$RES_DB_TOML_PATH"
