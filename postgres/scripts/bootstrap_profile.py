import getpass
import os
import re
import shutil
import subprocess
import sys
import tomllib
import urllib.parse


LATEST_SCHEMA = 1
TOML_PATH = sys.argv[1]
PROJECT_ROOT = sys.argv[2] if len(sys.argv) > 2 else os.getcwd()
IGNORE_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    "target",
    "vendor",
    ".venv",
    "venv",
    "Pods",
    "DerivedData",
    "coverage",
    ".next",
    ".turbo",
    ".cache",
    ".idea",
    ".vscode",
}
SSL_TRUE = {
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
}
SSL_FALSE = {"false", "f", "0", "no", "n", "off", "disable", "disabled"}
FORBIDDEN_ENV_ALIASES = {
    "PROJECT_ROOT": "DB_PROJECT_ROOT",
    "DATABASE_URL": "DB_URL",
    "POSTGRES_URL": "DB_URL",
    "POSTGRESQL_URL": "DB_URL",
    "PGHOST": "DB_URL",
    "PGPORT": "DB_URL",
    "PGDATABASE": "DB_URL",
    "PGUSER": "DB_URL",
    "PGPASSWORD": "DB_URL",
    "PGSSLMODE": "DB_URL",
    "DB_HOST": "DB_URL",
    "DB_PORT": "DB_URL",
    "DB_NAME": "DB_URL",
    "DB_DATABASE": "DB_URL",
    "DB_USER": "DB_URL",
    "DB_PASSWORD": "DB_URL",
}


def prompt(text: str, default: str | None = None) -> str:
    if default is None:
        return input(f"{text}: ").strip()
    value = input(f"{text} [{default}]: ").strip()
    return value or default


def prompt_yes_no(text: str, default: bool = False) -> bool:
    suffix = "Y/n" if default else "y/N"
    value = input(f"{text} [{suffix}]: ").strip().lower()
    if not value:
        return default
    return value in {"y", "yes"}


