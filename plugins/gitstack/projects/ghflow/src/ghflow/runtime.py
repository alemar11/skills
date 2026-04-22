#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import io
import json
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from . import checks
from . import lists_cli
from . import stars_cli
from . import user_state


HOST = "github.com"
PROJECT_DIR = Path(__file__).resolve().parents[2]
PROJECT_SRC_DIR = Path(__file__).resolve().parents[1]
SKILL_DIR = Path(__file__).resolve().parents[4]
PYPROJECT_PATH = PROJECT_DIR / "pyproject.toml"


def load_version() -> str:
    candidates = [PYPROJECT_PATH]
    argv0 = Path(sys.argv[0]).resolve()
    if argv0.name == "ghflow":
        candidates.append(argv0.parent.parent / "projects" / "ghflow" / "pyproject.toml")
    for candidate in candidates:
        if not candidate.exists():
            continue
        with candidate.open("rb") as handle:
            payload = tomllib.load(handle)
        return str(payload.get("project", {}).get("version", "3.0.0"))
    return "3.0.0"


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
    allow_nonzero: bool = False
    error_code: str | None = None
    error_message: str | None = None
    error_retry: str | None = None


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


class GhflowError(Exception):
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
        if parsed["mode"] == "noun_help":
            print(render_noun_help(parsed["command"]))
            return 0

        command_path = parsed["command"]
        spec = COMMAND_SPECS.get(command_path)
        if spec is None or spec.handler is None:
            raise GhflowError(
                f"Unsupported command: {' '.join(command_path)}",
                code="invalid_arguments",
                exit_code=64,
                command_path=command_path,
            )

        response = spec.handler(spec, parsed["tail"], parsed["json"])
        if response.result.returncode != 0 and not response.allow_nonzero:
            raise build_runtime_error(response.result, command_path)

        if parsed["json"]:
            data = parse_output(response.result.stdout, response.output_kind)
            if response.result.returncode != 0:
                print_json_report(
                    command_path,
                    data=data,
                    code=response.error_code or "command_failed",
                    message=response.error_message
                    or extract_runtime_error_message(response.result)
                    or "Command failed.",
                    retry=response.error_retry,
                )
                return response.result.returncode
            print_json_success(command_path, data)
            return 0

        if response.result.stdout:
            sys.stdout.write(response.result.stdout)
        if response.result.stderr:
            sys.stderr.write(response.result.stderr)
        return response.result.returncode
    except GhflowError as exc:
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

    if argv[0] not in ROOT_NOUNS:
        raise GhflowError(
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
    raise GhflowError(
        f"Unsupported command: {' '.join(tokens)}",
        code="invalid_arguments",
        exit_code=64,
    )


def render_root_help() -> str:
    lines = [
        "Usage:",
        "  ghflow [--json] <noun> <verb> [args...]",
        "  ghflow --version",
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
            "  ghflow <noun> --help",
            "  ghflow <noun> <verb> --help",
        ]
    )
    return "\n".join(lines) + "\n"


def render_noun_help(command: tuple[str, ...]) -> str:
    if command not in GROUP_HELP_PREFIXES and command not in COMMAND_SPECS:
        raise GhflowError(
            f"No help is available for {' '.join(command)}.",
            code="invalid_arguments",
            exit_code=64,
            command_path=command,
        )
    return build_help_text(command)


