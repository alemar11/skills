#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ROOT_OVERRIDE="${DB_PROJECT_ROOT:-${PROJECT_ROOT:-}}"
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
      echo "Run this from your project root or set DB_PROJECT_ROOT/PROJECT_ROOT." >&2
      exit 1
      ;;
  esac
fi

TOML_PATH="$PROJECT_ROOT/.skills/postgres/postgres.toml"
PROFILE="${DB_PROFILE:-local}"

python3 - "$TOML_PATH" "$PROFILE" <<'PY'
import os
import re
import shlex
import sys
import tomllib
import urllib.parse


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
        "require",
        "required",
        "verify-ca",
        "verify-full",
    }:
        return "require"
    if lower in {"false", "f", "0", "no", "n", "off", "disable", "disabled"}:
        return "disable"
    return text


def die(message: str) -> None:
    print(message, file=sys.stderr)
    sys.exit(1)


toml_path = sys.argv[1]
profile = sys.argv[2]

if not re.match(r"^[a-z0-9_]+$", profile):
    die(
        "Invalid DB_PROFILE. Use lowercase letters, digits, and underscores only "
        "(e.g. local, db_test_1)."
    )

env_url = os.environ.get("DB_URL")
if env_url:
    sslmode = normalize_sslmode(sslmode_from_url(env_url)) or "disable"
    shell_print("DB_URL", env_url)
    shell_print("DB_SSLMODE", sslmode)
    shell_print("DB_PROFILE", profile)
    shell_print("DB_URL_SOURCE", "env")
    shell_print("DB_TOML_PATH", toml_path)
    sys.exit(0)

if not os.path.exists(toml_path):
    die(
        f"Missing postgres.toml at {toml_path}. "
        "Create a [database.<profile>] entry first."
    )

with open(toml_path, "rb") as f:
    data = tomllib.load(f)

db = data.get("database")
if not isinstance(db, dict):
    die("postgres.toml is missing a [database] table.")

defaults = {k: v for k, v in db.items() if not isinstance(v, dict)}
profile_data = db.get(profile)
if not isinstance(profile_data, dict):
    die(
        f"Profile '{profile}' not found in postgres.toml. "
        "Add a [database.<profile>] section first."
    )

cfg = {**defaults, **profile_data}

url = cfg.get("url")
sslmode = normalize_sslmode(cfg.get("sslmode"))

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
