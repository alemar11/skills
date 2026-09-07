from __future__ import annotations

# Public compatibility façade for the split star command modules.
# ruff: noqa: F401

import argparse
import contextlib
import io
import json
import sys
from dataclasses import dataclass
from typing import Callable

from . import __version__ as VERSION
from .health import doctor as shared_doctor, doctor_text
from .star_api import (
    GhError,
    collect_repo_targets,
    graphql,
    list_items,
    repo_memberships,
    repo_view,
    resolve_list,
    validate_repo_reference,
    viewer_lists,
)
from .star_lists import build_parser as build_lists_parser
from .star_lists import main as lists_main


@dataclass(frozen=True)
class RunResult:
    returncode: int
    stdout: str
    stderr: str


def helper_result(
    main_func: Callable[[list[str] | None], int], argv: list[str]
) -> RunResult:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        try:
            returncode = int(main_func(argv))
        except SystemExit as exc:
            returncode = int(exc.code) if isinstance(exc.code, int) else 1
    return RunResult(returncode, stdout.getvalue(), stderr.getvalue())


def doctor_payload() -> dict[str, object]:
    return shared_doctor()


def parse_json(stdout: str) -> object:
    cleaned = stdout.strip()
    return json.loads(cleaned) if cleaned else None


def emit_json_result(command: list[str], result: RunResult) -> int:
    if result.returncode == 0:
        payload = {
            "ok": True,
            "version": VERSION,
            "command": command,
            "data": parse_json(result.stdout),
        }
    else:
        payload = {
            "ok": False,
            "version": VERSION,
            "command": command,
            "error": {
                "code": "command_failed",
                "message": (
                    result.stderr or result.stdout or "stars command failed"
                ).strip(),
            },
        }
    print(json.dumps(payload, indent=2))
    return result.returncode


def invoke(command: list[str], json_mode: bool) -> int:
    if not command:
        print(build_top_parser().format_help(), end="")
        return 0
    domain = command[0]
    if domain == "lists" and len(command) >= 2:
        mapping = {"assign": "--assign", "unassign": "--unassign"}
        if command[1] not in mapping:
            raise SystemExit(f"Unsupported lists command: {command[1]}")
        argv = [mapping[command[1]], *_list_args(command[1], command[2:])]
        main_func = lists_main
    else:
        raise SystemExit(f"Unsupported command: {' '.join(command)}")
    if json_mode and "--json" not in argv:
        argv.append("--json")
    result = helper_result(main_func, argv)
    if json_mode:
        return emit_json_result(command, result)
    if result.stdout:
        sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)
    return result.returncode


def _list_args(action: str, args: list[str]) -> list[str]:
    if not args or args[0].startswith("-"):
        return args
    converted = ["--list-id", args[0]]
    rest = args[1:]
    if action in {"assign", "unassign"} and rest and not rest[0].startswith("-"):
        converted += ["--repo", rest[0]]
        rest = rest[1:]
    return [*converted, *rest]


def build_top_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Update authenticated-user GitHub star-list memberships."
    )
    parser.add_argument(
        "--json", action="store_true", help="Emit a stable JSON envelope."
    )
    parser.add_argument(
        "--version", action="store_true", help="Print version and exit."
    )
    parser.add_argument(
        "command",
        nargs="*",
        help="Commands: lists assign/unassign, doctor.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    raw = list(argv if argv is not None else sys.argv[1:])
    if not raw or raw in (["-h"], ["--help"]):
        print(build_top_parser().format_help(), end="")
        return 0
    json_mode = "--json" in raw
    raw = [item for item in raw if item != "--json"]
    if raw == ["--version"]:
        print(VERSION)
        return 0
    if raw == ["doctor"]:
        payload = doctor_payload()
        if json_mode:
            print(json.dumps(payload, indent=2))
        else:
            print(doctor_text(payload, f"g stars {VERSION}"))
        return 0 if payload["ok"] else 1
    try:
        return invoke(raw, json_mode)
    except SystemExit as exc:
        message = str(exc)
        if json_mode:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "version": VERSION,
                        "command": raw,
                        "error": {"code": "invalid_arguments", "message": message},
                    },
                    indent=2,
                )
            )
        else:
            print(message, file=sys.stderr)
        return 64


if __name__ == "__main__":
    raise SystemExit(main())
