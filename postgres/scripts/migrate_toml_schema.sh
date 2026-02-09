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
      echo "Run this from the postgres skill directory with DB_PROJECT_ROOT/PROJECT_ROOT set (or run from your project root)." >&2
      exit 1
      ;;
  esac
fi

TOML_PATH="$PROJECT_ROOT/.skills/postgres/postgres.toml"

if [[ ! -f "$TOML_PATH" ]]; then
  echo "postgres.toml not found at $TOML_PATH" >&2
  exit 1
fi

if [[ -x "$SCRIPT_DIR/check_toml_gitignored.sh" ]]; then
  "$SCRIPT_DIR/check_toml_gitignored.sh" "$PROJECT_ROOT" || true
fi

python3 - "$TOML_PATH" <<'PY'
import os
import sys
import tomllib
import shutil
from typing import Any

LATEST_SCHEMA = 1


def die(message: str) -> None:
    print(message, file=sys.stderr)
    sys.exit(1)


def parse_schema_version(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if text.isdigit():
        return int(text)
    die(f"Invalid schema_version: {value!r}")
    return 0


def sslmode_to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        if value in (0, 1):
            return bool(value)
        die(f"Invalid sslmode integer: {value!r}")
    text = str(value).strip()
    if not text:
        return False
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
        return True
    if lower in {"false", "f", "0", "no", "n", "off", "disable", "disabled"}:
        return False
    die(f"Unrecognized sslmode value: {value!r}")
    return False


def normalize_pg_bin_path(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    text = text.rstrip("/")
    if os.path.basename(text) == "psql":
        return os.path.dirname(text)
    return text


def detect_pg_bin_path() -> str:
    psql_path = shutil.which("psql")
    if not psql_path:
        return ""
    return os.path.dirname(psql_path)


def require_pg_bin_path(config: dict) -> None:
    value = normalize_pg_bin_path(config.get("pg_bin_path"))
    if not value:
        value = detect_pg_bin_path()
    if not value:
        die(
            "pg_bin_path is required but could not be determined. "
            "Install psql or set [configuration].pg_bin_path, then re-run."
        )
    if not os.path.isdir(value):
        die(
            "pg_bin_path must point to a directory that exists. "
            f"Got: {value}"
        )
    psql_path = os.path.join(value, "psql")
    if not os.path.isfile(psql_path):
        die(
            "pg_bin_path must contain a psql binary. "
            f"Expected: {psql_path}"
        )
    config["pg_bin_path"] = value


def migrate_0_to_1(data: dict) -> dict:
    config = data.setdefault("configuration", {})
    config["schema_version"] = 1
    require_pg_bin_path(config)

    db = data.get("database")
    if isinstance(db, dict):
        for key, value in list(db.items()):
            if isinstance(value, dict):
                if "sslmode" in value:
                    value["sslmode"] = sslmode_to_bool(value["sslmode"])
                continue
            if key == "sslmode":
                db[key] = sslmode_to_bool(value)
        if "sslmode" not in db:
            db["sslmode"] = False
    return data


MIGRATIONS = {
    0: migrate_0_to_1,
}


def format_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


def render_table(name: str, data: dict) -> list[str]:
    lines: list[str] = [f"[{name}]"]
    keys = list(data.keys())
    if name == "configuration" and "schema_version" in data:
        keys = ["schema_version"] + [k for k in keys if k != "schema_version"]
    for key in keys:
        lines.append(f"{key} = {format_value(data[key])}")
    return lines


def render_toml(data: dict) -> str:
    lines: list[str] = []

    config = data.get("configuration")
    if isinstance(config, dict):
        lines.extend(render_table("configuration", config))

    db = data.get("database")
    if isinstance(db, dict):
        if lines:
            lines.append("")
        defaults = [(k, v) for k, v in db.items() if not isinstance(v, dict)]
        profiles = [(k, v) for k, v in db.items() if isinstance(v, dict)]
        lines.append("[database]")
        for key, value in defaults:
            lines.append(f"{key} = {format_value(value)}")
        for profile, cfg in profiles:
            lines.append("")
            lines.append(f"[database.{profile}]")
            for key, value in cfg.items():
                lines.append(f"{key} = {format_value(value)}")

    for key, value in data.items():
        if key in {"configuration", "database"}:
            continue
        if isinstance(value, dict):
            if lines:
                lines.append("")
            lines.extend(render_table(key, value))
        else:
            if lines:
                lines.append("")
            lines.append(f"{key} = {format_value(value)}")

    return "\n".join(lines).rstrip() + "\n"


toml_path = sys.argv[1]
with open(toml_path, "rb") as fh:
    data = tomllib.load(fh)

config = data.get("configuration", {})
if not isinstance(config, dict):
    die("postgres.toml [configuration] must be a table if present.")
current = parse_schema_version(config.get("schema_version"))

if current > LATEST_SCHEMA:
    die(f"postgres.toml schema_version {current} is newer than supported {LATEST_SCHEMA}.")

existing_pg_bin = normalize_pg_bin_path(config.get("pg_bin_path"))
if current == LATEST_SCHEMA:
    require_pg_bin_path(data.setdefault("configuration", {}))
    if normalize_pg_bin_path(data["configuration"].get("pg_bin_path")) == existing_pg_bin:
        print(f"postgres.toml already at schema_version {LATEST_SCHEMA}.")
        sys.exit(0)
    with open(toml_path, "w", encoding="utf-8") as fh:
        fh.write(render_toml(data))
    print(f"Updated postgres.toml pg_bin_path for schema_version {LATEST_SCHEMA}.")
    sys.exit(0)

version = current
while version < LATEST_SCHEMA:
    migrate = MIGRATIONS.get(version)
    if not migrate:
        die(f"Missing migration for schema_version {version} -> {version + 1}.")
    data = migrate(data)
    version += 1

data.setdefault("configuration", {})["schema_version"] = LATEST_SCHEMA
require_pg_bin_path(data.setdefault("configuration", {}))

with open(toml_path, "w", encoding="utf-8") as fh:
    fh.write(render_toml(data))

print(f"Migrated postgres.toml to schema_version {LATEST_SCHEMA}.")
PY
