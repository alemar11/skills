#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from . import checks as checks_lib
from . import lists_cli
from . import stars_cli
from . import user_state


HOST = "github.com"
PROJECT_DIR = Path(__file__).resolve().parents[2]
PROJECT_SRC_DIR = Path(__file__).resolve().parents[1]
SKILL_DIR = Path(__file__).resolve().parents[4]
PYPROJECT_PATH = PROJECT_DIR / "pyproject.toml"


def load_version() -> str:
    if not PYPROJECT_PATH.exists():
        return "1.0.0"
    with PYPROJECT_PATH.open("rb") as handle:
        payload = tomllib.load(handle)
    return str(payload.get("project", {}).get("version", "1.0.0"))


VERSION = load_version()
REPO_PATTERN = re.compile(r"^[^/\s]+/[^/\s]+$")
TOKEN_RE = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class RunResult:
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class CommandResponse:
    result: RunResult
    output_kind: str


@dataclass(frozen=True)
class OptionSpec:
    dest: str
    takes_value: bool = True
    multiple: bool = False
    default: Any = None


CommandHandler = Callable[["CommandSpec", list[str], bool], CommandResponse]


@dataclass(frozen=True)
class CommandSpec:
    command_path: tuple[str, ...]
    usage_tail: str = "[args...]"
    handler: CommandHandler | None = None


