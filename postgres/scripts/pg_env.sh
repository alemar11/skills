#!/usr/bin/env bash

if [[ -z "${PGAPPNAME:-}" ]]; then
  export PGAPPNAME="${DB_APPLICATION_NAME:-codex-postgres-skill}"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

pg_env_add_path() {
  local dir="$1"
  if [[ -n "$dir" && -d "$dir" ]]; then
    case ":$PATH:" in
      *":$dir:"*) ;;
      *) export PATH="$dir:$PATH" ;;
    esac
  fi
}

pg_env_normalize_bin_dir() {
  local path="$1"
  if [[ -z "$path" ]]; then
    return 0
  fi
  local trimmed="${path%/}"
  if [[ -f "$trimmed" || "${trimmed##*/}" == "psql" ]]; then
    dirname "$trimmed"
  else
    echo "$trimmed"
  fi
}

pg_env_resolve_project_root() {
  local root_override="${DB_PROJECT_ROOT:-${PROJECT_ROOT:-}}"
  local root="$root_override"
  if [[ -z "$root" && -x "$(command -v git)" ]]; then
    root="$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null || true)"
  fi
  if [[ -z "$root" ]]; then
    root="$PWD"
  fi
  if [[ -z "$root_override" ]]; then
    case "$root" in
      "$SKILL_ROOT"|"$SKILL_ROOT"/*)
        root=""
        ;;
    esac
  fi
  echo "$root"
}

pg_env_read_pg_bin_path() {
  local toml_path="$1"
  python3 - "$toml_path" <<'PY' 2>/dev/null || true
import sys
try:
    import tomllib
except Exception:
    sys.exit(0)

path = sys.argv[1]
try:
    with open(path, "rb") as fh:
        data = tomllib.load(fh)
except Exception:
    sys.exit(0)

conf = data.get("configuration", {})
val = conf.get("pg_bin_path", "")
if isinstance(val, str):
    print(val)
PY
}

pg_env_check_schema_version() {
  local toml_path="$1"
  if [[ -z "$toml_path" || ! -f "$toml_path" ]]; then
    return 0
  fi
  python3 - "$toml_path" <<'PY' 2>/dev/null || true
import sys
try:
    import tomllib
except Exception:
    sys.exit(0)

path = sys.argv[1]
try:
    with open(path, "rb") as fh:
        data = tomllib.load(fh)
except Exception:
    sys.exit(0)

conf = data.get("configuration")
if not isinstance(conf, dict) or conf.get("schema_version") in (None, ""):
    print(
        "postgres.toml is missing [configuration].schema_version; "
        "run ./scripts/migrate_toml_schema.sh to update.",
        file=sys.stderr,
    )
PY
}

pg_env_warn_if_toml_not_ignored() {
  local project_root="$1"
  local toml_rel_path=".skills/postgres/postgres.toml"

  if [[ -z "$project_root" ]]; then
    return 0
  fi
  if ! command -v git >/dev/null 2>&1; then
    return 0
  fi
  if ! git -C "$project_root" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    return 0
  fi

  if git -C "$project_root" check-ignore -q "$toml_rel_path" 2>/dev/null; then
    return 0
  fi

  echo "Warning: $toml_rel_path is not ignored by git. Add it to .gitignore to avoid committing credentials." >&2
}

pg_env_write_pg_bin_path() {
  local toml_path="$1"
  local new_dir="$2"
  if [[ -z "$toml_path" || -z "$new_dir" || ! -f "$toml_path" ]]; then
    return 1
  fi
  local tmp_file
  tmp_file="$(mktemp)" || return 1
  if ! awk -v new="$new_dir" '
    BEGIN { in_config=0; found=0; seen_config=0 }
    /^[[:space:]]*\[configuration\][[:space:]]*$/ {
      seen_config=1
      in_config=1
      print
      next
    }
    /^[[:space:]]*\[[^]]+\][[:space:]]*$/ {
      if (in_config && !found) {
        print "pg_bin_path = \"" new "\""
        print ""
        found=1
      }
      in_config=0
      print
      next
    }
    {
      if (in_config && $0 ~ /^[[:space:]]*pg_bin_path[[:space:]]*=/) {
        print "pg_bin_path = \"" new "\""
        found=1
        next
      }
      print
    }
    END {
      if (in_config && !found) {
        print "pg_bin_path = \"" new "\""
        found=1
      }
      if (!seen_config) {
        print ""
        print "[configuration]"
        print "pg_bin_path = \"" new "\""
        print ""
      }
    }
  ' "$toml_path" > "$tmp_file"; then
    rm -f "$tmp_file"
    return 1
  fi
  mv "$tmp_file" "$toml_path"
  echo "Updated postgres.toml: [configuration] pg_bin_path = \"$new_dir\"" >&2
}

pg_env_confirm_update() {
  local message="$1"
  if [[ -t 0 ]]; then
    local reply
    read -r -p "$message [y/N] " reply
    case "$reply" in
      [yY]|[yY][eE][sS]) return 0 ;;
      *) return 1 ;;
    esac
  fi
  echo "$message (no TTY; skipping update)" >&2
  return 1
}

pg_env_prompt_install() {
  local formula="$1"
  if [[ -z "$formula" ]]; then
    return 1
  fi
  if [[ -t 0 ]]; then
    local reply
    read -r -p "psql not found. Install ${formula} with Homebrew? [y/N] " reply
    case "$reply" in
      [yY]|[yY][eE][sS]) return 0 ;;
      *) return 1 ;;
    esac
  fi
  echo "psql not found. Install with: brew install ${formula}" >&2
  return 1
}

pg_env_project_root="$(pg_env_resolve_project_root)"
pg_env_toml_path=""
if [[ -n "$pg_env_project_root" ]]; then
  pg_env_toml_path="$pg_env_project_root/.skills/postgres/postgres.toml"
fi

pg_env_config_bin=""
if [[ -n "$pg_env_toml_path" && -f "$pg_env_toml_path" ]]; then
  pg_env_check_schema_version "$pg_env_toml_path"
  pg_env_warn_if_toml_not_ignored "$pg_env_project_root"
  pg_env_config_bin="$(pg_env_read_pg_bin_path "$pg_env_toml_path")"
fi

if [[ -n "$pg_env_config_bin" ]]; then
  pg_env_config_bin_dir="$(pg_env_normalize_bin_dir "$pg_env_config_bin")"
  pg_env_add_path "$pg_env_config_bin_dir"
fi

pg_env_psql_path=""
if command -v psql >/dev/null 2>&1; then
  pg_env_psql_path="$(command -v psql)"
fi

if [[ -z "$pg_env_psql_path" ]]; then
  case "$(uname -s 2>/dev/null || echo unknown)" in
    Darwin)
      if command -v brew >/dev/null 2>&1; then
        pg_env_formula="$(brew list --versions 2>/dev/null | awk '/^postgresql(@[0-9]+)? / {print $1}' | sort -V | tail -n 1)"
        if [[ -z "$pg_env_formula" ]]; then
          pg_env_formula="$(brew search postgresql@ 2>/dev/null | awk '/^postgresql@/ {print $1}' | sort -V | tail -n 1)"
          if [[ -z "$pg_env_formula" ]]; then
            pg_env_formula="postgresql"
          fi
          if pg_env_prompt_install "$pg_env_formula"; then
            brew install "$pg_env_formula" || true
          fi
        fi
        if [[ -n "$pg_env_formula" ]]; then
          pg_env_prefix="$(brew --prefix "$pg_env_formula" 2>/dev/null || true)"
          if [[ -n "$pg_env_prefix" && -d "$pg_env_prefix/bin" ]]; then
            pg_env_add_path "$pg_env_prefix/bin"
          fi
        fi
      fi
      ;;
    Linux)
      if [[ -d /usr/lib/postgresql ]]; then
        pg_env_candidate="$(ls /usr/lib/postgresql 2>/dev/null | sort -V | tail -n 1)"
        if [[ -n "$pg_env_candidate" && -d "/usr/lib/postgresql/$pg_env_candidate/bin" ]]; then
          pg_env_add_path "/usr/lib/postgresql/$pg_env_candidate/bin"
        fi
      fi
      ;;
    MINGW*|MSYS*|CYGWIN*)
      if [[ -d "/c/Program Files/PostgreSQL" ]]; then
        pg_env_win_version="$(ls "/c/Program Files/PostgreSQL" 2>/dev/null | sort -V | tail -n 1)"
        if [[ -n "$pg_env_win_version" && -d "/c/Program Files/PostgreSQL/$pg_env_win_version/bin" ]]; then
          pg_env_add_path "/c/Program Files/PostgreSQL/$pg_env_win_version/bin"
        fi
      fi
      ;;
  esac
  if command -v psql >/dev/null 2>&1; then
    pg_env_psql_path="$(command -v psql)"
  fi
fi

if [[ -n "$pg_env_psql_path" ]]; then
  pg_env_found_bin="$(dirname "$pg_env_psql_path")"
  if [[ -n "$pg_env_toml_path" && -f "$pg_env_toml_path" ]]; then
    if [[ -z "$pg_env_config_bin" ]]; then
      pg_env_write_pg_bin_path "$pg_env_toml_path" "$pg_env_found_bin" || true
    else
      pg_env_config_bin_dir="$(pg_env_normalize_bin_dir "$pg_env_config_bin")"
      if [[ "$pg_env_found_bin" != "$pg_env_config_bin_dir" ]]; then
        if pg_env_confirm_update "Configured pg_bin_path '${pg_env_config_bin}' does not resolve to psql. Update postgres.toml to '${pg_env_found_bin}'?"; then
          pg_env_write_pg_bin_path "$pg_env_toml_path" "$pg_env_found_bin" || true
        fi
      fi
    fi
  fi
fi

if [[ -n "${DB_STATEMENT_TIMEOUT_MS:-}" || -n "${DB_LOCK_TIMEOUT_MS:-}" ]]; then
  pgopts="${PGOPTIONS:-}"
  if [[ -n "${DB_STATEMENT_TIMEOUT_MS:-}" ]]; then
    pgopts="${pgopts} -c statement_timeout=${DB_STATEMENT_TIMEOUT_MS}"
  fi
  if [[ -n "${DB_LOCK_TIMEOUT_MS:-}" ]]; then
    pgopts="${pgopts} -c lock_timeout=${DB_LOCK_TIMEOUT_MS}"
  fi
  export PGOPTIONS="$pgopts"
fi
