from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from typing import Any, Sequence

from .common import REPO_PATTERN, GError, Result, envelope, run, safe_diagnostic


EXTENSION_REPOSITORY = "github/gh-stack"
EXTENSION_COMMAND = "stack"
EXTENSION_LIST_COMMAND = ["gh", "extension", "list"]
EXTENSION_INSTALL_COMMAND = ["gh", "extension", "install", EXTENSION_REPOSITORY]

STACK_COMMANDS = (
    "init",
    "add",
    "checkout",
    "link",
    "push",
    "submit",
    "sync",
    "rebase",
    "view",
    "merge",
    "unstack",
    "up",
    "down",
    "top",
    "bottom",
    "trunk",
)

BLOCKED_COMMANDS = {"modify", "switch", "alias", "feedback"}
INTERACTIVE_FLAGS = {"--interactive", "--tty"}
INIT_OPTIONS_WITH_VALUES = {"--base", "-b", "--prefix", "-p"}
MERGE_OPTIONS_WITH_VALUES = {"--merge-method"}
MISSING_EXIT_CODE = 69
CONFLICT_EXIT_CODE = 65


def _noninteractive_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment["GH_PAGER"] = "cat"
    environment["GIT_PAGER"] = "cat"
    environment["PAGER"] = "cat"
    environment["GIT_TERMINAL_PROMPT"] = "0"
    return environment


def _empty_status(*, status: str, gh_path: str | None) -> dict[str, Any]:
    return {
        "ok": status == "ready",
        "status": status,
        "installed": False,
        "command": EXTENSION_COMMAND,
        "repository": EXTENSION_REPOSITORY,
        "version": None,
        "publisher_verification": None,
        "reason": None,
        "gh_path": gh_path,
    }


def _parse_extension_line(line: str) -> dict[str, str | None] | None:
    parts = line.split()
    if len(parts) < 2 or parts[0] != "gh":
        return None
    return {
        "command": parts[1],
        "repository": parts[2] if len(parts) > 2 else None,
        "version": parts[3] if len(parts) > 3 else None,
    }


def extension_status(gh_path: str | None = None) -> dict[str, Any]:
    """Inspect the locally installed official gh-stack extension.

    The check is deliberately based on ``gh extension list`` rather than
    invoking ``gh stack``. This keeps discovery read-only and prevents a
    missing-extension prompt from becoming an implicit installation path.
    """

    resolved_gh_path = gh_path if gh_path is not None else shutil.which("gh")
    if not resolved_gh_path:
        return _empty_status(status="gh-missing", gh_path=None)

    result = run(
        EXTENSION_LIST_COMMAND,
        env=_noninteractive_environment(),
        stdin=subprocess.DEVNULL,
    )
    if result.returncode:
        status = _empty_status(status="unverified", gh_path=resolved_gh_path)
        status["reason"] = "command-failed"
        status["list_exit_code"] = result.returncode
        status["upstream_command"] = list(EXTENSION_LIST_COMMAND)
        return status

    entries = [
        entry
        for line in result.stdout.splitlines()
        if (entry := _parse_extension_line(line)) is not None
    ]
    official = next(
        (entry for entry in entries if entry["repository"] == EXTENSION_REPOSITORY),
        None,
    )
    if official is not None:
        if not official["version"]:
            status = _empty_status(status="unverified", gh_path=resolved_gh_path)
            status["reason"] = "missing-version"
            status["detected_repository"] = official["repository"]
            return status
        return {
            "ok": True,
            "status": "ready",
            "installed": True,
            "command": EXTENSION_COMMAND,
            "repository": official["repository"],
            "version": official["version"],
            "publisher_verification": "not-verified",
            "reason": None,
            "gh_path": resolved_gh_path,
        }

    stack_entries = [entry for entry in entries if entry["command"] == EXTENSION_COMMAND]
    if stack_entries:
        detected = stack_entries[0]["repository"]
        if not detected or not REPO_PATTERN.fullmatch(detected):
            status = _empty_status(status="unverified", gh_path=resolved_gh_path)
            status["reason"] = "missing-repository" if not detected else "invalid-repository"
            status["detected_repository"] = detected
            status["upstream_command"] = list(EXTENSION_LIST_COMMAND)
            return status
        conflict = _empty_status(status="conflict", gh_path=resolved_gh_path)
        conflict["installed"] = True
        conflict["repository"] = detected
        conflict["version"] = stack_entries[0]["version"]
        conflict["publisher_verification"] = "not-verified"
        conflict["expected_repository"] = EXTENSION_REPOSITORY
        return conflict

    if result.stdout.strip() and not entries:
        status = _empty_status(status="unverified", gh_path=resolved_gh_path)
        status["reason"] = "unparseable-output"
        status["upstream_command"] = list(EXTENSION_LIST_COMMAND)
        return status

    return _empty_status(status="missing", gh_path=resolved_gh_path)