class GhopsError(Exception):
    def __init__(
        self,
        message: str,
        *,
        code: str = "command_failed",
        retry: str | None = None,
        exit_code: int = 1,
        command_path: tuple[str, ...] = (),
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.retry = retry
        self.exit_code = exit_code
        self.command_path = command_path


def flag(dest: str) -> OptionSpec:
    return OptionSpec(dest=dest, takes_value=False, default=False)


def value(dest: str, *, default: Any = None, multiple: bool = False) -> OptionSpec:
    return OptionSpec(dest=dest, takes_value=True, default=default, multiple=multiple)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        parsed = parse_root_args(argv)
        if parsed["mode"] == "help":
            print(render_root_help())
            return 0
        if parsed["mode"] == "version":
            print(VERSION)
            return 0
        if parsed["mode"] == "doctor":
            if parsed["json"]:
                print_json_success(("doctor",), collect_doctor_data())
            else:
                print(render_doctor_text(collect_doctor_data()))
            return 0
        if parsed["mode"] == "noun_help":
            print(render_noun_help(parsed["command"]))
            return 0

        command_path = parsed["command"]
        spec = COMMAND_SPECS.get(command_path)
        if spec is None or spec.handler is None:
            raise GhopsError(
                f"Unsupported command: {' '.join(command_path)}",
                code="invalid_arguments",
                exit_code=64,
                command_path=command_path,
            )

        response = spec.handler(spec, parsed["tail"], parsed["json"])
        if response.result.returncode != 0:
            raise build_runtime_error(response.result, command_path)

        if parsed["json"]:
            print_json_success(command_path, parse_output(response.result.stdout, response.output_kind))
            return 0

        if response.result.stdout:
            sys.stdout.write(response.result.stdout)
        if response.result.stderr:
            sys.stderr.write(response.result.stderr)
        return 0
    except GhopsError as exc:
        if parsed_json_requested(argv):
            print_json_error(
                exc.command_path or (),
                code=exc.code,
                message=exc.message,
                retry=exc.retry,
            )
        else:
            print(exc.message, file=sys.stderr)
        return exc.exit_code


def parsed_json_requested(argv: list[str]) -> bool:
    return bool(argv) and argv[0] == "--json"


def parse_root_args(argv: list[str]) -> dict[str, object]:
    if not argv or argv[0] in {"-h", "--help"}:
        return {"mode": "help", "json": False, "command": (), "tail": []}

    json_mode = False
    if argv and argv[0] == "--json":
        json_mode = True
        argv = argv[1:]
        if not argv:
            return {"mode": "help", "json": True, "command": (), "tail": []}

    if argv[0] == "--version":
        return {"mode": "version", "json": json_mode, "command": (), "tail": []}

    if argv[0] == "doctor":
        if len(argv) > 1 and argv[1] in {"-h", "--help"}:
            return {"mode": "noun_help", "json": json_mode, "command": ("doctor",), "tail": []}
        if len(argv) > 1:
            raise GhopsError(
                "doctor does not accept additional arguments.",
                code="invalid_arguments",
                exit_code=64,
                command_path=("doctor",),
            )
        return {"mode": "doctor", "json": json_mode, "command": ("doctor",), "tail": []}

    if argv[0] not in ROOT_NOUNS:
        raise GhopsError(
            f"Unknown command group: {argv[0]}",
            code="invalid_arguments",
            exit_code=64,
        )

    if len(argv) == 1 or argv[1] in {"-h", "--help"}:
        return {"mode": "noun_help", "json": json_mode, "command": (argv[0],), "tail": []}

    for size in range(min(MAX_COMMAND_DEPTH, len(argv)), 0, -1):
        key = tuple(argv[:size])
        if key in GROUP_HELP_PREFIXES and (len(argv) == size or (len(argv) > size and argv[size] in {"-h", "--help"})):
            return {"mode": "noun_help", "json": json_mode, "command": key, "tail": []}

    key, tail = match_command(tuple(argv))
    if tail and tail[0] in {"-h", "--help"} and (key in GROUP_HELP_PREFIXES or key in COMMAND_SPECS):
        return {"mode": "noun_help", "json": json_mode, "command": key, "tail": []}
    return {"mode": "command", "json": json_mode, "command": key, "tail": tail}


def match_command(tokens: tuple[str, ...]) -> tuple[tuple[str, ...], list[str]]:
    for key in SORTED_COMMAND_KEYS:
        if tokens[: len(key)] == key:
            return key, list(tokens[len(key) :])
    raise GhopsError(
        f"Unsupported command: {' '.join(tokens)}",
        code="invalid_arguments",
        exit_code=64,
    )


def render_root_help() -> str:
    lines = [
        "Usage:",
        "  ghops [--json] doctor",
        "  ghops [--json] <noun> <verb> [args...]",
        "  ghops --version",
        "",
        "Public runtime surface:",
    ]
    for noun in ROOT_NOUN_ORDER:
        if noun in ROOT_NOUNS:
            lines.append(f"  {noun:<10} {ROOT_NOUN_DESCRIPTIONS[noun]}")
    lines.extend(
        [
            "",
            "Use:",
            "  ghops <noun> --help",
            "  ghops <noun> <verb> --help",
        ]
    )
    return "\n".join(lines) + "\n"


def render_noun_help(command: tuple[str, ...]) -> str:
    if command == ("doctor",):
        return "Usage:\n  ghops [--json] doctor\n"
    if command not in GROUP_HELP_PREFIXES and command not in COMMAND_SPECS:
        raise GhopsError(
            f"No help is available for {' '.join(command)}.",
            code="invalid_arguments",
            exit_code=64,
            command_path=command,
        )
    return build_help_text(command)


def build_help_text(prefix: tuple[str, ...]) -> str:
    if prefix in COMMAND_SPECS and not has_descendants(prefix):
        spec = COMMAND_SPECS[prefix]
        return f"Usage:\n  ghops [--json] {' '.join(prefix)} {spec.usage_tail}\n"

    direct_leaf_specs: list[CommandSpec] = []
    nested_groups: list[str] = []
    for child in immediate_children(prefix):
        child_path = (*prefix, child)
        if child_path in COMMAND_SPECS:
            direct_leaf_specs.append(COMMAND_SPECS[child_path])
        if has_descendants(child_path):
            nested_groups.append(child)

    lines = ["Usage:"]
    if direct_leaf_specs:
        if len(direct_leaf_specs) == 1 and not nested_groups:
            spec = direct_leaf_specs[0]
            lines.append(f"  ghops [--json] {' '.join(spec.command_path)} {spec.usage_tail}")
        else:
            verbs = "|".join(spec.command_path[-1] for spec in direct_leaf_specs)
            lines.append(f"  ghops [--json] {' '.join(prefix)} <{verbs}> [args...]")
    for child in nested_groups:
        nested_prefix = (*prefix, child)
        nested_leaf_specs = [COMMAND_SPECS[(*nested_prefix, grandchild)] for grandchild in immediate_children(nested_prefix) if (*nested_prefix, grandchild) in COMMAND_SPECS]
        if len(nested_leaf_specs) == 1 and not has_nested_groups(nested_prefix):
            spec = nested_leaf_specs[0]
            lines.append(f"  ghops [--json] {' '.join(spec.command_path)} {spec.usage_tail}")
        elif nested_leaf_specs:
            verbs = "|".join(spec.command_path[-1] for spec in nested_leaf_specs)
            lines.append(f"  ghops [--json] {' '.join(nested_prefix)} <{verbs}> [args...]")
    return "\n".join(lines) + "\n"


def has_descendants(prefix: tuple[str, ...]) -> bool:
    return any(command_path[: len(prefix)] == prefix and len(command_path) > len(prefix) for command_path in COMMAND_SPECS)


def has_nested_groups(prefix: tuple[str, ...]) -> bool:
    return any(has_descendants((*prefix, child)) for child in immediate_children(prefix))


def immediate_children(prefix: tuple[str, ...]) -> list[str]:
    children: list[str] = []
    seen: set[str] = set()
    for command_path in COMMAND_ORDER:
        if command_path[: len(prefix)] == prefix and len(command_path) > len(prefix):
            child = command_path[len(prefix)]
            if child not in seen:
                seen.add(child)
                children.append(child)
    return children


def parse_options(command_path: tuple[str, ...], tail: list[str], specs: dict[str, OptionSpec]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for spec in specs.values():
        if spec.multiple:
            values[spec.dest] = []
        else:
            values[spec.dest] = spec.default

    index = 0
    while index < len(tail):
        token = tail[index]
        if not token.startswith("--"):
            raise GhopsError(
                f"Unsupported argument for {' '.join(command_path)}: {token}",
                code="invalid_arguments",
                exit_code=64,
                command_path=command_path,
            )
        name, inline_value = token.split("=", 1) if "=" in token else (token, None)
        spec = specs.get(name)
        if spec is None:
            raise GhopsError(
                f"Unsupported argument for {' '.join(command_path)}: {name}",
                code="invalid_arguments",
                exit_code=64,
                command_path=command_path,
            )
        if spec.takes_value:
            if inline_value is None:
                if index + 1 >= len(tail):
                    raise GhopsError(
                        f"Missing value for {name}.",
                        code="invalid_arguments",
                        exit_code=64,
                        command_path=command_path,
                    )
                inline_value = tail[index + 1]
                index += 1
            if inline_value == "":
                raise GhopsError(
                    f"Missing value for {name}.",
                    code="invalid_arguments",
                    exit_code=64,
                    command_path=command_path,
                )
            if spec.multiple:
                values[spec.dest].append(inline_value)
            else:
                values[spec.dest] = inline_value
        else:
            if inline_value is not None:
                raise GhopsError(
                    f"{name} does not accept a value.",
                    code="invalid_arguments",
                    exit_code=64,
                    command_path=command_path,
                )
            values[spec.dest] = True
        index += 1
    return values


def run(command: list[str], *, cwd: Path | None = None, input_text: str | None = None) -> RunResult:
    completed = subprocess.run(command, cwd=cwd, text=True, input=input_text, capture_output=True)
    return RunResult(completed.returncode, completed.stdout, completed.stderr)


def helper_result(main_func: Callable[[list[str] | None], int], argv: list[str]) -> RunResult:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        try:
            returncode = int(main_func(argv))
        except SystemExit as exc:
            returncode = int(exc.code) if isinstance(exc.code, int) else 1
    return RunResult(returncode, stdout.getvalue(), stderr.getvalue())


def text_response(stdout: str = "", *, stderr: str = "", returncode: int = 0, output_kind: str = "text") -> CommandResponse:
    return CommandResponse(RunResult(returncode, stdout, stderr), output_kind)


def json_response(payload: object) -> CommandResponse:
    return CommandResponse(RunResult(0, json.dumps(payload, indent=2) + "\n", ""), "json")


def run_gh_text(args: list[str], *, cwd: Path | None = None, input_text: str | None = None) -> RunResult:
    return run(["gh", *args], cwd=cwd, input_text=input_text)


def run_git_text(args: list[str], *, cwd: Path | None = None) -> RunResult:
    return run(["git", *args], cwd=cwd)


def gh_json(args: list[str], *, command_path: tuple[str, ...], cwd: Path | None = None, input_text: str | None = None) -> object:
    result = run_gh_text(args, cwd=cwd, input_text=input_text)
    if result.returncode != 0:
        raise build_runtime_error(result, command_path)
    try:
        return json.loads(result.stdout or "null")
    except json.JSONDecodeError as exc:
        raise GhopsError(
            f"Failed to parse JSON output for {' '.join(command_path)}: {exc}",
            code="command_failed",
            exit_code=1,
            command_path=command_path,
        ) from exc


def gh_api_paginated_list(
    endpoint: str,
    *,
    command_path: tuple[str, ...],
    fields: dict[str, str] | None = None,
    headers: list[str] | None = None,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    page = 1
    while True:
        args = ["api", endpoint, "-X", "GET", "-F", "per_page=100", "-F", f"page={page}"]
        for key, value in (fields or {}).items():
            args.extend(["-F", f"{key}={value}"])
        for header in headers or []:
            args.extend(["-H", header])
        payload = gh_json(args, command_path=command_path)
        if not isinstance(payload, list):
            raise GhopsError(
                f"Unexpected response shape for {' '.join(command_path)}.",
                code="command_failed",
                exit_code=1,
                command_path=command_path,
            )
        page_items = [item for item in payload if isinstance(item, dict)]
        items.extend(page_items)
        if len(payload) < 100:
            break
        page += 1
    return items


def parse_output(stdout: str, output_kind: str) -> object:
    cleaned = stdout.strip()
    if output_kind == "text":
        return {"stdout": cleaned}
    if output_kind == "json":
        if not cleaned:
            return None
        return json.loads(cleaned)
    if output_kind == "json_lines":
        if not cleaned:
            return []
        return [json.loads(line) for line in cleaned.splitlines() if line.strip()]
    if output_kind == "maybe_json":
        if not cleaned:
            return None
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {"stdout": cleaned}
    raise GhopsError(f"Unsupported output kind: {output_kind}", code="internal_error")


def print_json_success(command_path: tuple[str, ...], data: object) -> None:
    payload = {"ok": True, "version": VERSION, "command": list(command_path), "data": data}
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")


def print_json_error(command_path: tuple[str, ...], *, code: str, message: str, retry: str | None) -> None:
    payload = {
        "ok": False,
        "version": VERSION,
        "command": list(command_path),
        "error": {"code": code, "message": message, "retry": retry},
    }
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")


def validate_repo_reference(repo: str) -> str:
    value = repo.strip()
    if not REPO_PATTERN.match(value):
        raise GhopsError(
            f"Invalid --repo value '{repo}'. Use owner/repo.",
            code="invalid_arguments",
            exit_code=64,
        )
    return value


def require_positive_int(name: str, raw_value: str | None, *, command_path: tuple[str, ...]) -> int:
    if not raw_value or not re.fullmatch(r"[1-9][0-9]*", raw_value):
        raise GhopsError(
            f"Invalid --{name} value '{raw_value or ''}'. It must be a positive integer.",
            code="invalid_arguments",
            exit_code=64,
            command_path=command_path,
        )
    return int(raw_value)


def require_allowed_value(name: str, raw_value: str | None, allowed: list[str], *, command_path: tuple[str, ...]) -> str:
    if raw_value not in allowed:
        raise GhopsError(
            f"Invalid --{name} value '{raw_value or ''}'. Use {', '.join(allowed)}.",
            code="invalid_arguments",
            exit_code=64,
            command_path=command_path,
        )
    return str(raw_value)


def normalize_hex_color(raw_value: str, *, command_path: tuple[str, ...]) -> str:
    normalized = raw_value.lstrip("#")
    if not re.fullmatch(r"[A-Fa-f0-9]{6}", normalized):
        raise GhopsError(
            f"Invalid --color value '{raw_value}'. Use six hex digits, e.g. 1F9D55.",
            code="invalid_arguments",
            exit_code=64,
            command_path=command_path,
        )
    return normalized


def is_git_repo() -> bool:
    repo_result = run_git_text(["rev-parse", "--is-inside-work-tree"])
    return repo_result.returncode == 0 and repo_result.stdout.strip() == "true"


def normalize_remote_url(remote: str | None) -> str | None:
    if not remote:
        return None
    repo = re.sub(r"^git@[^:]+:", "", remote)
    repo = re.sub(r"^https?://[^/]+/", "", repo)
    repo = re.sub(r"^ssh://[^/]+/", "", repo)
    repo = re.sub(r"^git://[^/]+/", "", repo)
    repo = re.sub(r"\.git$", "", repo)
    repo = repo.rstrip("/")
    if REPO_PATTERN.fullmatch(repo):
        return repo
    return None


def resolve_repo(repo_ref: str | None, allow_non_project: bool, *, command_path: tuple[str, ...]) -> str:
    if repo_ref:
        return validate_repo_reference(repo_ref)
    if not is_git_repo():
        if allow_non_project:
            raise GhopsError(
                "repo is required when using --allow-non-project.",
                code="repo_context_missing",
                exit_code=2,
                command_path=command_path,
            )
        raise GhopsError(
            "No git repository detected. Pass --repo <owner/repo> for non-project operations.",
            code="repo_context_missing",
            exit_code=3,
            command_path=command_path,
        )
    remote_result = run_git_text(["remote", "get-url", "origin"])
    if remote_result.returncode != 0:
        raise GhopsError(
            "No origin remote found. Pass --repo <owner/repo>.",
            code="repo_context_missing",
            exit_code=4,
            command_path=command_path,
        )
    repo = normalize_remote_url(remote_result.stdout.strip())
    if repo is None:
        raise GhopsError(
            f"Could not resolve owner/repo from git remote: {remote_result.stdout.strip()}",
            code="repo_context_missing",
            exit_code=5,
            command_path=command_path,
        )
    return repo


def require_git_repo(command_path: tuple[str, ...]) -> None:
    if not is_git_repo():
        raise GhopsError(
            "No git repository detected.",
            code="repo_context_missing",
            exit_code=3,
            command_path=command_path,
        )


def current_branch(command_path: tuple[str, ...]) -> str:
    require_git_repo(command_path)
    result = run_git_text(["rev-parse", "--abbrev-ref", "HEAD"])
    branch = result.stdout.strip()
    if result.returncode != 0 or not branch or branch == "HEAD":
        raise GhopsError(
            "Detached HEAD detected. Check out a branch first.",
            code="repo_context_missing",
            exit_code=5,
            command_path=command_path,
        )
    return branch


def tracking_remote_name(branch: str) -> str | None:
    result = run_git_text(["config", "--get", f"branch.{branch}.remote"])
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def tracking_branch_name(branch: str) -> str | None:
    result = run_git_text(["config", "--get", f"branch.{branch}.merge"])
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    if not value:
        return None
    return value.removeprefix("refs/heads/")


def branch_is_long_lived(branch: str) -> bool:
    return branch in {"main", "master", "stable", "develop", "development", "trunk", "next", "integration", "staging"} or branch.startswith("release/")


def parse_auth_login(status_text: str) -> str | None:
    patterns = (r"Logged in to [^\s]+ as ([^\s]+)", r"Logged in to [^\s]+ account ([^\s]+)")
    for pattern in patterns:
        match = re.search(pattern, status_text)
        if match:
            return match.group(1)
    return None


def collect_doctor_data() -> dict[str, object]:
    gh_path = shutil_which("gh")
    gh_version = None
    gh_installed = gh_path is not None
    gh_error = None
    if gh_installed:
        version_result = run(["gh", "--version"])
        if version_result.returncode == 0:
            first_line = next((line for line in version_result.stdout.splitlines() if line.strip()), "")
            parts = first_line.split()
            gh_version = parts[2] if len(parts) >= 3 else None
        else:
            gh_error = first_nonempty_line(version_result.stderr, version_result.stdout)

    auth_authenticated = False
    auth_login = None
    auth_error = None
    if gh_installed:
        auth_result = run(["gh", "auth", "status", "--hostname", HOST])
        status_text = "\n".join(part for part in (auth_result.stdout, auth_result.stderr) if part).strip()
        if auth_result.returncode == 0 and "Logged in to" in status_text:
            auth_authenticated = True
            auth_login = parse_auth_login(status_text)
        else:
            auth_error = first_nonempty_line(status_text)

    git_repo = False
    remote_url = None
    resolved_repo = None
    current = None
    repo_result = run_git_text(["rev-parse", "--is-inside-work-tree"])
    if repo_result.returncode == 0 and repo_result.stdout.strip() == "true":
        git_repo = True
        branch_result = run_git_text(["rev-parse", "--abbrev-ref", "HEAD"])
        branch_value = branch_result.stdout.strip()
        if branch_result.returncode == 0 and branch_value and branch_value != "HEAD":
            current = branch_value
        remote_result = run_git_text(["remote", "get-url", "origin"])
        if remote_result.returncode == 0:
            remote_url = remote_result.stdout.strip() or None
            resolved_repo = normalize_remote_url(remote_url)

    ready = bool(gh_installed and auth_authenticated)
    return {
        "gh": {"installed": gh_installed, "path": gh_path, "version": gh_version, "error": gh_error},
        "auth": {"host": HOST, "authenticated": auth_authenticated, "login": auth_login, "source": "gh", "error": auth_error},
        "project": {
            "is_git_repo": git_repo,
            "current_branch": current,
            "origin_remote": remote_url,
            "resolved_repo": resolved_repo,
            "allow_non_project": True,
        },
        "ready": ready,
    }


def render_doctor_text(data: dict[str, object]) -> str:
    gh_data = data["gh"]
    auth_data = data["auth"]
    project_data = data["project"]
    lines = [
        f"gh installed: {'yes' if gh_data['installed'] else 'no'}",
        f"gh version: {gh_data['version'] or 'unknown'}",
        f"Authenticated to {auth_data['host']}: {'yes' if auth_data['authenticated'] else 'no'}",
        f"Login: {auth_data['login'] or 'unknown'}",
        f"Git repository: {'yes' if project_data['is_git_repo'] else 'no'}",
        f"Resolved repo: {project_data['resolved_repo'] or 'none'}",
        f"Allow non-project: {'yes' if project_data['allow_non_project'] else 'no'}",
        f"Ready: {'yes' if data['ready'] else 'no'}",
    ]
    return "\n".join(lines) + "\n"


def first_nonempty_line(*parts: str) -> str | None:
    for part in parts:
        for line in part.splitlines():
            line = line.strip()
            if line:
                return line
    return None


def extract_runtime_error_message(result: RunResult) -> str | None:
    filtered = filter_runtime_noise(result.stderr, result.stdout)
    meaningful = first_nonempty_line(filtered)
    if meaningful:
        return meaningful
    return first_nonempty_line(result.stderr, result.stdout)


def filter_runtime_noise(*parts: str) -> str:
    kept: list[str] = []
    for part in parts:
        for raw_line in part.splitlines():
            line = raw_line.strip()
            if line and not is_runtime_noise_line(line):
                kept.append(line)
    return "\n".join(kept)


def is_runtime_noise_line(line: str) -> bool:
    noise_prefixes = (
        "gh is installed:",
        "Authenticated to ",
        "Current directory is a git repository.",
        "origin remote:",
        "gh preflight checks passed.",
    )
    noise_contains = (
        "Logged in to github.com account ",
        "Token scopes:",
        "Git operations protocol:",
        "Active account:",
    )
    if line == "github.com":
        return True
    if any(line.startswith(prefix) for prefix in noise_prefixes):
        return True
    if any(fragment in line for fragment in noise_contains):
        return True
    if line.startswith(("✓ ", "-", "X ")):
        return True
    if "************************************" in line:
        return True
    return False


def build_runtime_error(result: RunResult, command_path: tuple[str, ...]) -> GhopsError:
    message = extract_runtime_error_message(result) or "Command failed."
    lower = message.lower()
    code = "command_failed"
    retry = None
    if "gh is not installed" in lower:
        code = "gh_missing"
        retry = "command -v gh && gh --version"
    elif "not authenticated" in lower or "gh auth login" in lower or "authentication required" in lower:
        code = "gh_auth_missing"
        retry = "gh auth login"
    elif "no git repository" in lower or "not a git repository" in lower:
        code = "repo_context_missing"
        retry = "gh repo view --json nameWithOwner"
    elif "cross-repo" in lower or "current directory resolves to" in lower:
        code = "repo_context_mismatch"
        retry = "gh repo view --json nameWithOwner"
    elif "missing required scopes" in lower:
        code = "gh_scope_missing"
    elif result.returncode == 64:
        code = "invalid_arguments"
    return GhopsError(message, code=code, retry=retry, exit_code=result.returncode or 1, command_path=command_path)


def shutil_which(binary: str) -> str | None:
    for base in os.environ.get("PATH", "").split(os.pathsep):
        candidate = Path(base) / binary
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def summary_names(items: list[dict[str, Any]] | None, key: str) -> str:
    values: list[str] = []
    for item in items or []:
        value = item.get(key)
        if isinstance(value, str) and value:
            values.append(value)
    return ", ".join(values) if values else "none"


def snippet(text: str, *, limit: int = 220) -> str:
    compact = (text or "").replace("\r\n", "\n").replace("\n", " ").strip()
    if len(compact) > limit:
        return compact[: limit - 3] + "..."
    return compact


def first_mutating_request_flag(extra: list[str]) -> str | None:
    exact_forbidden = {"-X", "--method", "--input", "-f", "-F", "--field", "--raw-field"}
    prefix_forbidden = ("-X", "--method=", "--input=", "-f", "-F", "--field=", "--raw-field=")
    for token in extra:
        if token in exact_forbidden:
            return token
        for prefix in prefix_forbidden:
            if token.startswith(prefix) and token != prefix:
                return prefix.rstrip("=")
    return None


def maybe_allows_json_inspect(tail: list[str]) -> None:
    for token in tail:
        if token == "--job-id" or token.startswith("--job-id="):
            raise GhopsError(
                "actions inspect --json does not support --job-id because that mode mixes structured summary data with plain logs.",
                code="invalid_arguments",
                exit_code=64,
                command_path=("actions", "inspect"),
            )
        if token == "--artifact-name" or token.startswith("--artifact-name="):
            raise GhopsError(
                "actions inspect --json does not support --artifact-name because artifact download mode is not a structured JSON read.",
                code="invalid_arguments",
                exit_code=64,
                command_path=("actions", "inspect"),
            )


def repos_list_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    opts = parse_options(spec.command_path, tail, {
        "--owner": value("owner"),
        "--type": value("repo_type", default="all"),
        "--all": flag("all"),
        "--limit": value("limit", default="100"),
        "--allow-non-project": flag("allow_non_project"),
    })
    owner = opts["owner"]
    if owner and "/" in owner:
        raise GhopsError("Invalid --owner value. Use a plain owner name.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
    repo_type = require_allowed_value("type", opts["repo_type"], ["all", "owner", "member", "public", "private", "forks", "archived", "sources"], command_path=spec.command_path)
    limit = require_positive_int("limit", opts["limit"], command_path=spec.command_path)
    if opts["all"]:
        limit = 1000
    endpoint_kind = "self"
    endpoint = "user/repos"
    if owner:
        probe = run_gh_text(["api", f"orgs/{owner}", "--silent"])
        if probe.returncode == 0:
            endpoint_kind = "org"
            endpoint = f"orgs/{owner}/repos"
        else:
            endpoint_kind = "user"
            endpoint = f"users/{owner}/repos"
    api_type = repo_type
    server_filtered = True
    if f"{endpoint_kind}:{repo_type}" in {
        "self:public", "self:private", "self:forks", "self:sources", "self:archived",
        "user:public", "user:private", "user:forks", "user:sources", "user:archived",
        "org:archived",
    }:
        api_type = "all"
        server_filtered = False

    def matches(item: dict[str, Any]) -> bool:
        if repo_type in {"all", "owner", "member"}:
            return True
        if repo_type == "public":
            return not bool(item.get("private"))
        if repo_type == "private":
            return bool(item.get("private"))
        if repo_type == "forks":
            return bool(item.get("fork"))
        if repo_type == "sources":
            return not bool(item.get("fork"))
        if repo_type == "archived":
            return bool(item.get("archived"))
        return True

    page = 1
    items: list[dict[str, Any]] = []
    while len(items) < limit:
        per_page = min(limit - len(items), 100) if server_filtered else 100
        payload = gh_json(["api", endpoint, "-X", "GET", "-F", f"per_page={per_page}", "-F", f"page={page}", "-F", f"type={api_type}"], command_path=spec.command_path)
        if not isinstance(payload, list):
            raise GhopsError("Unexpected repository list response shape.", code="command_failed", command_path=spec.command_path)
        if not payload:
            break
        for repo in payload:
            if not isinstance(repo, dict) or not matches(repo):
                continue
            items.append({
                "name": repo.get("name"),
                "full_name": repo.get("full_name"),
                "private": repo.get("private"),
                "visibility": repo.get("visibility"),
                "fork": repo.get("fork"),
                "archived": repo.get("archived"),
                "owner": ((repo.get("owner") or {}).get("login")),
            })
            if len(items) >= limit:
                break
        if len(payload) < per_page:
            break
        page += 1
    if json_mode:
        return json_response(items)
    text = "\n".join(json.dumps(item, separators=(",", ":")) for item in items)
    return text_response(text + ("\n" if text else ""))


def repos_view_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    opts = parse_options(spec.command_path, tail, {"--repo": value("repo"), "--allow-non-project": flag("allow_non_project")})
    repo = resolve_repo(opts["repo"], bool(opts["allow_non_project"]), command_path=spec.command_path)
    data = gh_json(["repo", "view", repo, "--json", "nameWithOwner,description,defaultBranchRef,visibility,isPrivate,isArchived,isFork,url"], command_path=spec.command_path)
    if not isinstance(data, dict):
        raise GhopsError("Unexpected repository view response shape.", code="command_failed", command_path=spec.command_path)
    visibility = data.get("visibility") or ("private" if data.get("isPrivate") else "public")
    normalized = {
        "repo": data.get("nameWithOwner", ""),
        "description": data.get("description") or "",
        "default_branch": ((data.get("defaultBranchRef") or {}).get("name") or ""),
        "visibility": visibility,
        "archived": bool(data.get("isArchived")),
        "fork": bool(data.get("isFork")),
        "url": data.get("url") or "",
    }
    if json_mode:
        return json_response(normalized)
    text = "\n".join([
        f"Repository: {normalized['repo']}",
        f"Description: {normalized['description'] or '(empty)'}",
        f"Default branch: {normalized['default_branch'] or 'unknown'}",
        f"Visibility: {normalized['visibility']}",
        f"Archived: {'yes' if normalized['archived'] else 'no'}",
        f"Fork: {'yes' if normalized['fork'] else 'no'}",
        f"URL: {normalized['url']}",
    ]) + "\n"
    return text_response(text)


def issues_list_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    opts = parse_options(spec.command_path, tail, {
        "--state": value("state", default="open"),
        "--labels": value("labels"),
        "--limit": value("limit", default="20"),
        "--repo": value("repo"),
        "--allow-non-project": flag("allow_non_project"),
    })
    state = require_allowed_value("state", opts["state"], ["open", "closed", "all"], command_path=spec.command_path)
    limit = require_positive_int("limit", opts["limit"], command_path=spec.command_path)
    repo = resolve_repo(opts["repo"], bool(opts["allow_non_project"]), command_path=spec.command_path)
    args = ["issue", "list", "--repo", repo, "--state", state, "--limit", str(limit), "--json", "number,title,state,labels,assignees,url,updatedAt"]
    if opts["labels"]:
        args.extend(["--label", str(opts["labels"])])
    payload = gh_json(args, command_path=spec.command_path)
    return json_response(payload) if json_mode else text_response(json.dumps(payload, indent=2) + "\n")


def issues_view_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    opts = parse_options(spec.command_path, tail, {"--issue": value("issue"), "--repo": value("repo"), "--allow-non-project": flag("allow_non_project")})
    issue = require_positive_int("issue", opts["issue"], command_path=spec.command_path)
    repo = resolve_repo(opts["repo"], bool(opts["allow_non_project"]), command_path=spec.command_path)
    payload = gh_json(["issue", "view", str(issue), "--repo", repo, "--json", "number,title,state,labels,assignees,body,createdAt,updatedAt,url,author,comments"], command_path=spec.command_path)
    if json_mode:
        return json_response(payload)
    if not isinstance(payload, dict):
        raise GhopsError("Unexpected issue view response shape.", code="command_failed", command_path=spec.command_path)
    author = ((payload.get("author") or {}).get("login") or "unknown")
    text = "\n".join([
        f"Issue: {repo}#{payload.get('number')} {payload.get('title', '')}",
        f"State: {payload.get('state', '')}",
        f"Author: {author}",
        f"Assignees: {summary_names(payload.get('assignees'), 'login')}",
        f"Labels: {summary_names(payload.get('labels'), 'name')}",
        f"Updated: {payload.get('updatedAt', '')}",
        f"URL: {payload.get('url', '')}",
        f"Body: {snippet(payload.get('body') or '') or '(empty)'}",
    ]) + "\n"
    return text_response(text)


def simple_gh_text_handler(args_builder: Callable[[dict[str, Any], tuple[str, ...]], list[str]], option_specs: dict[str, OptionSpec], required: dict[str, str] | None = None) -> CommandHandler:
    def handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
        opts = parse_options(spec.command_path, tail, option_specs)
        for field, kind in (required or {}).items():
            if kind == "issue":
                require_positive_int(field, opts[field], command_path=spec.command_path)
            elif kind == "pr":
                require_positive_int(field, opts[field], command_path=spec.command_path)
            elif kind == "repo":
                validate_repo_reference(str(opts[field]))
            elif kind == "text" and not opts[field]:
                raise GhopsError(f"Missing required --{field}.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
        args = args_builder(opts, spec.command_path)
        result = run_gh_text(args)
        return CommandResponse(result, "text")
    return handler


def issues_create_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    opts = parse_options(spec.command_path, tail, {
        "--title": value("title"),
        "--body": value("body"),
        "--labels": value("labels"),
        "--assignees": value("assignees"),
        "--repo": value("repo"),
        "--allow-non-project": flag("allow_non_project"),
    })
    if not opts["title"]:
        raise GhopsError("Missing required --title.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
    repo = resolve_repo(opts["repo"], bool(opts["allow_non_project"]), command_path=spec.command_path)
    args = ["issue", "create", "--repo", repo, "--title", str(opts["title"])]
    if opts["body"]:
        args.extend(["--body", str(opts["body"])])
    if opts["labels"]:
        args.extend(["--label", str(opts["labels"])])
    if opts["assignees"]:
        args.extend(["--assignee", str(opts["assignees"])])
    return CommandResponse(run_gh_text(args), "text")


def issues_update_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    opts = parse_options(spec.command_path, tail, {
        "--issue": value("issue"),
        "--title": value("title"),
        "--body": value("body"),
        "--state": value("state"),
        "--type": value("issue_type"),
        "--type-label-bug": value("type_label_bug", default="bug"),
        "--type-label-task": value("type_label_task", default="task"),
        "--milestone": value("milestone"),
        "--milestone-id": value("milestone_id"),
        "--remove-milestone": flag("remove_milestone"),
        "--add-labels": value("add_labels"),
        "--remove-labels": value("remove_labels"),
        "--assignees": value("assignees"),
        "--remove-assignees": value("remove_assignees"),
        "--repo": value("repo"),
        "--allow-non-project": flag("allow_non_project"),
    })
    issue = require_positive_int("issue", opts["issue"], command_path=spec.command_path)
    if not any(opts[key] for key in ("title", "body", "state", "issue_type", "milestone", "milestone_id", "remove_milestone", "add_labels", "remove_labels", "assignees", "remove_assignees")):
        raise GhopsError(
            "At least one update field is required: --title, --body, --state, --type, --milestone, --milestone-id, --remove-milestone, --add-labels, --remove-labels, --assignees, or --remove-assignees.",
            code="invalid_arguments",
            exit_code=64,
            command_path=spec.command_path,
        )
    if opts["state"]:
        require_allowed_value("state", opts["state"], ["open", "closed"], command_path=spec.command_path)
    if opts["issue_type"]:
        require_allowed_value("type", opts["issue_type"], ["bug", "task", "none"], command_path=spec.command_path)
    if opts["milestone_id"]:
        require_positive_int("milestone-id", opts["milestone_id"], command_path=spec.command_path)
    if opts["type_label_bug"] == opts["type_label_task"]:
        raise GhopsError("--type-label-bug and --type-label-task must be different label names.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
    if opts["milestone"] and opts["milestone_id"]:
        raise GhopsError("Use either --milestone or --milestone-id, not both.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
    if (opts["milestone"] or opts["milestone_id"]) and opts["remove_milestone"]:
        raise GhopsError("Use either --milestone / --milestone-id or --remove-milestone, not both.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
    repo = resolve_repo(opts["repo"], bool(opts["allow_non_project"]), command_path=spec.command_path)
    args = ["issue", "edit", str(issue), "--repo", repo]
    if opts["title"]:
        args.extend(["--title", str(opts["title"])])
    if opts["body"]:
        args.extend(["--body", str(opts["body"])])
    if opts["state"] == "open":
        args.append("--reopen")
    elif opts["state"] == "closed":
        args.append("--close")
    if opts["milestone"]:
        args.extend(["--milestone", str(opts["milestone"])])
    if opts["milestone_id"]:
        args.extend(["--milestone", str(opts["milestone_id"])])
    if opts["remove_milestone"]:
        args.append("--remove-milestone")
    if opts["add_labels"]:
        args.extend(["--add-label", str(opts["add_labels"])])
    if opts["remove_labels"]:
        args.extend(["--remove-label", str(opts["remove_labels"])])
    if opts["assignees"]:
        args.extend(["--add-assignee", str(opts["assignees"])])
    if opts["remove_assignees"]:
        args.extend(["--remove-assignee", str(opts["remove_assignees"])])
    issue_type = opts["issue_type"]
    if issue_type == "none":
        if opts["type_label_bug"]:
            args.extend(["--remove-label", str(opts["type_label_bug"])])
        if opts["type_label_task"]:
            args.extend(["--remove-label", str(opts["type_label_task"])])
    elif issue_type == "bug":
        if opts["type_label_task"]:
            args.extend(["--remove-label", str(opts["type_label_task"])])
        if opts["type_label_bug"]:
            args.extend(["--add-label", str(opts["type_label_bug"])])
    elif issue_type == "task":
        if opts["type_label_bug"]:
            args.extend(["--remove-label", str(opts["type_label_bug"])])
        if opts["type_label_task"]:
            args.extend(["--add-label", str(opts["type_label_task"])])
    return CommandResponse(run_gh_text(args), "text")


def issues_comment_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    opts = parse_options(spec.command_path, tail, {"--issue": value("issue"), "--body": value("body"), "--repo": value("repo"), "--allow-non-project": flag("allow_non_project")})
    issue = require_positive_int("issue", opts["issue"], command_path=spec.command_path)
    if not opts["body"]:
        raise GhopsError("Missing required --body.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
    repo = resolve_repo(opts["repo"], bool(opts["allow_non_project"]), command_path=spec.command_path)
    return CommandResponse(run_gh_text(["issue", "comment", str(issue), "--repo", repo, "--body", str(opts["body"])]), "text")


def issues_comments_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    opts = parse_options(spec.command_path, tail, {"--issue": value("issue"), "--repo": value("repo"), "--allow-non-project": flag("allow_non_project")})
    issue = require_positive_int("issue", opts["issue"], command_path=spec.command_path)
    repo = resolve_repo(opts["repo"], bool(opts["allow_non_project"]), command_path=spec.command_path)
    payload = gh_api_paginated_list(f"repos/{repo}/issues/{issue}/comments", command_path=spec.command_path)
    return json_response(payload) if json_mode else text_response(json.dumps(payload, indent=2) + "\n")


def issues_close_reopen_handler(action: str) -> CommandHandler:
    def handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
        opts = parse_options(spec.command_path, tail, {"--issue": value("issue"), "--repo": value("repo"), "--allow-non-project": flag("allow_non_project")})
        issue = require_positive_int("issue", opts["issue"], command_path=spec.command_path)
        repo = resolve_repo(opts["repo"], bool(opts["allow_non_project"]), command_path=spec.command_path)
        return CommandResponse(run_gh_text(["issue", action, str(issue), "--repo", repo]), "text")
    return handler


def issues_close_with_evidence_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    opts = parse_options(spec.command_path, tail, {
        "--issue": value("issue"),
        "--commit-sha": value("commit_sha"),
        "--commit-url": value("commit_url"),
        "--pr-url": value("pr_url"),
        "--repo": value("repo"),
        "--allow-non-project": flag("allow_non_project"),
        "--dry-run": flag("dry_run"),
    })
    issue = require_positive_int("issue", opts["issue"], command_path=spec.command_path)
    commit_sha = str(opts["commit_sha"] or "")
    if not re.fullmatch(r"[0-9A-Fa-f]{7,40}", commit_sha):
        raise GhopsError(
            f"Invalid --commit-sha value '{commit_sha}'. Use a 7-40 character hex commit SHA.",
            code="invalid_arguments",
            exit_code=64,
            command_path=spec.command_path,
        )
    allow_non_project = bool(opts["allow_non_project"] or opts["repo"])
    repo = resolve_repo(opts["repo"], allow_non_project, command_path=spec.command_path)
    commit_url = str(opts["commit_url"] or f"https://github.com/{repo}/commit/{commit_sha}")
    short_sha = commit_sha[:7]
    body = f"Implemented in commit {short_sha} ({commit_url})."
    if opts["pr_url"]:
        body = f"{body} Implemented via PR {opts['pr_url']}."
    state = str(gh_json(["issue", "view", str(issue), "--repo", repo, "--json", "state"], command_path=spec.command_path).get("state"))
    if state != "OPEN":
        return text_response(f"Issue #{issue} is already {state}; no changes made.\n")
    if opts["dry_run"]:
        text = "\n".join([
            f"Dry run: issue #{issue} in {repo} is OPEN.",
            "Dry run: would post comment body:",
            body,
            f"Dry run: would close issue #{issue}.",
            "",
        ])
        return text_response(text)
    comment_result = run_gh_text(["issue", "comment", str(issue), "--repo", repo, "--body", body])
    if comment_result.returncode != 0:
        return CommandResponse(comment_result, "text")
    close_result = run_gh_text(["issue", "close", str(issue), "--repo", repo])
    if close_result.returncode != 0:
        return CommandResponse(close_result, "text")
    return text_response(f"Closed issue #{issue} in {repo} with implementation evidence.\n")


def transfer_note_body(prefix: str, source_repo: str, issue: int, source_url: str, body_text: str) -> str:
    pieces = [f"{prefix} {source_repo}#{issue} ({source_url})."]
    if body_text:
        pieces.extend(["", body_text])
    return "\n".join(pieces)


def issue_copy_like_handler(*, move: bool) -> CommandHandler:
    def handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
        opts = parse_options(spec.command_path, tail, {
            "--issue": value("issue"),
            "--source-repo": value("source_repo"),
            "--target-repo": value("target_repo"),
            "--dry-run": flag("dry_run"),
        })
        issue = require_positive_int("issue", opts["issue"], command_path=spec.command_path)
        source_repo = validate_repo_reference(str(opts["source_repo"] or ""))
        target_repo = validate_repo_reference(str(opts["target_repo"] or ""))
        if move and source_repo == target_repo:
            raise GhopsError("--source-repo and --target-repo must be different for issue moves.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
        issue_payload = gh_json(["issue", "view", str(issue), "--repo", source_repo, "--json", "title,state,url,body"], command_path=spec.command_path)
        title = str(issue_payload.get("title") or "")
        state = str(issue_payload.get("state") or "")
        source_url = str(issue_payload.get("url") or "")
        body_text = str(issue_payload.get("body") or "")
        transfer_note = transfer_note_body("Moved from" if move else "Copied from", source_repo, issue, source_url, body_text)
        if opts["dry_run"]:
            lines = [
                f"Dry run: would {'move' if move else 'copy'} issue #{issue} from {source_repo} to {target_repo}.",
                f"Dry run: source state: {state}" if move else f"Dry run: target title: {title}",
                f"Dry run: target body note: {transfer_note.splitlines()[0]}",
                "",
            ]
            return text_response("\n".join(line for line in lines if line))
        create_result = run_gh_text(["issue", "create", "--repo", target_repo, "--title", title, "--body", transfer_note])
        if create_result.returncode != 0:
            return CommandResponse(create_result, "text")
        new_url = create_result.stdout.strip()
        if not move:
            return text_response(create_result.stdout, stderr=create_result.stderr)
        new_number = new_url.rsplit("/", 1)[-1]
        source_note = f"Moved to {target_repo}#{new_number} ({new_url}). Continuing work there."
        comment_result = run_gh_text(["issue", "comment", str(issue), "--repo", source_repo, "--body", source_note])
        if comment_result.returncode != 0:
            return CommandResponse(comment_result, "text")
        if state == "OPEN":
            close_result = run_gh_text(["issue", "close", str(issue), "--repo", source_repo])
            if close_result.returncode != 0:
                return CommandResponse(close_result, "text")
        return text_response(new_url + ("\n" if not new_url.endswith("\n") else ""))
    return handler


def issues_lock_unlock_handler(action: str) -> CommandHandler:
    def handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
        specs = {"--issue": value("issue"), "--repo": value("repo"), "--allow-non-project": flag("allow_non_project")}
        if action == "lock":
            specs["--reason"] = value("reason")
        opts = parse_options(spec.command_path, tail, specs)
        issue = require_positive_int("issue", opts["issue"], command_path=spec.command_path)
        repo = resolve_repo(opts["repo"], bool(opts["allow_non_project"]), command_path=spec.command_path)
        args = ["issue", action, str(issue), "--repo", repo]
        if action == "lock" and opts.get("reason"):
            args.extend(["--reason", str(opts["reason"])])
        return CommandResponse(run_gh_text(args), "text")
    return handler


def issues_pin_unpin_handler(action: str) -> CommandHandler:
    def handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
        opts = parse_options(spec.command_path, tail, {"--issue": value("issue"), "--repo": value("repo"), "--allow-non-project": flag("allow_non_project")})
        issue = require_positive_int("issue", opts["issue"], command_path=spec.command_path)
        repo = resolve_repo(opts["repo"], bool(opts["allow_non_project"]), command_path=spec.command_path)
        return CommandResponse(run_gh_text(["issue", action, str(issue), "--repo", repo]), "text")
    return handler


def issues_labels_list_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    opts = parse_options(spec.command_path, tail, {"--repo": value("repo"), "--allow-non-project": flag("allow_non_project")})
    repo = resolve_repo(opts["repo"], bool(opts["allow_non_project"]), command_path=spec.command_path)
    payload = gh_json(["label", "list", "--repo", repo, "--json", "name,color,description,isDefault"], command_path=spec.command_path)
    return json_response(payload) if json_mode else text_response(json.dumps(payload, indent=2) + "\n")


def issues_labels_create_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    opts = parse_options(spec.command_path, tail, {"--name": value("name"), "--color": value("color"), "--description": value("description"), "--repo": value("repo"), "--allow-non-project": flag("allow_non_project")})
    if not opts["name"]:
        raise GhopsError("Missing required --name.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
    repo = resolve_repo(opts["repo"], bool(opts["allow_non_project"]), command_path=spec.command_path)
    args = ["label", "create", str(opts["name"]), "--repo", repo]
    if opts["color"]:
        args.extend(["--color", normalize_hex_color(str(opts["color"]), command_path=spec.command_path)])
    if opts["description"]:
        args.extend(["--description", str(opts["description"])])
    return CommandResponse(run_gh_text(args), "text")


def issues_labels_update_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    opts = parse_options(spec.command_path, tail, {"--name": value("name"), "--new-name": value("new_name"), "--color": value("color"), "--description": value("description"), "--repo": value("repo"), "--allow-non-project": flag("allow_non_project")})
    if not opts["name"]:
        raise GhopsError("Missing required --name.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
    repo = resolve_repo(opts["repo"], bool(opts["allow_non_project"]), command_path=spec.command_path)
    args = ["label", "edit", str(opts["name"]), "--repo", repo]
    if opts["new_name"]:
        args.extend(["--name", str(opts["new_name"])])
    if opts["color"]:
        args.extend(["--color", normalize_hex_color(str(opts["color"]), command_path=spec.command_path)])
    if opts["description"]:
        args.extend(["--description", str(opts["description"])])
    return CommandResponse(run_gh_text(args), "text")


def issues_labels_delete_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    opts = parse_options(spec.command_path, tail, {"--name": value("name"), "--repo": value("repo"), "--allow-non-project": flag("allow_non_project")})
    if not opts["name"]:
        raise GhopsError("Missing required --name.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
    repo = resolve_repo(opts["repo"], bool(opts["allow_non_project"]), command_path=spec.command_path)
    return CommandResponse(run_gh_text(["label", "delete", str(opts["name"]), "--repo", repo, "--yes"]), "text")


def issues_milestones_list_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    opts = parse_options(spec.command_path, tail, {"--repo": value("repo"), "--state": value("state", default="open"), "--limit": value("limit", default="20"), "--allow-non-project": flag("allow_non_project")})
    state = require_allowed_value("state", opts["state"], ["open", "closed", "all"], command_path=spec.command_path)
    limit = require_positive_int("limit", opts["limit"], command_path=spec.command_path)
    repo = resolve_repo(opts["repo"], bool(opts["allow_non_project"]), command_path=spec.command_path)
    items = gh_api_paginated_list(f"repos/{repo}/milestones", command_path=spec.command_path, fields={} if state == "all" else {"state": state})
    normalized = [{
        "number": item.get("number"),
        "title": item.get("title"),
        "state": item.get("state"),
        "description": item.get("description"),
        "dueOn": item.get("due_on"),
        "closedAt": item.get("closed_at"),
    } for item in items[:limit]]
    if json_mode:
        return json_response(normalized)
    text = "\n".join(json.dumps(item, separators=(",", ":")) for item in normalized)
    return text_response(text + ("\n" if text else ""))


ALIASES = {
    "docs": ["docs", "documentation", "doc", "readme"],
    "documentation": ["documentation", "docs", "doc", "reference"],
    "bug": ["bug", "error", "defect", "regression"],
    "enhancement": ["enhancement", "feature", "improve", "improvement"],
    "tests": ["test", "tests", "ci", "coverage", "pytest", "unittest", "unit"],
    "test": ["test", "tests", "ci", "coverage", "unit"],
    "build": ["build", "builds", "make", "package", "compile"],
    "ci": ["ci", "pipeline", "workflow", "build"],
    "chore": ["chore", "maintenance", "housekeeping", "cleanup"],
}

REUSABLE_FALLBACK_LABELS = {
    "bug": ["bug", "bugs", "error", "crash", "fault", "issue", "fail", "failure"],
    "enhancement": ["enhancement", "enhance", "feature", "improve", "improvement"],
    "documentation": ["documentation", "docs", "readme", "typo", "doc", "docstring"],
    "tests": ["test", "tests", "pytest", "unittest", "coverage", "ci", "unit"],
    "build": ["build", "builds", "pipeline", "compile", "package", "make"],
    "dependencies": ["dependency", "dependencies", "upgrade", "version", "package", "npm", "pip"],
    "chore": ["chore", "cleanup", "housekeeping", "maintenance"],
}

FALLBACK_LABEL_COLORS = {
    "bug": "d73a4a",
    "enhancement": "a2eeef",
    "documentation": "0075ca",
    "tests": "fbca04",
    "build": "0052cc",
    "dependencies": "5319e7",
    "chore": "bfd4f2",
}


def label_tokens(text: str) -> list[str]:
    return TOKEN_RE.findall((text or "").lower())


def overlap_ratio(base: list[str], other: list[str]) -> float:
    base_set = set(base)
    if not base_set:
        return 0.0
    other_set = set(other)
    return len(base_set & other_set) / len(base_set)


def exact_name_match(label_name: str, source_tokens: list[str], match_weight: float) -> tuple[float, bool]:
    label_parts = label_tokens(label_name)
    if not label_parts:
        return 0.0, False
    if " ".join(label_parts) in " ".join(source_tokens):
        return match_weight, True
    return 0.0, False


def issues_suggest_labels_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    opts = parse_options(spec.command_path, tail, {
        "--repo": value("repo"),
        "--title": value("title"),
        "--body": value("body", default=""),
        "--max-suggestions": value("max_suggestions", default="5"),
        "--min-score": value("min_score", default="0.2"),
        "--allow-new-label": flag("allow_new_label"),
        "--new-label-color": value("new_label_color"),
        "--new-label-description": value("new_label_description", default=""),
    })
    repo = validate_repo_reference(str(opts["repo"] or ""))
    if not opts["title"]:
        raise GhopsError("Missing required --title.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
    max_suggestions = require_positive_int("max-suggestions", opts["max_suggestions"], command_path=spec.command_path)
    try:
        min_score = float(str(opts["min_score"]))
    except ValueError as exc:
        raise GhopsError("Invalid --min-score. Use 0..1.", code="invalid_arguments", exit_code=64, command_path=spec.command_path) from exc
    if not (0.0 <= min_score <= 1.0):
        raise GhopsError("Invalid --min-score. Use 0..1.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
    if opts["new_label_color"]:
        normalize_hex_color(str(opts["new_label_color"]), command_path=spec.command_path)
    labels = gh_json(["label", "list", "--repo", repo, "--json", "name,description"], command_path=spec.command_path)
    if not isinstance(labels, list):
        raise GhopsError("Unexpected labels JSON shape.", code="command_failed", command_path=spec.command_path)
    source_tokens = label_tokens(f"{opts['title']} {opts['body']}")
    scored: list[dict[str, Any]] = []
    for label in labels:
        if not isinstance(label, dict):
            continue
        name = str(label.get("name") or "")
        description = str(label.get("description") or "")
        score = 0.0
        direct_score, direct_hit = exact_name_match(name, source_tokens, 0.65)
        score += direct_score
        label_words = label_tokens(name) + label_tokens(description)
        score += overlap_ratio(label_words, source_tokens) * 0.45
        for part in label_tokens(name):
            for alias in ALIASES.get(part, []):
                if alias in source_tokens:
                    score += 0.15
        if direct_hit:
            score += 0.1
        score = min(score, 1.0)
        if score >= min_score:
            scored.append({"name": name, "description": description, "score": round(score, 3), "source": "existing"})
    scored.sort(key=lambda item: (-float(item["score"]), str(item["name"])))
    suggestions = scored[:max_suggestions]
    if not suggestions and opts["allow_new_label"]:
        for fallback_name, keywords in REUSABLE_FALLBACK_LABELS.items():
            if any(keyword in source_tokens for keyword in keywords):
                suggestions.append({
                    "name": fallback_name,
                    "description": str(opts["new_label_description"] or ""),
                    "score": 0.5,
                    "source": "fallback",
                    "color": str(opts["new_label_color"] or FALLBACK_LABEL_COLORS.get(fallback_name, "bfd4f2")),
                })
                break
    payload = {"repository": repo, "title": str(opts["title"]), "suggestions": suggestions}
    if json_mode:
        return json_response(payload)
    lines = [f"Repository: {repo}", f"Title: {opts['title']}", "Suggestions:"]
    if not suggestions:
        lines.append("- none")
    for item in suggestions:
        lines.append(f"- {item['name']} score={item['score']} source={item['source']}")
    return text_response("\n".join(lines) + "\n")


def prs_list_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    opts = parse_options(spec.command_path, tail, {
        "--state": value("state", default="open"),
        "--author": value("author"),
        "--label": value("label"),
        "--base": value("base"),
        "--head": value("head"),
        "--search": value("search"),
        "--limit": value("limit", default="20"),
        "--repo": value("repo"),
        "--allow-non-project": flag("allow_non_project"),
    })
    state = require_allowed_value("state", opts["state"], ["open", "closed", "merged", "all"], command_path=spec.command_path)
    limit = require_positive_int("limit", opts["limit"], command_path=spec.command_path)
    repo = resolve_repo(opts["repo"], bool(opts["allow_non_project"]), command_path=spec.command_path)
    args = ["pr", "list", "--repo", repo, "--state", state, "--limit", str(limit), "--json", "number,title,state,author,baseRefName,headRefName,isDraft,mergeStateStatus,createdAt,updatedAt,url"]
    for flag_name, key in (("--author", "author"), ("--label", "label"), ("--base", "base"), ("--head", "head"), ("--search", "search")):
        if opts[key]:
            args.extend([flag_name, str(opts[key])])
    payload = gh_json(args, command_path=spec.command_path)
    return json_response(payload) if json_mode else text_response(json.dumps(payload, indent=2) + "\n")


def prs_view_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    opts = parse_options(spec.command_path, tail, {"--pr": value("pr"), "--repo": value("repo"), "--allow-non-project": flag("allow_non_project")})
    pr = require_positive_int("pr", opts["pr"], command_path=spec.command_path)
    repo = resolve_repo(opts["repo"], bool(opts["allow_non_project"]), command_path=spec.command_path)
    payload = gh_json(["pr", "view", str(pr), "--repo", repo, "--json", "number,title,state,body,author,baseRefName,headRefName,maintainerCanModify,assignees,labels,reviewDecision,isDraft,closedAt,createdAt,updatedAt,url"], command_path=spec.command_path)
    if json_mode:
        return json_response(payload)
    if not isinstance(payload, dict):
        raise GhopsError("Unexpected pull request view response shape.", code="command_failed", command_path=spec.command_path)
    author = ((payload.get("author") or {}).get("login") or "unknown")
    text = "\n".join([
        f"Pull request: {repo}#{payload.get('number')} {payload.get('title', '')}",
        f"State: {payload.get('state', '')}",
        f"Draft: {'yes' if payload.get('isDraft') else 'no'}",
        f"Review decision: {payload.get('reviewDecision') or 'none'}",
        f"Author: {author}",
        f"Base/head: {payload.get('baseRefName', '')} <- {payload.get('headRefName', '')}",
        f"Labels: {summary_names(payload.get('labels'), 'name')}",
        f"Assignees: {summary_names(payload.get('assignees'), 'login')}",
        f"Updated: {payload.get('updatedAt', '')}",
        f"URL: {payload.get('url', '')}",
        f"Body: {snippet(payload.get('body') or '') or '(empty)'}",
    ]) + "\n"
    return text_response(text)


def prs_patch_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    opts = parse_options(spec.command_path, tail, {"--pr": value("pr"), "--repo": value("repo"), "--path": value("path_filter"), "--include-patch": flag("include_patch"), "--allow-non-project": flag("allow_non_project")})
    pr = require_positive_int("pr", opts["pr"], command_path=spec.command_path)
    repo = resolve_repo(opts["repo"], bool(opts["allow_non_project"]), command_path=spec.command_path)
    items = gh_api_paginated_list(f"repos/{repo}/pulls/{pr}/files", command_path=spec.command_path, headers=["Accept: application/vnd.github+json"])
    normalized: list[dict[str, Any]] = []
    for item in items:
        filename = str(item.get("filename") or "")
        if opts["path_filter"] and filename != opts["path_filter"]:
            continue
        entry = {
            "path": filename,
            "status": item.get("status") or "",
            "additions": int(item.get("additions") or 0),
            "deletions": int(item.get("deletions") or 0),
            "changes": int(item.get("changes") or 0),
            "blob_url": item.get("blob_url") or "",
        }
        if opts["include_patch"]:
            entry["patch"] = item.get("patch") or ""
        normalized.append(entry)
    if opts["path_filter"] and not normalized:
        raise GhopsError(f"No changed file matched path '{opts['path_filter']}' in {repo}#{pr}.", code="command_failed", exit_code=1, command_path=spec.command_path)
    if json_mode:
        return json_response(normalized)
    lines = [f"Pull request files: {repo}#{pr}", f"Files returned: {len(normalized)}"]
    for item in normalized:
        lines.append(f"- {item['path']} [{item['status']}] +{item['additions']} -{item['deletions']} ({item['changes']})")
        lines.append(f"  URL: {item['blob_url'] or '(none)'}")
        if opts["include_patch"]:
            lines.append("  Patch:")
            patch = str(item.get("patch") or "")
            if patch:
                lines.extend([f"    {line}" for line in patch.splitlines()])
            else:
                lines.append("    (no patch available)")
    return text_response("\n".join(lines) + "\n")


def prs_update_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    opts = parse_options(spec.command_path, tail, {
        "--pr": value("pr"),
        "--title": value("title"),
        "--body": value("body"),
        "--base": value("base"),
        "--milestone": value("milestone"),
        "--remove-milestone": flag("remove_milestone"),
        "--add-labels": value("add_labels"),
        "--remove-labels": value("remove_labels"),
        "--add-assignees": value("add_assignees"),
        "--remove-assignees": value("remove_assignees"),
        "--add-reviewers": value("add_reviewers"),
        "--remove-reviewers": value("remove_reviewers"),
        "--repo": value("repo"),
        "--allow-non-project": flag("allow_non_project"),
    })
    pr = require_positive_int("pr", opts["pr"], command_path=spec.command_path)
    if not any(opts[key] for key in ("title", "body", "base", "milestone", "remove_milestone", "add_labels", "remove_labels", "add_assignees", "remove_assignees", "add_reviewers", "remove_reviewers")):
        raise GhopsError(
            "At least one update field is required: --title, --body, --base, --milestone, --remove-milestone, --add-labels, --remove-labels, --add-assignees, --remove-assignees, --add-reviewers, or --remove-reviewers.",
            code="invalid_arguments",
            exit_code=64,
            command_path=spec.command_path,
        )
    if opts["milestone"] and opts["remove_milestone"]:
        raise GhopsError("Use either --milestone or --remove-milestone, not both.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
    repo = resolve_repo(opts["repo"], bool(opts["allow_non_project"]), command_path=spec.command_path)
    args = ["pr", "edit", str(pr), "--repo", repo]
    for key, flag_name in (
        ("title", "--title"),
        ("body", "--body"),
        ("base", "--base"),
        ("milestone", "--milestone"),
        ("add_labels", "--add-label"),
        ("remove_labels", "--remove-label"),
        ("add_assignees", "--add-assignee"),
        ("remove_assignees", "--remove-assignee"),
        ("add_reviewers", "--add-reviewer"),
        ("remove_reviewers", "--remove-reviewer"),
    ):
        if opts[key]:
            args.extend([flag_name, str(opts[key])])
    if opts["remove_milestone"]:
        args.append("--remove-milestone")
    edit_result = run_gh_text(args)
    only_simple_fields = bool(opts["title"] or opts["body"] or opts["base"]) and not any(opts[key] for key in ("milestone", "remove_milestone", "add_labels", "remove_labels", "add_assignees", "remove_assignees", "add_reviewers", "remove_reviewers"))
    if edit_result.returncode != 0 and only_simple_fields and "missing required scopes [read:project]" in (edit_result.stderr or edit_result.stdout):
        api_args = ["api", "-X", "PATCH", f"repos/{repo}/pulls/{pr}"]
        if opts["title"]:
            api_args.extend(["-f", f"title={opts['title']}"])
        if opts["body"]:
            api_args.extend(["-f", f"body={opts['body']}"])
        if opts["base"]:
            api_args.extend(["-f", f"base={opts['base']}"])
        api_result = run_gh_text(api_args)
        if api_result.returncode == 0:
            summary = run_gh_text(["pr", "view", str(pr), "--repo", repo, "--json", "number,title,baseRefName,url", "-q", r"#\(.number) \(.title) [base: \(.baseRefName)]\n\(.url)"])
            stderr = "gh pr edit required read:project; retried with gh api for title/body/base.\n"
            if summary.returncode == 0:
                return text_response(summary.stdout, stderr=stderr)
            return text_response(api_result.stdout, stderr=stderr)
        return CommandResponse(api_result, "text")
    return CommandResponse(edit_result, "text")


def reviews_comment_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    opts = parse_options(spec.command_path, tail, {"--pr": value("pr"), "--body": value("body"), "--repo": value("repo"), "--allow-non-project": flag("allow_non_project")})
    pr = require_positive_int("pr", opts["pr"], command_path=spec.command_path)
    if not opts["body"]:
        raise GhopsError("Missing required --body.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
    repo = resolve_repo(opts["repo"], bool(opts["allow_non_project"]), command_path=spec.command_path)
    return CommandResponse(run_gh_text(["pr", "comment", str(pr), "--repo", repo, "--body", str(opts["body"])]), "text")


def reviews_comments_list_handler(endpoint_builder: Callable[[str, int], str]) -> CommandHandler:
    def handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
        opts = parse_options(spec.command_path, tail, {"--pr": value("pr"), "--repo": value("repo"), "--allow-non-project": flag("allow_non_project")})
        pr = require_positive_int("pr", opts["pr"], command_path=spec.command_path)
        repo = resolve_repo(opts["repo"], bool(opts["allow_non_project"]), command_path=spec.command_path)
        payload = gh_api_paginated_list(endpoint_builder(repo, pr), command_path=spec.command_path)
        return json_response(payload) if json_mode else text_response(json.dumps(payload, indent=2) + "\n")
    return handler


def reviews_review_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    opts = parse_options(spec.command_path, tail, {"--pr": value("pr"), "--approve": flag("approve"), "--request-changes": flag("request_changes"), "--comment": flag("comment"), "--body": value("body"), "--repo": value("repo"), "--allow-non-project": flag("allow_non_project")})
    pr = require_positive_int("pr", opts["pr"], command_path=spec.command_path)
    actions = [name for name in ("approve", "request_changes", "comment") if opts[name]]
    if len(actions) != 1:
        raise GhopsError("Choose exactly one review action: --approve, --request-changes, or --comment.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
    repo = resolve_repo(opts["repo"], bool(opts["allow_non_project"]), command_path=spec.command_path)
    args = ["pr", "review", str(pr), "--repo", repo]
    if actions[0] == "approve":
        args.append("--approve")
    elif actions[0] == "request_changes":
        args.append("--request-changes")
    else:
        args.append("--comment")
    if opts["body"]:
        args.extend(["--body", str(opts["body"])])
    return CommandResponse(run_gh_text(args), "text")


def reviews_address_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    opts = parse_options(spec.command_path, tail, {
        "--pr": value("pr"),
        "--repo": value("repo"),
        "--include-resolved": flag("include_resolved"),
        "--selection": value("selection"),
        "--comment-ids": value("comment_ids"),
        "--reply-body": value("reply_body"),
        "--dry-run": flag("dry_run"),
        "--allow-non-project": flag("allow_non_project"),
    })
    pr = require_positive_int("pr", opts["pr"], command_path=spec.command_path)
    repo = resolve_repo(opts["repo"], bool(opts["allow_non_project"]), command_path=spec.command_path)
    reply_mode = bool(opts["reply_body"])
    if reply_mode:
        if opts["selection"] and opts["comment_ids"]:
            raise GhopsError("Use either --selection or --comment-ids with --reply-body, not both.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
        if not opts["selection"] and not opts["comment_ids"]:
            raise GhopsError("--reply-body requires either --selection or --comment-ids.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
    elif opts["selection"] or opts["comment_ids"]:
        raise GhopsError("--selection and --comment-ids require --reply-body.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
    conversation_comments = gh_api_paginated_list(f"repos/{repo}/issues/{pr}/comments", command_path=spec.command_path, headers=["Accept: application/vnd.github+json"])
    review_comments = gh_api_paginated_list(f"repos/{repo}/pulls/{pr}/comments", command_path=spec.command_path, headers=["Accept: application/vnd.github+json"])
    owner, repo_name = repo.split("/", 1)
    query = """
query($owner: String!, $repo: String!, $number: Int!, $after: String) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      reviewThreads(first: 50, after: $after) {
        pageInfo { hasNextPage endCursor }
        nodes {
          isResolved
          isOutdated
          path
          line
          startLine
          comments(first: 100) {
            nodes {
              databaseId
              body
              createdAt
              updatedAt
              author { login }
            }
          }
        }
      }
    }
  }
}
""".strip()
    threads: list[dict[str, Any]] = []
    after: str | None = None
    while True:
        payload = user_state.graphql(query, {"owner": owner, "repo": repo_name, "number": pr, "after": after})
        review_threads = (((payload.get("data") or {}).get("repository") or {}).get("pullRequest") or {}).get("reviewThreads") or {}
        nodes = review_threads.get("nodes") or []
        threads.extend([node for node in nodes if isinstance(node, dict)])
        page_info = review_threads.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        after = page_info.get("endCursor")
        if not after:
            break
    active_thread_entries: list[dict[str, Any]] = []
    other_thread_entries: list[dict[str, Any]] = []
    thread_comment_ids: set[int] = set()
    for thread in threads:
        resolved = bool(thread.get("isResolved"))
        outdated = bool(thread.get("isOutdated"))
        is_active = (not resolved) and (not outdated)
        if not opts["include_resolved"] and not is_active:
            continue
        bucket = active_thread_entries if is_active else other_thread_entries
        for comment in ((thread.get("comments") or {}).get("nodes") or []):
            if not isinstance(comment, dict) or not comment.get("databaseId"):
                continue
            comment_id = int(comment["databaseId"])
            thread_comment_ids.add(comment_id)
            bucket.append({
                "type": "review_thread_comment",
                "comment_id": comment_id,
                "author": ((comment.get("author") or {}).get("login") or ""),
                "updated": comment.get("updatedAt") or comment.get("createdAt") or "",
                "body": comment.get("body") or "",
                "body_preview": snippet(comment.get("body") or ""),
                "path": thread.get("path") or "",
                "line": thread.get("line"),
                "start_line": thread.get("startLine"),
                "is_resolved": resolved,
                "is_outdated": outdated,
            })
    orphan_review_entries: list[dict[str, Any]] = []
    for comment in review_comments:
        if not comment.get("id"):
            continue
        comment_id = int(comment["id"])
        if comment_id in thread_comment_ids:
            continue
        orphan_review_entries.append({
            "type": "review_comment",
            "comment_id": comment_id,
            "author": ((comment.get("user") or {}).get("login") or ""),
            "updated": comment.get("updated_at") or comment.get("created_at") or "",
            "body": comment.get("body") or "",
            "body_preview": snippet(comment.get("body") or ""),
            "path": comment.get("path") or "",
            "line": comment.get("line"),
            "start_line": comment.get("start_line"),
            "is_resolved": None,
            "is_outdated": None,
        })
    conversation_entries = [{
        "type": "conversation_comment",
        "comment_id": int(comment["id"]),
        "author": ((comment.get("user") or {}).get("login") or ""),
        "updated": comment.get("updated_at") or comment.get("created_at") or "",
        "body": comment.get("body") or "",
        "body_preview": snippet(comment.get("body") or ""),
        "path": "",
        "line": None,
        "start_line": None,
        "is_resolved": None,
        "is_outdated": None,
    } for comment in conversation_comments if isinstance(comment, dict) and comment.get("id")]
    entries = active_thread_entries + other_thread_entries + orphan_review_entries + conversation_entries
    for index, item in enumerate(entries, start=1):
        item["index"] = index
    actions: list[dict[str, Any]] = []
    if reply_mode:
        selected_entries: list[dict[str, Any]] = []
        entries_by_index = {str(item["index"]): item for item in entries}
        entries_by_comment_id = {str(item["comment_id"]): item for item in entries}
        raw_parts = str(opts["selection"] or opts["comment_ids"] or "").replace(",", " ").split()
        if opts["selection"]:
            for part in raw_parts:
                if part not in entries_by_index:
                    raise GhopsError(f"Selection index '{part}' was not found.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
                selected_entries.append(entries_by_index[part])
        else:
            for part in raw_parts:
                if part not in entries_by_comment_id:
                    raise GhopsError(f"Comment ID '{part}' was not found in the fetched context.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
                selected_entries.append(entries_by_comment_id[part])
        for item in selected_entries:
            action: dict[str, Any] = {"comment_id": item["comment_id"], "type": item["type"], "status": "dry-run" if opts["dry_run"] else "pending"}
            if item["type"] == "conversation_comment":
                command = ["pr", "comment", str(pr), "--repo", repo, "--body", f"{opts['reply_body']} (ref: {item['comment_id']})"]
                action["transport"] = "gh pr comment"
                if not opts["dry_run"]:
                    posted = run_gh_text(command)
                    if posted.returncode != 0:
                        return CommandResponse(posted, "text")
                    action["status"] = "posted"
            else:
                endpoint = f"repos/{repo}/pulls/comments/{item['comment_id']}/replies"
                action["transport"] = "gh api"
                action["endpoint"] = endpoint
                action["body"] = opts["reply_body"]
                if not opts["dry_run"]:
                    posted = run_gh_text(["api", "-X", "POST", endpoint, "-H", "Accept: application/vnd.github+json", "-f", f"body={opts['reply_body']}"])
                    if posted.returncode == 0:
                        action["status"] = "replied"
                    else:
                        fallback = run_gh_text(["pr", "comment", str(pr), "--repo", repo, "--body", f"{opts['reply_body']} (ref: {item['comment_id']})"])
                        if fallback.returncode != 0:
                            return CommandResponse(fallback, "text")
                        action["status"] = "fallback-pr-comment"
            actions.append(action)
    payload: dict[str, Any] = {"entries": entries}
    if reply_mode:
        payload["actions"] = actions
    if json_mode:
        return json_response(payload)
    if entries:
        lines: list[str] = []
        for item in entries:
            lines.append(f"[{item['index']:>3}] {item['type']} id={item['comment_id']} author={item['author'] or 'unknown'} updated={item['updated']}")
            lines.append(f"      {item['body_preview'] or '(empty)'}")
            if item["path"]:
                lines.append(f"      file={item['path']} line={item['line']} startLine={item['start_line']} resolved={item['is_resolved']} outdated={item['is_outdated']}")
    else:
        lines = [f"No comment context found for {repo}#{pr}."]
    if reply_mode:
        lines.extend(["", "Reply actions:"])
        for action in actions:
            lines.append(f"- comment {action['comment_id']} via {action['transport']}: {action['status']}")
    return text_response("\n".join(lines) + "\n")


def checks_pr_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    argv = list(tail)
    if json_mode and "--json" not in argv:
        argv.extend(["--json"])
    return CommandResponse(helper_result(checks_lib.main, argv), "json" if json_mode else "text")


def actions_list_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    opts = parse_options(spec.command_path, tail, {
        "--repo": value("repo"),
        "--branch": value("branch"),
        "--commit": value("commit"),
        "--workflow": value("workflow"),
        "--event": value("event"),
        "--status": value("status"),
        "--limit": value("limit", default="10"),
        "--all": flag("all"),
        "--allow-non-project": flag("allow_non_project"),
    })
    limit = require_positive_int("limit", opts["limit"], command_path=spec.command_path)
    repo = resolve_repo(opts["repo"], bool(opts["allow_non_project"]), command_path=spec.command_path)
    args = ["run", "list", "--repo", repo, "-L", str(limit), "--json", "databaseId,workflowName,status,conclusion,headBranch,headSha,displayTitle,event,url"]
    if opts["all"]:
        args.append("--all")
    for key, flag_name in (("branch", "--branch"), ("commit", "--commit"), ("workflow", "--workflow"), ("event", "--event"), ("status", "--status")):
        if opts[key]:
            args.extend([flag_name, str(opts[key])])
    payload = gh_json(args, command_path=spec.command_path)
    return json_response(payload) if json_mode else text_response(json.dumps(payload, indent=2) + "\n")


def actions_inspect_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    if json_mode:
        maybe_allows_json_inspect(tail)
    opts = parse_options(spec.command_path, tail, {
        "--repo": value("repo"),
        "--run-id": value("run_id"),
        "--job-id": value("job_id"),
        "--artifact-name": value("artifact_name"),
        "--download-dir": value("download_dir", default="."),
        "--summary-only": flag("summary_only"),
        "--allow-non-project": flag("allow_non_project"),
    })
    repo = resolve_repo(opts["repo"], bool(opts["allow_non_project"]), command_path=spec.command_path)
    run_id = int(opts["run_id"]) if opts["run_id"] else None
    job_id = int(opts["job_id"]) if opts["job_id"] else None
    if opts["artifact_name"] and not run_id:
        raise GhopsError("--artifact-name requires --run-id.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
    if not run_id and not job_id:
        raise GhopsError("actions inspect requires --run-id or --job-id.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
    if job_id and not run_id:
        result = run_gh_text(["run", "view", "--repo", repo, "--job", str(job_id), "--log"])
        return CommandResponse(result, "text")
    summary = gh_json(["run", "view", str(run_id), "--repo", repo, "--json", "databaseId,workflowName,status,conclusion,headBranch,headSha,displayTitle,url,event,createdAt,updatedAt"], command_path=spec.command_path)
    if json_mode:
        return json_response(summary)
    parts = [json.dumps(summary, indent=2)]
    if not opts["summary_only"]:
        failed_logs = run_gh_text(["run", "view", str(run_id), "--repo", repo, "--log-failed"])
        if failed_logs.returncode == 0:
            parts.extend(["", failed_logs.stdout.rstrip()])
        else:
            parts.extend(["", failed_logs.stderr.strip() or failed_logs.stdout.strip()])
        if job_id:
            job_logs = run_gh_text(["run", "view", "--repo", repo, "--job", str(job_id), "--log"])
            if job_logs.returncode != 0:
                return CommandResponse(job_logs, "text")
            parts.extend(["", job_logs.stdout.rstrip()])
        if opts["artifact_name"]:
            download_dir = Path(str(opts["download_dir"]))
            download_dir.mkdir(parents=True, exist_ok=True)
            artifact = run_gh_text(["run", "download", str(run_id), "--repo", repo, "-n", str(opts["artifact_name"]), "-D", str(download_dir)])
            if artifact.returncode != 0:
                return CommandResponse(artifact, "text")
            parts.extend(["", artifact.stdout.rstrip()])
    return text_response("\n".join(part for part in parts if part) + "\n")


def helper_based_handler(main_func: Callable[[list[str] | None], int], *, ensure_json_flag: bool = False) -> CommandHandler:
    def handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
        argv = list(tail)
        if ensure_json_flag and json_mode and "--json" not in argv:
            argv.append("--json")
        return CommandResponse(helper_result(main_func, argv), "json" if json_mode else "text")
    return handler


def reactions_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    opts = parse_options(spec.command_path, tail, {
        "--resource": value("resource"),
        "--repo": value("repo"),
        "--number": value("number"),
        "--comment-id": value("comment_id"),
        "--dry-run": flag("dry_run"),
        "--allow-non-project": flag("allow_non_project"),
    })
    action_path = spec.command_path[-1]
    repo = resolve_repo(opts["repo"], bool(opts["allow_non_project"]), command_path=spec.command_path)
    resource = require_allowed_value("resource", opts["resource"], ["pr", "issue", "issue-comment", "pr-review-comment"], command_path=spec.command_path)
    if action_path == "list":
        if resource in {"pr", "issue"}:
            number = require_positive_int("number", opts["number"], command_path=spec.command_path)
            base_endpoint = f"repos/{repo}/issues/{number}/reactions"
            target_label = f"{resource} {repo}#{number}"
        else:
            comment_id = require_positive_int("comment-id", opts["comment_id"], command_path=spec.command_path)
            base_endpoint = f"repos/{repo}/issues/comments/{comment_id}/reactions" if resource == "issue-comment" else f"repos/{repo}/pulls/comments/{comment_id}/reactions"
            target_label = f"{resource} {repo} comment {comment_id}"
        items = gh_api_paginated_list(base_endpoint, command_path=spec.command_path, headers=["Accept: application/vnd.github+json"])
        payload = [{"id": item.get("id"), "content": item.get("content") or "", "user": ((item.get("user") or {}).get("login") or "")} for item in items]
        if json_mode:
            return json_response(payload)
        lines = [f"Reactions: {target_label}", f"Count: {len(payload)}"]
        lines.extend([f"- id={item['id']} {item['content']} by {item['user'] or 'unknown'}" for item in payload])
        return text_response("\n".join(lines) + "\n")

    value_token = tail[0] if tail and not tail[0].startswith("--") else None
    remaining_tail = tail[1:] if value_token is not None else tail
    if value_token is None:
        label = "reaction" if action_path == "add" else "reaction-id"
        raise GhopsError(f"{' '.join(spec.command_path)} requires a {label} positional argument.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
    opts = parse_options(spec.command_path, remaining_tail, {
        "--resource": value("resource"),
        "--repo": value("repo"),
        "--number": value("number"),
        "--comment-id": value("comment_id"),
        "--dry-run": flag("dry_run"),
        "--allow-non-project": flag("allow_non_project"),
    })
    repo = resolve_repo(opts["repo"], bool(opts["allow_non_project"]), command_path=spec.command_path)
    resource = require_allowed_value("resource", opts["resource"], ["pr", "issue", "issue-comment", "pr-review-comment"], command_path=spec.command_path)
    if resource in {"pr", "issue"}:
        number = require_positive_int("number", opts["number"], command_path=spec.command_path)
        base_endpoint = f"repos/{repo}/issues/{number}/reactions"
        target_label = f"{resource} {repo}#{number}"
    else:
        comment_id = require_positive_int("comment-id", opts["comment_id"], command_path=spec.command_path)
        base_endpoint = f"repos/{repo}/issues/comments/{comment_id}/reactions" if resource == "issue-comment" else f"repos/{repo}/pulls/comments/{comment_id}/reactions"
        target_label = f"{resource} {repo} comment {comment_id}"
    if action_path == "add":
        require_allowed_value("add", value_token, ["+1", "-1", "laugh", "confused", "heart", "hooray", "rocket", "eyes"], command_path=spec.command_path)
        if opts["dry_run"]:
            payload = {"action": "add", "target": target_label, "content": value_token}
            return json_response(payload) if json_mode else text_response(f"Dry run: would add reaction {value_token} to {target_label}.\n")
        result = run_gh_text(["api", "-X", "POST", base_endpoint, "-H", "Accept: application/vnd.github+json", "-f", f"content={value_token}"])
        if json_mode and result.returncode == 0:
            return CommandResponse(result, "json")
        return CommandResponse(result, "text")
    reaction_id = require_positive_int("remove", value_token, command_path=spec.command_path)
    if opts["dry_run"]:
        payload = {"action": "remove", "target": target_label, "reaction_id": reaction_id}
        return json_response(payload) if json_mode else text_response(f"Dry run: would remove reaction {reaction_id} from {target_label}.\n")
    result = run_gh_text(["api", "-X", "DELETE", f"{base_endpoint}/{reaction_id}", "-H", "Accept: application/vnd.github+json"])
    if json_mode:
        payload = {"action": "remove", "target": target_label, "reaction_id": reaction_id, "stdout": result.stdout.strip()}
        return json_response(payload) if result.returncode == 0 else CommandResponse(result, "text")
    return text_response(f"Removed reaction {reaction_id} from {target_label}.\n") if result.returncode == 0 else CommandResponse(result, "text")


def release_plan_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    opts = parse_options(spec.command_path, tail, {"--repo": value("repo"), "--target-branch": value("target_branch"), "--allow-non-project": flag("allow_non_project")})
    repo = resolve_repo(opts["repo"], bool(opts["allow_non_project"]), command_path=spec.command_path)
    default_branch = str(gh_json(["repo", "view", repo, "--json", "defaultBranchRef"], command_path=spec.command_path).get("defaultBranchRef", {}).get("name") or "")
    target_branch = str(opts["target_branch"] or default_branch)
    commit_payload = gh_json(["api", f"repos/{repo}/commits/{target_branch}"], command_path=spec.command_path)
    previous = gh_json(["release", "list", "--repo", repo, "--exclude-drafts", "--exclude-pre-releases", "--json", "tagName", "--limit", "1"], command_path=spec.command_path)
    previous_tag = previous[0]["tagName"] if isinstance(previous, list) and previous else None
    payload = {
        "repository": repo,
        "default_branch": default_branch,
        "target_branch": target_branch,
        "target_commit": f"{str(commit_payload.get('sha') or '')[:7]} {str(((commit_payload.get('commit') or {}).get('message') or '').splitlines()[0])}".strip(),
        "previous_tag": previous_tag,
    }
    if json_mode:
        return json_response(payload)
    lines = [
        f"Repository:      {repo}",
        f"Default branch:  {default_branch}",
        f"Target branch:   {target_branch}",
        f"Target commit:   {payload['target_commit']}",
        f"Previous tag:    {previous_tag or '<none found>'}",
    ]
    return text_response("\n".join(lines) + "\n")


def release_notes_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    opts = parse_options(spec.command_path, tail, {
        "--tag": value("tag"),
        "--target-ref": value("target_ref"),
        "--repo": value("repo"),
        "--previous-tag": value("previous_tag"),
        "--workdir": value("workdir"),
        "--title-file": value("title_file"),
        "--notes-file": value("notes_file"),
        "--allow-non-project": flag("allow_non_project"),
    })
    if not opts["tag"] or not opts["target_ref"]:
        raise GhopsError("Missing required arguments: --tag and --target-ref are required.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
    repo = resolve_repo(opts["repo"], bool(opts["allow_non_project"]), command_path=spec.command_path)
    previous_tag = str(opts["previous_tag"] or "")
    if not previous_tag:
        release_list = gh_json(["release", "list", "--repo", repo, "--exclude-drafts", "--exclude-pre-releases", "--json", "tagName", "--limit", "1"], command_path=spec.command_path)
        previous_tag = str(release_list[0]["tagName"]) if isinstance(release_list, list) and release_list else ""
    workdir = Path(str(opts["workdir"])) if opts["workdir"] else Path(tempfile.mkdtemp(prefix="gh-release-notes-"))
    workdir.mkdir(parents=True, exist_ok=True)
    title_file = Path(str(opts["title_file"])) if opts["title_file"] else workdir / "release_title.txt"
    notes_file = Path(str(opts["notes_file"])) if opts["notes_file"] else workdir / "release_notes.md"
    args = ["api", f"repos/{repo}/releases/generate-notes", "-X", "POST", "-f", f"tag_name={opts['tag']}", "-f", f"target_commitish={opts['target_ref']}"]
    if previous_tag:
        args.extend(["-f", f"previous_tag_name={previous_tag}"])
    payload = gh_json(args, command_path=spec.command_path)
    draft_title = str(payload.get("name") or "")
    draft_body = str(payload.get("body") or "")
    title_file.parent.mkdir(parents=True, exist_ok=True)
    notes_file.parent.mkdir(parents=True, exist_ok=True)
    title_file.write_text(draft_title + ("\n" if draft_title else ""), encoding="utf-8")
    notes_file.write_text(draft_body, encoding="utf-8")
    normalized = {
        "repository": repo,
        "tag": opts["tag"],
        "target_ref": opts["target_ref"],
        "previous_tag": previous_tag or None,
        "title_file": str(title_file),
        "notes_file": str(notes_file),
        "draft_title": draft_title,
        "draft_notes_preview": "\n".join(draft_body.splitlines()[:80]).strip(),
    }
    if json_mode:
        return json_response(normalized)
    lines = [
        f"Repository:   {repo}",
        f"Tag:          {opts['tag']}",
        f"Target ref:   {opts['target_ref']}",
        f"Previous tag: {previous_tag or '<none found>'}",
        f"Title file:   {title_file}",
        f"Notes file:   {notes_file}",
        "",
        "Draft title:",
        draft_title,
        "",
        "Draft notes preview:",
        "\n".join(draft_body.splitlines()[:80]).rstrip(),
    ]
    return text_response("\n".join(lines) + "\n")


def release_create_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    opts = parse_options(spec.command_path, tail, {
        "--tag": value("tag"),
        "--target-ref": value("target_ref"),
        "--notes-mode": value("notes_mode"),
        "--repo": value("repo"),
        "--title": value("title"),
        "--title-file": value("title_file"),
        "--notes-file": value("notes_file"),
        "--notes-text": value("notes_text"),
        "--previous-tag": value("previous_tag"),
        "--allow-non-project": flag("allow_non_project"),
    })
    if not opts["tag"] or not opts["target_ref"] or not opts["notes_mode"]:
        raise GhopsError("Missing required arguments: --tag, --target-ref, and --notes-mode are required.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
    require_allowed_value("notes-mode", opts["notes_mode"], ["infer", "blank", "user"], command_path=spec.command_path)
    if opts["title"] and opts["title_file"]:
        raise GhopsError("Use either --title or --title-file, not both.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
    repo = resolve_repo(opts["repo"], bool(opts["allow_non_project"]), command_path=spec.command_path)
    args = ["release", "create", str(opts["tag"]), "--repo", repo, "--target", str(opts["target_ref"]), "--fail-on-no-commits"]
    if opts["title"]:
        args.extend(["-t", str(opts["title"])])
    elif opts["title_file"]:
        args.extend(["-t", Path(str(opts["title_file"])).read_text(encoding="utf-8")])
    notes_mode = str(opts["notes_mode"])
    if notes_mode == "infer":
        if opts["notes_file"]:
            args.extend(["-F", str(opts["notes_file"])])
        elif opts["previous_tag"]:
            args.extend(["--generate-notes", "--notes-start-tag", str(opts["previous_tag"])])
        else:
            args.append("--generate-notes")
    elif notes_mode == "blank":
        if opts["notes_file"] or opts["notes_text"]:
            raise GhopsError("--notes-file/--notes-text are not valid with --notes-mode blank.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
        args.extend(["--notes", ""])
    else:
        if opts["notes_file"]:
            args.extend(["-F", str(opts["notes_file"])])
        elif opts["notes_text"]:
            args.extend(["--notes", str(opts["notes_text"])])
        else:
            raise GhopsError("For --notes-mode user, provide either --notes-file or --notes-text.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
    created = run_gh_text(args)
    if created.returncode != 0:
        return CommandResponse(created, "text")
    view_result = run_gh_text(["release", "view", str(opts["tag"]), "--repo", repo, "--json", "url,tagName,targetCommitish,name"])
    return CommandResponse(view_result, "json" if json_mode else "text")


def publish_context_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    opts = parse_options(spec.command_path, tail, {"--repo": value("repo"), "--allow-non-project": flag("allow_non_project")})
    require_git_repo(spec.command_path)
    local_repo = resolve_repo(None, False, command_path=spec.command_path)
    if opts["repo"] and str(opts["repo"]) != local_repo:
        raise GhopsError(f"Cross-repo publish is not supported. Current checkout resolves to {local_repo}.", code="repo_context_mismatch", exit_code=2, command_path=spec.command_path)
    repo = local_repo
    default_branch = str(gh_json(["repo", "view", repo, "--json", "defaultBranchRef"], command_path=spec.command_path).get("defaultBranchRef", {}).get("name") or "")
    head_ref = run_git_text(["rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
    detached = not head_ref or head_ref == "HEAD"
    branch = None if detached else head_ref
    on_default_branch = bool(branch and branch == default_branch)
    current_branch_is_long_lived = bool(branch and branch_is_long_lived(branch))
    upstream_remote = tracking_remote_name(branch) if branch else None
    upstream_branch = tracking_branch_name(branch) if branch else None
    upstream_configured = bool(upstream_remote and upstream_branch)
    same_name_remote = bool(upstream_configured and upstream_branch == branch)
    ahead = behind = 0
    if upstream_configured:
        counts = run_git_text(["rev-list", "--left-right", "--count", "HEAD...@{upstream}"]).stdout.strip()
        if counts:
            parts = counts.split()
            if len(parts) == 2:
                ahead, behind = int(parts[0]), int(parts[1])
    staged = unstaged = untracked = total = 0
    status = run_git_text(["status", "--porcelain=v1"]).stdout.splitlines()
    for line in status:
        total += 1
        if line.startswith("??"):
            untracked += 1
            continue
        if line[:1] != " ":
            staged += 1
        if line[1:2] != " ":
            unstaged += 1
    open_pr: dict[str, Any] = {"exists": False, "number": None, "url": None, "title": None, "base": None, "head": None, "is_draft": None}
    if branch:
        pr_list = gh_json(["pr", "list", "--repo", repo, "--head", branch, "--state", "open", "--json", "number,url,title,baseRefName,headRefName,isDraft", "--limit", "1"], command_path=spec.command_path)
        if isinstance(pr_list, list) and pr_list:
            entry = pr_list[0]
            open_pr = {
                "exists": True,
                "number": entry.get("number"),
                "url": entry.get("url"),
                "title": entry.get("title"),
                "base": entry.get("baseRefName"),
                "head": entry.get("headRefName"),
                "is_draft": entry.get("isDraft"),
            }
    recommended_pr_base = None
    recommended_next_step = "Keep the current branch, push, then open or reuse the draft PR."
    if detached:
        recommended_next_step = "Create a new short-lived branch before staging because the checkout is detached."
    elif on_default_branch:
        recommended_pr_base = default_branch
        recommended_next_step = f"Create a new short-lived branch before staging because the current branch is the default branch, and open the PR against {default_branch}."
    elif current_branch_is_long_lived and branch:
        recommended_pr_base = branch
        recommended_next_step = f"Create a new short-lived branch from {branch} before staging, and open the PR against {branch}."
    elif open_pr["exists"]:
        recommended_next_step = "Keep the current branch, push the next commit, and reuse the existing PR."
    elif not upstream_configured and branch:
        recommended_next_step = f"Keep the current branch, then push with git push -u origin {branch} before opening the PR."
    payload = {
        "repo": repo,
        "default_branch": default_branch,
        "current_branch": branch,
        "detached_head": detached,
        "on_default_branch": on_default_branch,
        "current_branch_is_long_lived": current_branch_is_long_lived,
        "upstream": {
            "configured": upstream_configured,
            "remote": upstream_remote,
            "branch": upstream_branch,
            "same_name_remote": same_name_remote,
            "ahead": ahead,
            "behind": behind,
        },
        "changes": {
            "tracked": total - untracked,
            "staged": staged,
            "unstaged": unstaged,
            "untracked": untracked,
            "total_paths": total,
        },
        "open_pr": open_pr,
        "recommended_pr_base": recommended_pr_base,
        "recommended_next_step": recommended_next_step,
    }
    if json_mode:
        return json_response(payload)
    lines = [
        f"Repo: {repo}",
        f"Default branch: {default_branch}",
        f"Current branch: {branch or '(detached HEAD)'}",
        f"On default branch: {'yes' if on_default_branch else 'no'}",
        f"Current branch is long-lived: {'yes' if current_branch_is_long_lived else 'no'}",
        f"Upstream: {upstream_remote}/{upstream_branch} (ahead {ahead}, behind {behind})" if upstream_configured else "Upstream: (none)",
        f"Same-name remote branch: {'yes' if same_name_remote else 'no'}",
        f"Changes: {total} path(s) total; staged {staged}, unstaged {unstaged}, untracked {untracked}",
        f"Open PR: #{open_pr['number']} {open_pr['title']}" if open_pr["exists"] else "Open PR: none",
    ]
    if open_pr["exists"]:
        lines.append(f"PR URL: {open_pr['url']}")
    if recommended_pr_base:
        lines.append(f"Recommended PR base: {recommended_pr_base}")
    lines.append(f"Recommended next step: {recommended_next_step}")
    return text_response("\n".join(lines) + "\n")


def publish_open_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    opts = parse_options(spec.command_path, tail, {
        "--title": value("title"),
        "--body": value("body"),
        "--body-from-head": flag("body_from_head"),
        "--base": value("base"),
        "--draft": flag("draft"),
        "--repo": value("repo"),
        "--dry-run": flag("dry_run"),
        "--allow-non-project": flag("allow_non_project"),
    })
    branch = current_branch(spec.command_path)
    local_repo = resolve_repo(None, False, command_path=spec.command_path)
    if opts["repo"] and str(opts["repo"]) != local_repo:
        raise GhopsError(f"Cross-repo PR creation is not supported by publish open. Current checkout resolves to {local_repo}.", code="repo_context_mismatch", exit_code=2, command_path=spec.command_path)
    repo = local_repo
    remote_name = tracking_remote_name(branch)
    remote_branch = tracking_branch_name(branch)
    if not remote_name or not remote_branch:
        raise GhopsError(f"Current branch '{branch}' has no configured upstream. Push it before opening a PR.", code="repo_context_missing", exit_code=5, command_path=spec.command_path)
    if remote_branch != branch:
        raise GhopsError(f"Current branch '{branch}' tracks '{remote_name}/{remote_branch}'. This helper only supports same-name remote branches.", code="repo_context_mismatch", exit_code=5, command_path=spec.command_path)
    if run_git_text(["ls-remote", "--exit-code", "--heads", remote_name, branch]).returncode != 0:
        raise GhopsError(f"Current branch '{branch}' is not available on remote '{remote_name}'. Push it before opening a PR.", code="repo_context_missing", exit_code=5, command_path=spec.command_path)
    existing = gh_json(["pr", "list", "--repo", repo, "--head", branch, "--state", "open", "--json", "number,url,title,baseRefName,headRefName,isDraft", "--limit", "1"], command_path=spec.command_path)
    if isinstance(existing, list) and existing:
        pr_info = existing[0]
        if opts["base"] and pr_info.get("baseRefName") != opts["base"]:
            raise GhopsError(
                f"Existing PR #{pr_info.get('number')} targets '{pr_info.get('baseRefName')}', not requested base '{opts['base']}'.",
                code="repo_context_mismatch",
                exit_code=7,
                command_path=spec.command_path,
            )
        if opts["dry_run"]:
            lines = [
                f"Dry run: would reuse existing PR for {branch} in {repo}.",
                f"PR: #{pr_info.get('number')} {pr_info.get('title')}",
                f"URL: {pr_info.get('url')}",
                "Create arguments are ignored because the PR already exists.",
                "",
            ]
            return text_response("\n".join(lines))
        return text_response(f"Reusing existing PR #{pr_info.get('number')}: {pr_info.get('url')}\n")
    base = str(opts["base"] or gh_json(["repo", "view", repo, "--json", "defaultBranchRef"], command_path=spec.command_path).get("defaultBranchRef", {}).get("name") or "")
    title = str(opts["title"] or run_git_text(["log", "-1", "--format=%s"]).stdout.strip())
    if not title:
        raise GhopsError("Could not derive a PR title from HEAD. Pass --title explicitly.", code="invalid_arguments", exit_code=6, command_path=spec.command_path)
    body = str(opts["body"] or "")
    if opts["body_from_head"] and not body:
        body = run_git_text(["log", "-1", "--format=%b"]).stdout
    args = ["pr", "create", "--repo", repo, "--title", title, "--head", branch, "--base", base, "--body", body]
    if opts["draft"]:
        args.append("--draft")
    if opts["dry_run"]:
        lines = [
            f"Dry run: would open a PR for {branch} in {repo}.",
            f"Base: {base}",
            f"Title: {title}",
            "Body source: latest commit body" if body and opts["body_from_head"] else ("Body source: provided" if body else "Body: (empty)"),
        ]
        if body:
            lines.append("Body:")
            lines.append(body.rstrip())
        lines.extend([f"Draft: {'yes' if opts['draft'] else 'no'}", f"Command: {' '.join(args)}", ""])
        return text_response("\n".join(lines))
    return CommandResponse(run_gh_text(args), "text")


def publish_simple_pr_handler(command: list[str], *, extra_flags: dict[str, str] | None = None) -> CommandHandler:
    def handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
        specs = {"--pr": value("pr"), "--repo": value("repo"), "--allow-non-project": flag("allow_non_project")}
        for flag_name in extra_flags or {}:
            specs[flag_name] = flag(extra_flags[flag_name])
        opts = parse_options(spec.command_path, tail, specs)
        pr = require_positive_int("pr", opts["pr"], command_path=spec.command_path)
        repo = resolve_repo(opts["repo"], bool(opts["allow_non_project"]), command_path=spec.command_path)
        args = [*command, str(pr), "--repo", repo]
        for flag_name, dest in (extra_flags or {}).items():
            if opts[dest]:
                args.append(flag_name)
        return CommandResponse(run_gh_text(args), "text")
    return handler


def publish_create_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    opts = parse_options(spec.command_path, tail, {"--title": value("title"), "--body": value("body"), "--base": value("base"), "--head": value("head"), "--draft": flag("draft"), "--labels": value("labels"), "--repo": value("repo"), "--allow-non-project": flag("allow_non_project")})
    if not opts["title"]:
        raise GhopsError("Missing required --title.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
    repo = resolve_repo(opts["repo"], bool(opts["allow_non_project"]), command_path=spec.command_path)
    args = ["pr", "create", "--repo", repo, "--title", str(opts["title"])]
    for key, flag_name in (("body", "--body"), ("base", "--base"), ("head", "--head"), ("labels", "--label")):
        if opts[key]:
            args.extend([flag_name, str(opts[key])])
    if opts["draft"]:
        args.append("--draft")
    return CommandResponse(run_gh_text(args), "text")


def publish_merge_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    opts = parse_options(spec.command_path, tail, {"--pr": value("pr"), "--merge": flag("merge"), "--squash": flag("squash"), "--rebase": flag("rebase"), "--delete-branch": flag("delete_branch"), "--admin": flag("admin"), "--auto": flag("auto"), "--repo": value("repo"), "--allow-non-project": flag("allow_non_project")})
    pr = require_positive_int("pr", opts["pr"], command_path=spec.command_path)
    repo = resolve_repo(opts["repo"], bool(opts["allow_non_project"]), command_path=spec.command_path)
    args = ["pr", "merge", str(pr), "--repo", repo]
    for key, flag_name in (("merge", "--merge"), ("squash", "--squash"), ("rebase", "--rebase"), ("delete_branch", "--delete-branch"), ("admin", "--admin"), ("auto", "--auto")):
        if opts[key]:
            args.append(flag_name)
    return CommandResponse(run_gh_text(args), "text")


def publish_checkout_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    opts = parse_options(spec.command_path, tail, {"--pr": value("pr"), "--branch": value("branch"), "--detach": flag("detach"), "--force": flag("force"), "--recurse-submodules": flag("recurse_submodules"), "--repo": value("repo"), "--allow-non-project": flag("allow_non_project")})
    pr = require_positive_int("pr", opts["pr"], command_path=spec.command_path)
    repo = resolve_repo(opts["repo"], bool(opts["allow_non_project"]), command_path=spec.command_path)
    args = ["pr", "checkout", str(pr), "--repo", repo]
    if opts["branch"]:
        args.extend(["--branch", str(opts["branch"])])
    for key, flag_name in (("detach", "--detach"), ("force", "--force"), ("recurse_submodules", "--recurse-submodules")):
        if opts[key]:
            args.append(flag_name)
    return CommandResponse(run_gh_text(args), "text")


def stars_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    argv = {
        "list": ["--list-stars"],
        "add": ["--star"],
        "remove": ["--unstar"],
    }[spec.command_path[-1]] + list(tail)
    if json_mode and "--json" not in argv:
        argv.append("--json")
    return CommandResponse(helper_result(stars_cli.main, argv), "json" if json_mode else "text")


def lists_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    argv = {
        "list": ["--list-lists"],
        "items": ["--list-items"],
        "create": ["--create"],
        "delete": ["--delete"],
        "assign": ["--assign"],
        "unassign": ["--unassign"],
    }[spec.command_path[-1]] + list(tail)
    if json_mode and "--json" not in argv:
        argv.append("--json")
    return CommandResponse(helper_result(lists_cli.main, argv), "json" if json_mode else "text")


def request_get_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    if not tail:
        raise GhopsError("request get requires a path.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
    path = tail[0]
    if path.startswith("-"):
        raise GhopsError("request get expects the path immediately after 'get'.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
    extra = tail[1:]
    forbidden = first_mutating_request_flag(extra)
    if forbidden is not None:
        raise GhopsError(f"request get does not allow {forbidden}. Use the high-level ghops commands for writes.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
    result = run_gh_text(["api", path, "-X", "GET", *extra])
    return CommandResponse(result, "maybe_json" if json_mode else "text")


COMMAND_LIST = [
    CommandSpec(("repos", "list"), handler=repos_list_handler),
    CommandSpec(("repos", "view"), handler=repos_view_handler),
    CommandSpec(("issues", "list"), usage_tail="[--state open|closed|all] [--labels <label1,label2>] [--limit N] [--repo <owner/repo>] [--allow-non-project]", handler=issues_list_handler),
    CommandSpec(("issues", "view"), usage_tail="--issue <number> [--repo <owner/repo>] [--allow-non-project]", handler=issues_view_handler),
    CommandSpec(("issues", "create"), handler=issues_create_handler),
    CommandSpec(("issues", "update"), handler=issues_update_handler),
    CommandSpec(("issues", "comment"), handler=issues_comment_handler),
    CommandSpec(("issues", "comments"), handler=issues_comments_handler),
    CommandSpec(("issues", "close"), handler=issues_close_reopen_handler("close")),
    CommandSpec(("issues", "reopen"), handler=issues_close_reopen_handler("reopen")),
    CommandSpec(("issues", "close-with-evidence"), handler=issues_close_with_evidence_handler),
    CommandSpec(("issues", "copy"), handler=issue_copy_like_handler(move=False)),
    CommandSpec(("issues", "move"), handler=issue_copy_like_handler(move=True)),
    CommandSpec(("issues", "lock"), handler=issues_lock_unlock_handler("lock")),
    CommandSpec(("issues", "unlock"), handler=issues_lock_unlock_handler("unlock")),
    CommandSpec(("issues", "pin"), handler=issues_pin_unpin_handler("pin")),
    CommandSpec(("issues", "unpin"), handler=issues_pin_unpin_handler("unpin")),
    CommandSpec(("issues", "labels", "list"), handler=issues_labels_list_handler),
    CommandSpec(("issues", "labels", "create"), handler=issues_labels_create_handler),
    CommandSpec(("issues", "labels", "update"), handler=issues_labels_update_handler),
    CommandSpec(("issues", "labels", "delete"), handler=issues_labels_delete_handler),
    CommandSpec(("issues", "milestones", "list"), handler=issues_milestones_list_handler),
    CommandSpec(("issues", "suggest-labels"), handler=issues_suggest_labels_handler),
    CommandSpec(("prs", "list"), usage_tail="[--state open|closed|merged|all] [--author <user>] [--label <label>] [--base <branch>] [--head <branch>] [--search <query>] [--limit N] [--repo <owner/repo>] [--allow-non-project]", handler=prs_list_handler),
    CommandSpec(("prs", "view"), usage_tail="--pr <number> [--repo <owner/repo>] [--allow-non-project]", handler=prs_view_handler),
    CommandSpec(("prs", "patch"), usage_tail="--pr <number> [--repo <owner/repo>] [--path <file>] [--include-patch] [--allow-non-project]", handler=prs_patch_handler),
    CommandSpec(("prs", "update"), handler=prs_update_handler),
    CommandSpec(("reviews", "address"), usage_tail="--pr <number> [--repo <owner/repo>] [--include-resolved] [--selection <rows>] [--comment-ids <ids>] [--reply-body <text>] [--dry-run] [--allow-non-project]", handler=reviews_address_handler),
    CommandSpec(("reviews", "comment"), handler=reviews_comment_handler),
    CommandSpec(("reviews", "comments"), handler=reviews_comments_list_handler(lambda repo, pr: f"repos/{repo}/issues/{pr}/comments")),
    CommandSpec(("reviews", "review-comments"), handler=reviews_comments_list_handler(lambda repo, pr: f"repos/{repo}/pulls/{pr}/comments")),
    CommandSpec(("reviews", "review"), handler=reviews_review_handler),
    CommandSpec(("checks", "pr"), usage_tail="--pr <number> [--required] [--watch] [--interval <seconds>] [--fail-fast] [--repo <owner/repo>] [--allow-non-project]", handler=checks_pr_handler),
    CommandSpec(("actions", "list"), handler=actions_list_handler),
    CommandSpec(("actions", "inspect"), handler=actions_inspect_handler),
    CommandSpec(("reactions", "list"), usage_tail="--resource <type> --repo <owner/repo> [--number <n>|--comment-id <id>] [args...]", handler=reactions_handler),
    CommandSpec(("reactions", "add"), usage_tail="<reaction> --resource <type> --repo <owner/repo> [--number <n>|--comment-id <id>] [args...]", handler=reactions_handler),
    CommandSpec(("reactions", "remove"), usage_tail="<reaction-id> --resource <type> --repo <owner/repo> [--number <n>|--comment-id <id>] [args...]", handler=reactions_handler),
    CommandSpec(("stars", "list"), handler=stars_handler),
    CommandSpec(("stars", "add"), handler=stars_handler),
    CommandSpec(("stars", "remove"), handler=stars_handler),
    CommandSpec(("lists", "list"), handler=lists_handler),
    CommandSpec(("lists", "items"), handler=lists_handler),
    CommandSpec(("lists", "create"), handler=lists_handler),
    CommandSpec(("lists", "delete"), handler=lists_handler),
    CommandSpec(("lists", "assign"), handler=lists_handler),
    CommandSpec(("lists", "unassign"), handler=lists_handler),
    CommandSpec(("releases", "plan"), handler=release_plan_handler),
    CommandSpec(("releases", "notes"), handler=release_notes_handler),
    CommandSpec(("releases", "create"), handler=release_create_handler),
    CommandSpec(("publish", "context"), handler=publish_context_handler),
    CommandSpec(("publish", "open"), handler=publish_open_handler),
    CommandSpec(("publish", "create"), handler=publish_create_handler),
    CommandSpec(("publish", "draft"), handler=publish_simple_pr_handler(["pr", "ready"], extra_flags={"--undo": "undo"})),
    CommandSpec(("publish", "ready"), handler=publish_simple_pr_handler(["pr", "ready"])),
    CommandSpec(("publish", "merge"), handler=publish_merge_handler),
    CommandSpec(("publish", "close"), handler=publish_simple_pr_handler(["pr", "close"])),
    CommandSpec(("publish", "reopen"), handler=publish_simple_pr_handler(["pr", "reopen"])),
    CommandSpec(("publish", "checkout"), handler=publish_checkout_handler),
    CommandSpec(("request", "get"), usage_tail="<path> [gh-api-read-flags...]", handler=request_get_handler),
]

COMMAND_ORDER = [spec.command_path for spec in COMMAND_LIST]
COMMAND_SPECS = {spec.command_path: spec for spec in COMMAND_LIST}
GROUP_HELP_PREFIXES = {prefix for command_path in COMMAND_ORDER for prefix in (command_path[:size] for size in range(1, len(command_path)))}
ROOT_NOUN_DESCRIPTIONS = {
    "doctor": "runtime readiness and auth status",
    "repos": "repository discovery and orientation",
    "issues": "issue reads and mutations",
    "prs": "pull request reads and metadata edits",
    "reactions": "issue / PR / comment reactions",
    "reviews": "PR review-thread work",
    "checks": "PR-associated check status",
    "actions": "generic GitHub Actions runs and job inspection",
    "stars": "authenticated-user stars",
    "lists": "authenticated-user star lists",
    "releases": "release planning and publication",
    "publish": "current-branch PR lifecycle flows",
    "request": "read-only raw gh api escape hatch",
}
ROOT_NOUN_ORDER = ("doctor", "repos", "issues", "prs", "reactions", "reviews", "checks", "actions", "stars", "lists", "releases", "publish", "request")
ROOT_NOUNS = tuple(noun for noun in ROOT_NOUN_ORDER if noun == "doctor" or any(command_path[0] == noun for command_path in COMMAND_ORDER))
SORTED_COMMAND_KEYS = sorted(COMMAND_ORDER, key=len, reverse=True)
MAX_COMMAND_DEPTH = max(len(command_path) for command_path in COMMAND_ORDER)
