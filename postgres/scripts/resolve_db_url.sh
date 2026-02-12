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
PROFILE="${DB_PROFILE:-}"
DEFAULT_PROFILE="local"

if [[ -x "$SCRIPT_DIR/check_toml_gitignored.sh" ]]; then
  "$SCRIPT_DIR/check_toml_gitignored.sh" "$PROJECT_ROOT" || true
fi

python3 - "$TOML_PATH" "$PROFILE" "$DEFAULT_PROFILE" "$PROJECT_ROOT" "$PWD" <<'PY'
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


toml_path = sys.argv[1]
profile_arg = sys.argv[2]
default_profile = sys.argv[3]
project_root = sys.argv[4]
cwd = sys.argv[5]

explicit_profile = profile_arg or None
if explicit_profile and not re.match(r"^[a-z0-9_]+$", explicit_profile):
    die(
        "Invalid DB_PROFILE. Use lowercase letters, digits, and underscores only "
        "(e.g. local, db_test_1)."
    )

env_url = os.environ.get("DB_URL")
if env_url:
    sslmode = normalize_sslmode(sslmode_from_url(env_url)) or "disable"
    shell_print("DB_URL", env_url)
    shell_print("DB_SSLMODE", sslmode)
    shell_print("DB_PROFILE", explicit_profile or default_profile)
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
if not re.match(r"^[a-z0-9_]+$", profile):
    die(
        "Invalid DB_PROFILE. Use lowercase letters, digits, and underscores only "
        "(e.g. local, db_test_1)."
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