def _print_provider_diagnostic(result: Result) -> None:
    diagnostic = safe_diagnostic(result.stderr or result.stdout, limit=2000)
    if diagnostic:
        print(diagnostic, file=sys.stderr)


def _raise_process_failure(
    result: Result,
    *,
    code: str,
    message: str,
    command: Sequence[str],
    exit_code: int | None = None,
    json_mode: bool = False,
) -> None:
    if not json_mode:
        _print_provider_diagnostic(result)
    diagnostic = safe_diagnostic(result.stderr or result.stdout)
    details: dict[str, Any] = {
        "upstream_exit_code": result.returncode,
        "upstream_command": list(command),
    }
    if diagnostic and not json_mode:
        details["diagnostic"] = diagnostic
    raise GError(
        message,
        code=code,
        exit_code=exit_code if exit_code is not None else (result.returncode or 1),
        details=details,
    )


def _status_error(status: dict[str, Any]) -> GError:
    state = status.get("status")
    if state == "gh-missing":
        return GError(
            "GitHub CLI 'gh' is not installed or not on PATH.",
            code="gh_missing",
            exit_code=MISSING_EXIT_CODE,
        )
    if state == "conflict":
        return GError(
            f"The 'gh stack' command is provided by '{status.get('repository')}', not '{EXTENSION_REPOSITORY}'.",
            code="extension_conflict",
            exit_code=CONFLICT_EXIT_CODE,
            details={
                "detected_repository": status.get("repository"),
                "expected_repository": EXTENSION_REPOSITORY,
            },
        )
    if state == "unverified":
        details: dict[str, Any] = {
            "upstream_command": status.get("upstream_command", EXTENSION_LIST_COMMAND),
        }
        if status.get("list_exit_code") is not None:
            details["upstream_exit_code"] = status["list_exit_code"]
        if status.get("reason") is not None:
            details["reason"] = status["reason"]
        if status.get("detected_repository") is not None:
            details["detected_repository"] = status["detected_repository"]
        return GError(
            "Could not verify the installed 'gh stack' extension from 'gh extension list'.",
            code="extension_unverified",
            exit_code=MISSING_EXIT_CODE,
            details=details,
        )
    return GError(
        f"The '{EXTENSION_REPOSITORY}' extension is not installed. Run 'g stack ensure --install'.",
        code="extension_missing",
        exit_code=MISSING_EXIT_CODE,
    )


def ensure(*, install: bool = False, json_mode: bool = False) -> dict[str, Any]:
    """Verify or explicitly install the official gh-stack extension."""

    status = extension_status()
    if status["status"] == "ready":
        status["action"] = "already-installed"
        return status
    if status["status"] != "missing":
        raise _status_error(status)
    if not install:
        raise _status_error(status)

    result = run(
        EXTENSION_INSTALL_COMMAND,
        env=_noninteractive_environment(),
        stdin=subprocess.DEVNULL,
    )
    if result.returncode:
        _raise_process_failure(
            result,
            code="extension_install_failed",
            message=f"Could not install '{EXTENSION_REPOSITORY}'.",
            command=EXTENSION_INSTALL_COMMAND,
            json_mode=json_mode,
        )

    verified = extension_status()
    if verified["status"] != "ready":
        raise GError(
            f"The '{EXTENSION_REPOSITORY}' installation completed but could not be verified.",
            code="extension_install_unverified",
            exit_code=MISSING_EXIT_CODE,
            details={"status": verified},
        )
    verified["action"] = "installed"
    return verified


def _has_flag(args: Sequence[str], flag: str) -> bool:
    return any(arg == flag for arg in args)


def _has_enabled_flag(args: Sequence[str], flag: str) -> bool:
    for arg in args:
        if arg == flag:
            return True
        if arg.startswith(f"{flag}="):
            return arg.split("=", 1)[1].lower() == "true"
    return False


def _has_positional(args: Sequence[str], options_with_values: set[str]) -> bool:
    skip_value = False
    for index, arg in enumerate(args):
        if skip_value:
            skip_value = False
            continue
        if arg == "--":
            return bool(args[index + 1 :])
        if arg in options_with_values:
            skip_value = True
            continue
        if any(arg.startswith(f"{option}=") for option in options_with_values):
            continue
        if not arg.startswith("-"):
            return True
    return False