def is_git_repo(path: str) -> bool:
    try:
        res = subprocess.run(
            ["git", "-C", path, "rev-parse", "--is-inside-work-tree"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return res.returncode == 0
    except OSError:
        return False


def is_toml_gitignored(project_root: str) -> bool:
    if not is_git_repo(project_root):
        return True
    try:
        res = subprocess.run(
            ["git", "-C", project_root, "check-ignore", "-q", ".skills/postgres/postgres.toml"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return res.returncode == 0
    except OSError:
        return True


def ensure_skills_gitignored(project_root: str) -> None:
    if not is_git_repo(project_root):
        return
    if is_toml_gitignored(project_root):
        return

    gitignore_path = os.path.join(project_root, ".gitignore")
    entry = ".skills/"

    print(
        "\nWarning: .skills/postgres/postgres.toml is not ignored by git. "
        "It may contain credentials."
    )
    if not prompt_yes_no(f"Add '{entry}' to {gitignore_path}?", True):
        return

    existing = ""
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8") as f:
            existing = f.read()

    lines = [ln.rstrip("\n") for ln in existing.splitlines()]
    if entry.rstrip("/") in {ln.rstrip("/").strip() for ln in lines if ln.strip()}:
        return

    with open(gitignore_path, "a", encoding="utf-8") as f:
        if existing and not existing.endswith("\n"):
            f.write("\n")
        if existing and existing.strip():
            f.write("\n")
        f.write(entry + "\n")


def prompt_password(text: str, default_present: bool = False) -> str:
    hint = " [leave blank to keep]" if default_present else ""
    value = getpass.getpass(f"{text}{hint}: ").strip()
    return value


def prompt_sslmode(current: bool | None) -> bool:
    default_value = "true" if current else "false"
    while True:
        value = prompt("sslmode (true/false)", default_value).strip().lower()
        if value in SSL_TRUE:
            return True
        if value in SSL_FALSE:
            return False
        print("Enter true or false.")


def clean_value(value: str) -> str:
    value = value.strip().strip(",;")
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        value = value[1:-1]
    return value.strip()


def looks_dynamic(value: str) -> bool:
    return any(token in value for token in ("${", "process.env", "$", "ENV[", "ENV.fetch"))


def normalize_sslmode(value, default: bool | None = None) -> bool | None:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip()
    if not text:
        return default
    lowered = text.lower()
    if lowered in SSL_TRUE:
        return True
    if lowered in SSL_FALSE:
        return False
    return default


def fail_if_unsupported_env_vars() -> None:
    for key, replacement in FORBIDDEN_ENV_ALIASES.items():
        if key in os.environ:
            raise SystemExit(
                f"Unsupported environment variable '{key}'. Use '{replacement}' instead."
            )


def sslmode_to_string(value: bool | None) -> str:
    return "require" if value else "disable"


def parse_url(url: str) -> dict:
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    sslmode = normalize_sslmode(query.get("sslmode", [None])[0])
    username = urllib.parse.unquote(parsed.username or "") if parsed.username else ""
    password = urllib.parse.unquote(parsed.password or "") if parsed.password else ""
    database = urllib.parse.unquote(parsed.path.lstrip("/")) if parsed.path else ""
    return {
        "host": parsed.hostname or "",
        "port": parsed.port or "",
        "database": database,
        "user": username,
        "password": password,
        "sslmode": sslmode,
    }


def build_url(cfg: dict) -> str:
    user = urllib.parse.quote(str(cfg["user"]))
    password = urllib.parse.quote(str(cfg["password"]))
    host = str(cfg["host"])
    port = str(cfg["port"])
    database = urllib.parse.quote(str(cfg["database"]))
    netloc = f"{user}:{password}@{host}:{port}"
    path = f"/{database}"
    query = urllib.parse.urlencode({"sslmode": sslmode_to_string(cfg.get("sslmode"))})
    return urllib.parse.urlunparse(("postgresql", netloc, path, "", query, ""))


def normalize_pg_bin_path(value: str) -> str:
    value = str(value).strip().rstrip("/\\")
    if not value:
        return ""
    base = os.path.basename(value)
    if base in {"psql", "psql.exe"}:
        return os.path.dirname(value)
    return value


def is_pg_bin_path_valid(path: str) -> bool:
    if not path:
        return False
    if not os.path.isdir(path):
        return False
    return os.path.isfile(os.path.join(path, "psql")) or os.path.isfile(
        os.path.join(path, "psql.exe")
    )


def ensure_pg_bin_path(config: dict) -> dict:
    current = normalize_pg_bin_path(config.get("pg_bin_path", ""))
    if current and is_pg_bin_path_valid(current):
        config["pg_bin_path"] = current
        return config

    detected = shutil.which("psql")
    if detected:
        config["pg_bin_path"] = os.path.dirname(detected)
        return config

    while True:
        entered = normalize_pg_bin_path(
            prompt_required("pg_bin_path (directory containing psql)")
        )
        if is_pg_bin_path_valid(entered):
            config["pg_bin_path"] = entered
            return config
        print(
            "Invalid pg_bin_path. Provide the directory that contains psql (or psql.exe)."
        )


def validate_profile(name: str) -> bool:
    return bool(re.match(r"^[a-z0-9_-]+$", name))


def prompt_required(text: str, default: str | None = None, secret: bool = False) -> str:
    while True:
        if secret:
            value = getpass.getpass(f"{text}: ").strip()
        else:
            value = prompt(text, default if default is not None else None)
        if value:
            return value
        if default is not None:
            return default
        print("Value required.")


def suggest_profile_name(source: str, used: set[str]) -> str:
    base = os.path.splitext(os.path.basename(source))[0].lower()
    base = re.sub(r"[^a-z0-9]+", "_", base).strip("_") or "profile"
    name = base
    idx = 2
    while name in used:
        name = f"{base}_{idx}"
        idx += 1
    used.add(name)
    return name


def should_scan_file(path: str) -> bool:
    name = os.path.basename(path)
    if name.startswith(".env") or name in {"Dockerfile", "docker-compose.yml", "docker-compose.yaml"}:
        return True
    ext = os.path.splitext(name)[1].lower()
    allowed = {
        ".env",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".py",
        ".rb",
        ".go",
        ".swift",
        ".java",
        ".kt",
        ".scala",
        ".php",
        ".rs",
        ".cs",
        ".ini",
        ".conf",
        ".cfg",
        ".properties",
        ".envrc",
    }
    return ext in allowed


def scan_project(root: str) -> list[dict]:
    key_re = re.compile(
        r"(?P<key>DB_URL)"
        r"\\s*[:=]\\s*(?P<val>[^\\s#]+)",
        re.IGNORECASE,
    )
    candidates: list[dict] = []
    used_profiles: set[str] = set()
    is_monorepo = detect_monorepo_root(root)

    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for name in files:
            path = os.path.join(base, name)
            if not should_scan_file(path):
                continue
            try:
                if os.path.getsize(path) > 1_000_000:
                    continue
                with open(path, "rb") as f:
                    raw = f.read()
                if b"\x00" in raw:
                    continue
                text = raw.decode("utf-8", errors="ignore")
            except Exception:
                continue

            env = {}
            for match in key_re.finditer(text):
                key = match.group("key").upper()
                val = clean_value(match.group("val"))
                if not val or looks_dynamic(val):
                    continue
                env[key] = val

            url_val = env.get("DB_URL")
            if url_val:
                cfg = parse_url(url_val)
                candidates.append(
                    {
                        "source": os.path.relpath(path, root),
                        "profile": suggest_profile_name(path, used_profiles),
                        "project": infer_project(
                            root, os.path.relpath(path, root), is_monorepo
                        ),
                        "data": cfg,
                    }
                )

    return candidates


def load_toml(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def read_toml_migrations_path(path: str) -> str | None:
    data = load_toml(path)
    migrations = data.get("migrations")
    if isinstance(migrations, dict):
        value = migrations.get("path")
        if value:
            return str(value)
    return None


def write_toml(path: str, data: dict, profile_order: list[str]) -> None:
    config = data.get("configuration")
    if not isinstance(config, dict):
        config = {}
    config.setdefault("schema_version", LATEST_SCHEMA)
    config.setdefault("pg_bin_path", "")

    db = data.get("database", {})
    defaults = {k: v for k, v in db.items() if not isinstance(v, dict)}
    profiles = {k: v for k, v in db.items() if isinstance(v, dict)}

    if "sslmode" not in defaults:
        defaults["sslmode"] = False

    lines: list[str] = []
    lines.append("[configuration]")
    # Keep schema_version first for readability/greppability.
    lines.append(
        f"schema_version = {format_value(config.get('schema_version', LATEST_SCHEMA))}"
    )
    lines.append(f'pg_bin_path = {format_value(config.get("pg_bin_path", ""))}')
    for key in sorted(k for k in config.keys() if k not in {"schema_version", "pg_bin_path"}):
        lines.append(f"{key} = {format_value(config[key])}")

    lines.append("")
    lines.append("[database]")
    for key, value in defaults.items():
        lines.append(f"{key} = {format_value(value)}")

    for profile in profile_order:
        cfg = profiles.get(profile)
        if not cfg:
            continue
        lines.append("")
        lines.append(f"[database.{profile}]")
        for key in ordered_profile_keys(cfg):
            lines.append(f"{key} = {format_value(cfg[key])}")

    # Preserve any additional top-level tables (e.g. [migrations]).
    extras = [(k, v) for k, v in data.items() if k not in {"configuration", "database"}]
    for key, value in extras:
        if isinstance(value, dict):
            lines.append("")
            lines.append(f"[{key}]")
            for k2, v2 in value.items():
                lines.append(f"{k2} = {format_value(v2)}")

    content = "\n".join(lines).rstrip() + "\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def format_value(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


def ordered_profile_keys(cfg: dict) -> list[str]:
    preferred = [
        "project",
        "description",
        "migrations_path",
        "host",
        "port",
        "database",
        "user",
        "password",
        "sslmode",
        "url",
    ]
    keys = [k for k in preferred if k in cfg]
    extra = sorted(k for k in cfg if k not in keys)
    return keys + extra


def coerce_port(value: str) -> str:
    value = str(value).strip()
    return value


def prompt_profile_name(default: str = "local") -> str:
    while True:
        name = prompt("Profile name (lowercase, digits, hyphen, underscore)", default)
        if validate_profile(name):
            return name
        print(
            "Invalid profile name. Use lowercase letters, digits, "
            "underscores, and hyphens only."
        )


def prompt_missing_fields(cfg: dict) -> dict:
    if not cfg.get("host"):
        cfg["host"] = prompt_required("Host")
    if not cfg.get("port"):
        cfg["port"] = prompt_required("Port", "5432")
    if not cfg.get("database"):
        cfg["database"] = prompt_required("Database")
    if not cfg.get("user"):
        cfg["user"] = prompt_required("User")
    if not cfg.get("password"):
        cfg["password"] = prompt_required("Password", secret=True)
    return cfg


def prompt_modifications(cfg: dict) -> dict:
    if not prompt_yes_no("Modify any values?", False):
        return cfg
    cfg["project"] = prompt("Project", cfg.get("project", ""))
    cfg["description"] = prompt("Description", cfg.get("description", ""))
    cfg["migrations_path"] = prompt(
        "Migrations path", cfg.get("migrations_path", "")
    )
    cfg["host"] = prompt("Host", cfg.get("host", ""))
    cfg["port"] = prompt("Port", str(cfg.get("port", "")))
    cfg["database"] = prompt("Database", cfg.get("database", ""))
    cfg["user"] = prompt("User", cfg.get("user", ""))
    password = prompt_password("Password", default_present=bool(cfg.get("password")))
    if password:
        cfg["password"] = password
    cfg["sslmode"] = prompt_sslmode(normalize_sslmode(cfg.get("sslmode"), False))
    return cfg


def format_profile_toml(profile: str, cfg: dict) -> str:
    lines = [f"[database.{profile}]"]
    if cfg.get("project"):
        lines.append(f'project = "{cfg["project"]}"')
    if cfg.get("description"):
        lines.append(f'description = "{cfg["description"]}"')
    if cfg.get("migrations_path"):
        lines.append(f'migrations_path = "{cfg["migrations_path"]}"')
    for key in ["host", "port", "database", "user", "password"]:
        if key in cfg and cfg[key] != "":
            lines.append(f'{key} = "{cfg[key]}"')
    if "sslmode" in cfg and cfg["sslmode"] is not None:
        lines.append(f'sslmode = {format_value(cfg["sslmode"])}')
    return "\n".join(lines)


def choose_candidate(candidates: list[dict]) -> dict | None:
    if not candidates:
        return None
    print("\nFound possible connection configs:\n")
    for idx, cand in enumerate(candidates, 1):
        print(f"{idx}) from {cand['source']}")
        merged = dict(cand["data"])
        if cand.get("project"):
            merged["project"] = cand["project"]
        print(format_profile_toml(cand["profile"], merged))
        print("")
    selection = input("\nPick a number to use (or press Enter to skip): ").strip()
    if not selection:
        return None
    try:
        idx = int(selection)
    except ValueError:
        return None
    if idx < 1 or idx > len(candidates):
        return None
    return candidates[idx - 1]


def detect_monorepo_root(root: str) -> bool:
    markers = {"apps", "packages", "services", "modules", "projects"}
    for name in markers:
        if os.path.isdir(os.path.join(root, name)):
            return True
    return False


def infer_project(root: str, relpath: str, is_monorepo: bool) -> str:
    base = os.path.basename(root.rstrip(os.sep)) or "project"
    if not relpath or relpath == ".":
        return base
    parts = relpath.split(os.sep)
    if len(parts) == 1:
        return base
    if is_monorepo:
        if parts[0] in {"apps", "packages", "services", "modules", "projects"} and len(parts) >= 2:
            return parts[1]
        return parts[0]
    return base


def normalize_migrations_path(value: str) -> str:
    value = value.strip()
    if not value:
        return value
    return os.path.normpath(value)


def find_migrations_matches(root: str, rel_path: str) -> list[str]:
    rel_norm = normalize_migrations_path(rel_path).strip(os.sep)
    if not rel_norm:
        return []
    matches: list[str] = []
    for base, dirs, _ in os.walk(root):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        if base == root:
            continue
        rel = os.path.normpath(os.path.relpath(base, root))
        if rel == rel_norm or rel.endswith(os.sep + rel_norm):
            matches.append(base)
    matches.sort()
    return matches


def choose_migrations_match(matches: list[str], project_root: str) -> str | None:
    if not matches:
        return None
    rel_matches = [
        os.path.normpath(os.path.relpath(match, project_root)) for match in matches
    ]
    rel_matches = list(dict.fromkeys(rel_matches))
    if len(rel_matches) == 1:
        if prompt_yes_no(f"Use existing migrations path '{rel_matches[0]}'?", True):
            return rel_matches[0]
        return None
    print("\nFound matching migrations directories:\n")
    for idx, rel in enumerate(rel_matches, 1):
        print(f"{idx}) {rel}")
    selection = input("\nPick a number to use (or press Enter to skip): ").strip()
    if not selection:
        return None
    try:
        idx = int(selection)
    except ValueError:
        return None
    if idx < 1 or idx > len(rel_matches):
        return None
    return rel_matches[idx - 1]


def resolve_custom_migrations_path(path: str, project_root: str) -> str:
    migrations_path = normalize_migrations_path(path)
    if not migrations_path:
        return migrations_path
    abs_path = (
        migrations_path
        if os.path.isabs(migrations_path)
        else os.path.join(project_root, migrations_path)
    )
    abs_path = os.path.normpath(abs_path)
    if os.path.isdir(abs_path):
        return migrations_path
    if not os.path.isabs(migrations_path):
        if prompt_yes_no(
            f"Search for '{migrations_path}' under '{project_root}'?", True
        ):
            matches = find_migrations_matches(project_root, migrations_path)
            if matches:
                chosen = choose_migrations_match(matches, project_root)
                if chosen:
                    return chosen
            else:
                print("No matching directories found.")
    if prompt_yes_no(f"Create migrations directory at '{abs_path}'?", True):
        os.makedirs(abs_path, exist_ok=True)
    return migrations_path


def read_agents_migrations_path(agents_path: str) -> str | None:
    if not os.path.exists(agents_path):
        return None
    try:
        with open(agents_path, "r", encoding="utf-8") as f:
            for line in f:
                match = re.match(r"^\s*[-*]?\s*DB_MIGRATIONS_PATH\s*=\s*(\S+)\s*$", line)
                if match:
                    return match.group(1)
    except OSError:
        return None
    return None


def update_agents_migrations_path(agents_path: str, migrations_path: str) -> None:
    line_value = f"- DB_MIGRATIONS_PATH={migrations_path}\n"
    if not os.path.exists(agents_path):
        with open(agents_path, "w", encoding="utf-8") as f:
            f.write("## Postgres Skill\n")
            f.write(line_value)
        return

    with open(agents_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    replaced = False
    for idx, line in enumerate(lines):
        if re.match(r"^\s*[-*]?\s*DB_MIGRATIONS_PATH\s*=", line):
            lines[idx] = line_value
            replaced = True
            break

    if not replaced:
        section_idx = None
        for idx, line in enumerate(lines):
            if line.strip().lower().startswith("## postgres"):
                section_idx = idx
                break

        if section_idx is None:
            if lines and not lines[-1].endswith("\n"):
                lines[-1] = lines[-1] + "\n"
            if lines and lines[-1].strip():
                lines.append("\n")
            lines.append("## Postgres Skill\n")
            lines.append(line_value)
        else:
            insert_idx = section_idx + 1
            while insert_idx < len(lines) and not lines[insert_idx].lstrip().startswith("## "):
                insert_idx += 1
            if insert_idx > 0 and lines[insert_idx - 1].strip():
                lines.insert(insert_idx, "\n")
                insert_idx += 1
            lines.insert(insert_idx, line_value)

    with open(agents_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def main() -> None:
    fail_if_unsupported_env_vars()
    print("Postgres profile bootstrap")
    print("(Nothing is written unless you choose to save.)\n")

    scan = prompt_yes_no(
        "Scan project for existing DB configs from files (not env vars)?", False
    )
    candidate = None
    scan_root = os.getcwd()
    if scan:
        scan_root = prompt("Project root to scan", PROJECT_ROOT)
        candidates = scan_project(scan_root)
        if not candidates:
            print("No configs found.")
        else:
            candidate = choose_candidate(candidates)

    project_root = scan_root
    if not scan:
        project_root = prompt(
            "Project root (used only if updating AGENTS.md)", PROJECT_ROOT
        )

    default_profile = candidate["profile"] if candidate else "local"
    profile = prompt_profile_name(default_profile)
    cfg = {"sslmode": False}

    if candidate:
        cfg.update(candidate["data"])
        if candidate.get("project"):
            cfg["project"] = candidate["project"]
    else:
        cfg["project"] = os.path.basename(scan_root.rstrip(os.sep)) or "project"

    cfg["sslmode"] = normalize_sslmode(cfg.get("sslmode"), False)

    agents_path = os.path.join(project_root, "AGENTS.md")
    agents_migrations_path = read_agents_migrations_path(agents_path)
    toml_migrations_path = read_toml_migrations_path(TOML_PATH)
    default_migrations_path = toml_migrations_path or agents_migrations_path or "db/migrations"

    use_default = prompt_yes_no(
        (
            "Use default migrations path "
            f"'{default_migrations_path}' (do not write migrations_path)?"
        ),
        True,
    )
    if use_default:
        cfg["migrations_path"] = ""
        # Ensure the default path exists when it's relative to the project root.
        if not os.path.isabs(default_migrations_path):
            default_path = os.path.join(project_root, default_migrations_path)
            if not os.path.isdir(default_path):
                if prompt_yes_no(
                    f"Create migrations directory at '{default_path}'?", True
                ):
                    os.makedirs(default_path, exist_ok=True)
    else:
        cfg["migrations_path"] = resolve_custom_migrations_path(
            prompt_required("Migrations path"),
            project_root,
        )

    migrations_path_before_mods = cfg.get("migrations_path", "")

    cfg = prompt_missing_fields(cfg)

    print("\nCandidate TOML:\n")
    print(format_profile_toml(profile, cfg))

    cfg = prompt_modifications(cfg)

    if cfg.get("migrations_path"):
        cfg["migrations_path"] = normalize_migrations_path(cfg["migrations_path"])
        if cfg["migrations_path"] != migrations_path_before_mods:
            cfg["migrations_path"] = resolve_custom_migrations_path(
                cfg["migrations_path"],
                project_root,
            )

    if cfg.get("migrations_path"):
        if cfg["migrations_path"] != agents_migrations_path:
            if prompt_yes_no(
                f"Update {agents_path} with DB_MIGRATIONS_PATH={cfg['migrations_path']}?",
                True,
            ):
                update_agents_migrations_path(agents_path, cfg["migrations_path"])

    save = prompt_yes_no(f"Save profile '{profile}' to postgres.toml?", True)
    if not save:
        cfg["sslmode"] = normalize_sslmode(cfg.get("sslmode"), False)
        url = build_url(cfg)
        print("\nTemporary connection (no TOML write):")
        print(f'DB_URL="{url}" \\\n  ./scripts/test_connection.sh')
        return

    ensure_skills_gitignored(project_root)

    data = load_toml(TOML_PATH)
    config = data.get("configuration")
    if not isinstance(config, dict):
        config = {}
    config["schema_version"] = LATEST_SCHEMA
    config = ensure_pg_bin_path(config)
    data["configuration"] = config

    db = data.get("database")
    if not isinstance(db, dict):
        db = {}
    defaults = {k: v for k, v in db.items() if not isinstance(v, dict)}
    profiles = {k: v for k, v in db.items() if isinstance(v, dict)}

    defaults["sslmode"] = normalize_sslmode(defaults.get("sslmode"), False)

    cfg["port"] = coerce_port(cfg.get("port", "5432"))
    cfg["sslmode"] = normalize_sslmode(cfg.get("sslmode"), defaults["sslmode"])

    profiles[profile] = {
        "host": cfg["host"],
        "port": int(cfg["port"]) if str(cfg["port"]).isdigit() else cfg["port"],
        "database": cfg["database"],
        "user": cfg["user"],
        "password": cfg["password"],
    }
    if cfg.get("project"):
        profiles[profile]["project"] = cfg["project"]
    if cfg.get("description"):
        profiles[profile]["description"] = cfg["description"]
    if cfg.get("migrations_path"):
        profiles[profile]["migrations_path"] = cfg["migrations_path"]
    if cfg.get("sslmode") and cfg["sslmode"] != defaults["sslmode"]:
        profiles[profile]["sslmode"] = cfg["sslmode"]

    profile_order = [k for k, v in db.items() if isinstance(v, dict)]
    if profile not in profile_order:
        profile_order.append(profile)

    data["database"] = {**defaults, **profiles}
    write_toml(TOML_PATH, data, profile_order)
    print(f"\nSaved profile '{profile}' to {TOML_PATH}")


if __name__ == "__main__":
    main()
