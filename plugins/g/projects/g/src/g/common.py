from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from . import __version__
from .repository import REPO_PATTERN, normalize_remote


@dataclass(frozen=True)
class Result:
    returncode: int
    stdout: str
    stderr: str


class GError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        code: str = "command_failed",
        exit_code: int = 1,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code
        self.details = details


def safe_diagnostic(value: str | None, *, limit: int = 2000) -> str | None:
    """Return bounded provider text with common credential forms removed."""

    if not value:
        return None
    diagnostic = value.strip()
    if not diagnostic:
        return None
    diagnostic = re.sub(
        r"(?i)(authorization\s*:\s*bearer\s+|bearer\s+|(?:token|password|passwd|secret|api[_-]?key)\s*[=:]\s*)\S+",
        r"\1[REDACTED]",
        diagnostic,
    )
    diagnostic = re.sub(r"(?i)(gh[pousr]_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+)", "[REDACTED]", diagnostic)
    if len(diagnostic) > limit:
        diagnostic = diagnostic[:limit].rstrip() + "…"
    return diagnostic


def run(
    command: Sequence[str],
    cwd: Path | None = None,
    *,
    env: Mapping[str, str] | None = None,
    stdin: int | None = None,
) -> Result:
    try:
        proc = subprocess.run(
            list(command),
            cwd=cwd,
            text=True,
            capture_output=True,
            env=dict(env) if env is not None else None,
            stdin=stdin,
        )
    except FileNotFoundError as exc:
        raise GError(
            f"Command '{command[0]}' is not installed or not on PATH.",
            code="process_spawn_failed",
            exit_code=127,
            details={"upstream_command": list(command), "reason": "not-found"},
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise GError(
            f"Command '{command[0]}' timed out.",
            code="process_timeout",
            exit_code=124,
            details={"upstream_command": list(command), "reason": "timeout"},
        ) from exc
    except (OSError, UnicodeError) as exc:
        details: dict[str, Any] = {
            "upstream_command": list(command),
            "reason": type(exc).__name__,
        }
        if isinstance(exc, OSError) and exc.errno is not None:
            details["errno"] = exc.errno
        raise GError(
            f"Could not execute command '{command[0]}'.",
            code="process_spawn_failed" if isinstance(exc, OSError) else "process_output_invalid",
            exit_code=126 if isinstance(exc, OSError) else 65,
            details=details,
        ) from exc
    return Result(proc.returncode, proc.stdout, proc.stderr)


def checked(
    command: Sequence[str],
    cwd: Path | None = None,
    *,
    env: Mapping[str, str] | None = None,
    stdin: int | None = None,
) -> Result:
    result = run(command, cwd, env=env, stdin=stdin)
    if result.returncode:
        diagnostic = safe_diagnostic(result.stderr or result.stdout)
        details: dict[str, Any] = {
            "upstream_command": list(command),
            "upstream_exit_code": result.returncode,
        }
        if diagnostic:
            details["diagnostic"] = diagnostic
        raise GError(
            diagnostic or "Command failed.",
            exit_code=result.returncode,
            details=details,
        )
    return result


def envelope(command: list[str], data: Any) -> dict[str, Any]:
    return {"ok": True, "version": __version__, "command": command, "data": data}


def error_envelope(command: list[str], exc: GError) -> dict[str, Any]:
    error: dict[str, Any] = {"code": exc.code, "message": str(exc)}
    if exc.details is not None:
        error["details"] = exc.details
    return {"ok": False, "version": __version__, "command": command, "error": error}