def _has_message_flag(args: Sequence[str]) -> bool:
    for arg in args:
        if arg == "--message" or arg.startswith("--message=") or arg == "-m":
            return True
        if arg.startswith("-") and not arg.startswith("--") and "m" in arg[1:]:
            return True
    return False


def _validate_noninteractive(command: str, args: Sequence[str]) -> None:
    if command in BLOCKED_COMMANDS or any(
        _has_enabled_flag(args, flag) for flag in INTERACTIVE_FLAGS
    ):
        raise GError(
            f"The 'gh stack {command}' interactive path is not available through G.",
            code="interactive_command",
            exit_code=64,
        )
    if command == "init" and not _has_positional(args, INIT_OPTIONS_WITH_VALUES):
        raise GError(
            "'gh stack init' requires at least one explicit branch.",
            code="interactive_command",
            exit_code=64,
        )
    if command == "add" and not (_has_positional(args, set()) or _has_message_flag(args)):
        raise GError(
            "'gh stack add' requires a branch or an explicit commit message.",
            code="interactive_command",
            exit_code=64,
        )
    if command == "checkout" and not _has_positional(args, set()):
        raise GError(
            "'gh stack checkout' requires an explicit stack, PR, URL, or branch.",
            code="interactive_command",
            exit_code=64,
        )
    if command == "submit" and not _has_enabled_flag(args, "--auto"):
        raise GError(
            "'gh stack submit' requires --auto in the non-interactive wrapper.",
            code="interactive_command",
            exit_code=64,
        )
    if command == "merge" and (
        not _has_positional(args, MERGE_OPTIONS_WITH_VALUES)
        or not _has_enabled_flag(args, "--yes")
    ):
        raise GError(
            "'gh stack merge' requires an explicit target and --yes in the non-interactive wrapper.",
            code="interactive_command",
            exit_code=64,
        )
    if command == "unstack" and not (
        _has_positional(args, set()) or _has_flag(args, "--local")
    ):
        raise GError(
            "'gh stack unstack' requires an explicit target; use --local to remove the active local stack.",
            code="invalid_arguments",
            exit_code=64,
        )


def _json_output(command: str, stdout: str, stderr: str, *, parse: bool) -> Any:
    if not parse:
        return {"stdout": stdout, "stderr": safe_diagnostic(stderr)}
    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise GError(
            f"Could not parse JSON output from 'gh stack {command}'.",
            code="provider_response_invalid",
            exit_code=65,
            details={"upstream_command": ["gh", "stack", command]},
        ) from exc


def _strip_raw_separator(args: Sequence[str]) -> list[str]:
    values = list(args)
    if values and values[0] == "--":
        values.pop(0)
    return values


def execute(command: str, args: Sequence[str], *, json_mode: bool, raw: bool = False) -> int:
    forwarded = list(args)
    if raw:
        forwarded = _strip_raw_separator(forwarded)
        if not forwarded:
            raise GError(
                "'stack raw' requires an upstream gh-stack command.",
                code="invalid_arguments",
                exit_code=64,
            )
        command, *forwarded = forwarded

    _validate_noninteractive(command, forwarded)
    ensure(json_mode=json_mode)

    view_json = command == "view" and not any(
        _has_enabled_flag(forwarded, flag) for flag in ("--help", "-h")
    )
    if json_mode and view_json and not _has_enabled_flag(forwarded, "--json"):
        forwarded.append("--json")

    upstream_command = ["gh", "stack", command, *forwarded]
    result = run(
        upstream_command,
        env=_noninteractive_environment(),
        stdin=subprocess.DEVNULL,
    )
    if result.returncode:
        _raise_process_failure(
            result,
            code="stack_command_failed",
            message=f"The 'gh stack {command}' command failed.",
            command=["gh", "stack", command],
            json_mode=json_mode,
        )

    if json_mode:
        data = _json_output(
            command,
            result.stdout,
            result.stderr,
            parse=view_json,
        )
        label = ["stack", "raw"] if raw else ["stack", command]
        print(json.dumps(envelope(label, data), indent=2))
    else:
        if result.stdout:
            sys.stdout.write(result.stdout)
        if result.stderr:
            sys.stderr.write(result.stderr)
    return 0


def execute_raw(args: Sequence[str], *, json_mode: bool) -> int:
    return execute("", args, json_mode=json_mode, raw=True)