def build_help_text(prefix: tuple[str, ...]) -> str:
    if prefix in COMMAND_SPECS and not has_descendants(prefix):
        spec = COMMAND_SPECS[prefix]
        return f"Usage:\n  ghflow [--json] {' '.join(prefix)} {spec.usage_tail}\n"

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
            lines.append(f"  ghflow [--json] {' '.join(spec.command_path)} {spec.usage_tail}")
        else:
            verbs = "|".join(spec.command_path[-1] for spec in direct_leaf_specs)
            lines.append(f"  ghflow [--json] {' '.join(prefix)} <{verbs}> [args...]")
    for child in nested_groups:
        nested_prefix = (*prefix, child)
        nested_leaf_specs = [COMMAND_SPECS[(*nested_prefix, grandchild)] for grandchild in immediate_children(nested_prefix) if (*nested_prefix, grandchild) in COMMAND_SPECS]
        if len(nested_leaf_specs) == 1 and not has_nested_groups(nested_prefix):
            spec = nested_leaf_specs[0]
            lines.append(f"  ghflow [--json] {' '.join(spec.command_path)} {spec.usage_tail}")
        elif nested_leaf_specs:
            verbs = "|".join(spec.command_path[-1] for spec in nested_leaf_specs)
            lines.append(f"  ghflow [--json] {' '.join(nested_prefix)} <{verbs}> [args...]")
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
            raise GhflowError(
                f"Unsupported argument for {' '.join(command_path)}: {token}",
                code="invalid_arguments",
                exit_code=64,
                command_path=command_path,
            )
        name, inline_value = token.split("=", 1) if "=" in token else (token, None)
        spec = specs.get(name)
        if spec is None:
            raise GhflowError(
                f"Unsupported argument for {' '.join(command_path)}: {name}",
                code="invalid_arguments",
                exit_code=64,
                command_path=command_path,
            )
        if spec.takes_value:
            if inline_value is None:
                if index + 1 >= len(tail):
                    raise GhflowError(
                        f"Missing value for {name}.",
                        code="invalid_arguments",
                        exit_code=64,
                        command_path=command_path,
                    )
                inline_value = tail[index + 1]
                index += 1
            if inline_value == "":
                raise GhflowError(
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
                raise GhflowError(
                    f"{name} does not accept a value.",
                    code="invalid_arguments",
                    exit_code=64,
                    command_path=command_path,
                )
            values[spec.dest] = True
        index += 1
    return values


def run(command: list[str], *, cwd: Path | None = None, input_text: str | None = None) -> RunResult:
    try:
        completed = subprocess.run(command, cwd=cwd, text=True, input=input_text, capture_output=True)
    except FileNotFoundError:
        executable = command[0] if command else "command"
        return RunResult(127, "", f"{executable} is not installed or not on PATH.\n")
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
        raise GhflowError(
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
            raise GhflowError(
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
    raise GhflowError(f"Unsupported output kind: {output_kind}", code="internal_error")


def print_json_success(command_path: tuple[str, ...], data: object) -> None:
    payload = {"ok": True, "version": VERSION, "command": list(command_path), "data": data}
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")


def print_json_report(
    command_path: tuple[str, ...],
    *,
    data: object,
    code: str,
    message: str,
    retry: str | None,
) -> None:
    payload = {
        "ok": False,
        "version": VERSION,
        "command": list(command_path),
        "data": data,
        "error": {"code": code, "message": message, "retry": retry},
    }
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
        raise GhflowError(
            f"Invalid --repo value '{repo}'. Use owner/repo.",
            code="invalid_arguments",
            exit_code=64,
        )
    return value


def require_positive_int(name: str, raw_value: str | None, *, command_path: tuple[str, ...]) -> int:
    if not raw_value or not re.fullmatch(r"[1-9][0-9]*", raw_value):
        raise GhflowError(
            f"Invalid --{name} value '{raw_value or ''}'. It must be a positive integer.",
            code="invalid_arguments",
            exit_code=64,
            command_path=command_path,
        )
    return int(raw_value)


def require_allowed_value(name: str, raw_value: str | None, allowed: list[str], *, command_path: tuple[str, ...]) -> str:
    if raw_value not in allowed:
        raise GhflowError(
            f"Invalid --{name} value '{raw_value or ''}'. Use {', '.join(allowed)}.",
            code="invalid_arguments",
            exit_code=64,
            command_path=command_path,
        )
    return str(raw_value)


def normalize_hex_color(raw_value: str, *, command_path: tuple[str, ...]) -> str:
    normalized = raw_value.lstrip("#")
    if not re.fullmatch(r"[A-Fa-f0-9]{6}", normalized):
        raise GhflowError(
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
            raise GhflowError(
                "repo is required when using --allow-non-project.",
                code="repo_context_missing",
                exit_code=2,
                command_path=command_path,
            )
        raise GhflowError(
            "No git repository detected. Pass --repo <owner/repo> for non-project operations.",
            code="repo_context_missing",
            exit_code=3,
            command_path=command_path,
        )
    remote_result = run_git_text(["remote", "get-url", "origin"])
    if remote_result.returncode != 0:
        raise GhflowError(
            "No origin remote found. Pass --repo <owner/repo>.",
            code="repo_context_missing",
            exit_code=4,
            command_path=command_path,
        )
    repo = normalize_remote_url(remote_result.stdout.strip())
    if repo is None:
        raise GhflowError(
            f"Could not resolve owner/repo from git remote: {remote_result.stdout.strip()}",
            code="repo_context_missing",
            exit_code=5,
            command_path=command_path,
        )
    return repo


def require_git_repo(command_path: tuple[str, ...]) -> None:
    if not is_git_repo():
        raise GhflowError(
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
        raise GhflowError(
            "Detached HEAD detected. Check out a branch first.",
            code="repo_context_missing",
            exit_code=5,
            command_path=command_path,
        )
    return branch


def current_repo_root() -> Path | None:
    result = run_git_text(["rev-parse", "--show-toplevel"])
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return Path(value) if value else None


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


def build_runtime_error(result: RunResult, command_path: tuple[str, ...]) -> GhflowError:
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
    return GhflowError(message, code=code, retry=retry, exit_code=result.returncode or 1, command_path=command_path)


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


def ci_inspect_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    opts = parse_options(spec.command_path, tail, {
        "--pr": value("pr"),
        "--repo": value("repo"),
        "--allow-non-project": flag("allow_non_project"),
        "--max-lines": value("max_lines", default=str(checks.DEFAULT_MAX_LINES)),
        "--context": value("context", default=str(checks.DEFAULT_CONTEXT_LINES)),
    })
    repo = resolve_repo(opts["repo"], bool(opts["allow_non_project"]), command_path=spec.command_path)
    max_lines = require_positive_int("max-lines", str(opts["max_lines"]), command_path=spec.command_path)
    context = require_positive_int("context", str(opts["context"]), command_path=spec.command_path)
    repo_root = current_repo_root() if is_git_repo() else None

    try:
        payload, exit_code = checks.inspect_pr_failures(
            repo=repo,
            repo_root=repo_root,
            pr_value=opts["pr"],
            max_lines=max_lines,
            context=context,
        )
    except checks.InspectionError as exc:
        return text_response(stderr=f"{exc.message}\n", returncode=exc.exit_code)

    if json_mode:
        return CommandResponse(
            RunResult(exit_code, json.dumps(payload, indent=2) + "\n", ""),
            "json",
            allow_nonzero=exit_code != 0,
            error_code="failing_checks" if exit_code != 0 else None,
            error_message="Failing checks remain." if exit_code != 0 else None,
        )
    return CommandResponse(
        RunResult(exit_code, checks.render_results(payload), ""),
        "text",
        allow_nonzero=exit_code != 0,
        error_code="failing_checks" if exit_code != 0 else None,
        error_message="Failing checks remain." if exit_code != 0 else None,
    )


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
            raise GhflowError("Use either --selection or --comment-ids with --reply-body, not both.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
        if not opts["selection"] and not opts["comment_ids"]:
            raise GhflowError("--reply-body requires either --selection or --comment-ids.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
    elif opts["selection"] or opts["comment_ids"]:
        raise GhflowError("--selection and --comment-ids require --reply-body.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
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
                    raise GhflowError(f"Selection index '{part}' was not found.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
                selected_entries.append(entries_by_index[part])
        else:
            for part in raw_parts:
                if part not in entries_by_comment_id:
                    raise GhflowError(f"Comment ID '{part}' was not found in the fetched context.", code="invalid_arguments", exit_code=64, command_path=spec.command_path)
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


def publish_context_handler(spec: CommandSpec, tail: list[str], json_mode: bool) -> CommandResponse:
    opts = parse_options(spec.command_path, tail, {"--repo": value("repo"), "--allow-non-project": flag("allow_non_project")})
    require_git_repo(spec.command_path)
    local_repo = resolve_repo(None, False, command_path=spec.command_path)
    if opts["repo"] and str(opts["repo"]) != local_repo:
        raise GhflowError(f"Cross-repo publish is not supported. Current checkout resolves to {local_repo}.", code="repo_context_mismatch", exit_code=2, command_path=spec.command_path)
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
        raise GhflowError(f"Cross-repo PR creation is not supported by publish open. Current checkout resolves to {local_repo}.", code="repo_context_mismatch", exit_code=2, command_path=spec.command_path)
    repo = local_repo
    remote_name = tracking_remote_name(branch)
    remote_branch = tracking_branch_name(branch)
    if not remote_name or not remote_branch:
        raise GhflowError(f"Current branch '{branch}' has no configured upstream. Push it before opening a PR.", code="repo_context_missing", exit_code=5, command_path=spec.command_path)
    if remote_branch != branch:
        raise GhflowError(f"Current branch '{branch}' tracks '{remote_name}/{remote_branch}'. This helper only supports same-name remote branches.", code="repo_context_mismatch", exit_code=5, command_path=spec.command_path)
    if run_git_text(["ls-remote", "--exit-code", "--heads", remote_name, branch]).returncode != 0:
        raise GhflowError(f"Current branch '{branch}' is not available on remote '{remote_name}'. Push it before opening a PR.", code="repo_context_missing", exit_code=5, command_path=spec.command_path)
    existing = gh_json(["pr", "list", "--repo", repo, "--head", branch, "--state", "open", "--json", "number,url,title,baseRefName,headRefName,isDraft", "--limit", "1"], command_path=spec.command_path)
    if isinstance(existing, list) and existing:
        pr_info = existing[0]
        if opts["base"] and pr_info.get("baseRefName") != opts["base"]:
            raise GhflowError(
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
        raise GhflowError("Could not derive a PR title from HEAD. Pass --title explicitly.", code="invalid_arguments", exit_code=6, command_path=spec.command_path)
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
        "delete": ["--delete"],
        "assign": ["--assign"],
        "unassign": ["--unassign"],
    }[spec.command_path[-1]] + list(tail)
    if json_mode and "--json" not in argv:
        argv.append("--json")
    return CommandResponse(helper_result(lists_cli.main, argv), "json" if json_mode else "text")


COMMAND_LIST = [
    CommandSpec(("ci", "inspect"), usage_tail="[--pr <number-or-url>] [--repo <owner/repo>] [--allow-non-project] [--max-lines <count>] [--context <count>]", handler=ci_inspect_handler),
    CommandSpec(("reviews", "address"), usage_tail="--pr <number> [--repo <owner/repo>] [--include-resolved] [--selection <rows>] [--comment-ids <ids>] [--reply-body <text>] [--dry-run] [--allow-non-project]", handler=reviews_address_handler),
    CommandSpec(("stars", "list"), handler=stars_handler),
    CommandSpec(("stars", "add"), handler=stars_handler),
    CommandSpec(("stars", "remove"), handler=stars_handler),
    CommandSpec(("stars", "lists", "list"), handler=lists_handler),
    CommandSpec(("stars", "lists", "items"), handler=lists_handler),
    CommandSpec(("stars", "lists", "delete"), handler=lists_handler),
    CommandSpec(("stars", "lists", "assign"), handler=lists_handler),
    CommandSpec(("stars", "lists", "unassign"), handler=lists_handler),
    CommandSpec(("publish", "context"), handler=publish_context_handler),
    CommandSpec(("publish", "open"), handler=publish_open_handler),
]

COMMAND_ORDER = [spec.command_path for spec in COMMAND_LIST]
COMMAND_SPECS = {spec.command_path: spec for spec in COMMAND_LIST}
GROUP_HELP_PREFIXES = {prefix for command_path in COMMAND_ORDER for prefix in (command_path[:size] for size in range(1, len(command_path)))}
ROOT_NOUN_DESCRIPTIONS = {
    "ci": "failing PR check inspection for GitHub Actions",
    "reviews": "PR review-thread work",
    "stars": "authenticated-user stars and star lists",
    "publish": "current-branch PR context and open-or-reuse flows",
}
ROOT_NOUN_ORDER = ("ci", "reviews", "stars", "publish")
ROOT_NOUNS = tuple(noun for noun in ROOT_NOUN_ORDER if any(command_path[0] == noun for command_path in COMMAND_ORDER))
SORTED_COMMAND_KEYS = sorted(COMMAND_ORDER, key=len, reverse=True)
MAX_COMMAND_DEPTH = max(len(command_path) for command_path in COMMAND_ORDER)
