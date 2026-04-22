#!/usr/bin/env python3
from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from shutil import which
from typing import Any, Iterable, Sequence


REPO_PATTERN = re.compile(r"^[^/\s]+/[^/\s]+$")

FAILURE_CONCLUSIONS = {
    "failure",
    "cancelled",
    "timed_out",
    "action_required",
}

FAILURE_STATES = {
    "failure",
    "error",
    "cancelled",
    "timed_out",
    "action_required",
}

FAILURE_BUCKETS = {"fail"}

FAILURE_MARKERS = (
    "error",
    "fail",
    "failed",
    "traceback",
    "exception",
    "assert",
    "panic",
    "fatal",
    "timeout",
    "segmentation fault",
)

DEFAULT_MAX_LINES = 160
DEFAULT_CONTEXT_LINES = 30
PENDING_LOG_MARKERS = (
    "still in progress",
    "log will be available when it is complete",
)

RUN_METADATA_FIELDS = [
    "conclusion",
    "status",
    "workflowName",
    "name",
    "event",
    "headBranch",
    "headSha",
    "url",
]

PRIMARY_CHECK_FIELDS = [
    "name",
    "state",
    "conclusion",
    "detailsUrl",
    "startedAt",
    "completedAt",
]

FALLBACK_CHECK_FIELDS = [
    "name",
    "state",
    "bucket",
    "link",
    "startedAt",
    "completedAt",
    "workflow",
    "conclusion",
    "event",
]


class InspectionError(Exception):
    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.message = message
        self.exit_code = exit_code


class GhResult:
    def __init__(self, returncode: int, stdout: str, stderr: str):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def run_gh_command(args: Sequence[str], cwd: Path | None) -> GhResult:
    process = subprocess.run(
        ["gh", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
    )
    return GhResult(process.returncode, process.stdout, process.stderr)


def run_gh_command_raw(args: Sequence[str], cwd: Path | None) -> tuple[int, bytes, str]:
    process = subprocess.run(
        ["gh", *args],
        cwd=cwd,
        capture_output=True,
    )
    return process.returncode, process.stdout, process.stderr.decode(errors="replace")


def run_git_command(args: Sequence[str], cwd: Path | None) -> GhResult:
    process = subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
    )
    return GhResult(process.returncode, process.stdout, process.stderr)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect failing GitHub PR checks, fetch GitHub Actions logs, and extract a "
            "failure snippet."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--repo",
        default=None,
        help="Target repository as owner/repo. Defaults to the current checkout.",
    )
    parser.add_argument(
        "--pr",
        default=None,
        help="PR number or URL (defaults to current branch PR).",
    )
    parser.add_argument("--max-lines", type=int, default=DEFAULT_MAX_LINES)
    parser.add_argument("--context", type=int, default=DEFAULT_CONTEXT_LINES)
    parser.add_argument(
        "--allow-non-project",
        action="store_true",
        help="Allow use outside a local git checkout when --repo is provided.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of human-readable output.",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        repo, repo_root = resolve_repo_context(
            args.repo,
            allow_non_project=args.allow_non_project,
        )
        payload, exit_code = inspect_pr_failures(
            repo=repo,
            repo_root=repo_root,
            pr_value=args.pr,
            max_lines=max(1, args.max_lines),
            context=max(1, args.context),
        )
    except InspectionError as exc:
        print(exc.message, file=sys.stderr)
        return exc.exit_code

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(render_results(payload), end="")
    return exit_code


def find_git_root(start: Path | None = None) -> Path | None:
    result = run_git_command(["rev-parse", "--show-toplevel"], cwd=start or Path.cwd())
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip())


def ensure_gh_available(cwd: Path | None) -> None:
    if which("gh") is None:
        raise InspectionError("gh is not installed or not on PATH.", 127)
    result = run_gh_command(["auth", "status"], cwd=cwd)
    if result.returncode == 0:
        return
    message = (result.stderr or result.stdout or "").strip()
    raise InspectionError(message or "gh not authenticated.", 1)


def validate_repo_reference(repo: str) -> str:
    value = repo.strip()
    if not REPO_PATTERN.fullmatch(value):
        raise InspectionError(f"Invalid --repo value '{repo}'. Use owner/repo.", 64)
    return value


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


def resolve_repo_from_checkout(repo_root: Path) -> str:
    result = run_git_command(["remote", "get-url", "origin"], cwd=repo_root)
    if result.returncode != 0:
        raise InspectionError("No origin remote found. Pass --repo <owner/repo>.", 4)
    repo = normalize_remote_url(result.stdout.strip())
    if repo is None:
        raise InspectionError(
            f"Could not resolve owner/repo from git remote: {result.stdout.strip()}",
            5,
        )
    return repo


def resolve_repo_context(
    repo_ref: str | None,
    *,
    allow_non_project: bool,
) -> tuple[str, Path | None]:
    repo_root = find_git_root()
    if repo_ref:
        repo = validate_repo_reference(repo_ref)
        if repo_root is None and not allow_non_project:
            raise InspectionError(
                "No git repository detected. Pass --allow-non-project with --repo <owner/repo>.",
                3,
            )
        return repo, repo_root
    if repo_root is None:
        raise InspectionError(
            "No git repository detected. Pass --repo <owner/repo> for non-project operations.",
            3,
        )
    return resolve_repo_from_checkout(repo_root), repo_root


def append_repo_flag(args: list[str], repo: str) -> list[str]:
    return [*args, "--repo", repo]


def resolve_pr(pr_value: str | None, repo: str, repo_root: Path | None) -> str:
    if pr_value:
        if pr_value.startswith("http://") or pr_value.startswith("https://"):
            match = re.search(r"/pull/(\d+)", pr_value)
            if match:
                return match.group(1)
        return pr_value

    result = run_gh_command(
        append_repo_flag(["pr", "view", "--json", "number"], repo),
        cwd=repo_root,
    )
    if result.returncode != 0:
        message = (result.stderr or result.stdout or "").strip()
        raise InspectionError(message or "Error: unable to resolve PR.", 1)
    try:
        data = json.loads(result.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise InspectionError(f"Error: unable to parse PR JSON: {exc}", 1) from exc

    number = data.get("number")
    if not number:
        raise InspectionError("Error: no PR number found. Provide --pr explicitly.", 1)
    return str(number)


def inspect_pr_failures(
    *,
    repo: str,
    repo_root: Path | None,
    pr_value: str | None,
    max_lines: int,
    context: int,
) -> tuple[dict[str, Any], int]:
    ensure_gh_available(repo_root)
    pr_number = resolve_pr(pr_value, repo, repo_root)
    checks = fetch_checks(pr_number, repo, repo_root)
    failing = [check for check in checks if is_failing(check)]
    payload: dict[str, Any] = {
        "repo": repo,
        "pr": pr_number,
        "failingCount": len(failing),
        "results": [],
    }
    if not failing:
        payload["summary"] = "no_failing_checks"
        payload["message"] = f"PR #{pr_number}: no failing checks detected."
        return payload, 0

    payload["summary"] = "failing_checks"
    payload["results"] = [
        analyze_check(
            check,
            repo=repo,
            repo_root=repo_root,
            max_lines=max_lines,
            context=context,
        )
        for check in failing
    ]
    payload["message"] = f"PR #{pr_number}: {len(failing)} failing checks analyzed."
    return payload, 1


def fetch_checks(pr_value: str, repo: str, repo_root: Path | None) -> list[dict[str, Any]]:
    fallback_field_sets = [PRIMARY_CHECK_FIELDS, FALLBACK_CHECK_FIELDS]
    index = 0
    result: GhResult | None = None
    seen_field_sets = {tuple(fields) for fields in fallback_field_sets}

    while index < len(fallback_field_sets):
        fields = fallback_field_sets[index]
        result = run_gh_command(
            append_repo_flag(["pr", "checks", pr_value, "--json", ",".join(fields)], repo),
            cwd=repo_root,
        )
        if result.returncode == 0:
            break

        message = (result.stderr or result.stdout or "").strip()
        available_fields = parse_available_fields(message)
        discovered_fields = [field for field in FALLBACK_CHECK_FIELDS if field in available_fields]
        if discovered_fields:
            discovered_tuple = tuple(discovered_fields)
            if discovered_tuple not in seen_field_sets:
                fallback_field_sets.append(discovered_fields)
                seen_field_sets.add(discovered_tuple)
        index += 1

    if result is None or result.returncode != 0:
        message = (result.stderr or result.stdout or "").strip() if result is not None else ""
        if index > 1:
            raise InspectionError(
                "Error: gh pr checks failed and no compatible field list succeeded.",
                1,
            )
        raise InspectionError(message or "Error: gh pr checks failed.", 1)

    try:
        data = json.loads(result.stdout or "[]")
    except json.JSONDecodeError as exc:
        raise InspectionError(f"Error: unable to parse checks JSON: {exc}", 1) from exc
    if not isinstance(data, list):
        raise InspectionError("Error: unexpected checks JSON shape.", 1)
    return data


def is_failing(check: dict[str, Any]) -> bool:
    conclusion = normalize_field(check.get("conclusion"))
    if conclusion in FAILURE_CONCLUSIONS:
        return True
    state = normalize_field(check.get("state") or check.get("status"))
    if state in FAILURE_STATES:
        return True
    bucket = normalize_field(check.get("bucket"))
    return bucket in FAILURE_BUCKETS


def analyze_check(
    check: dict[str, Any],
    *,
    repo: str,
    repo_root: Path | None,
    max_lines: int,
    context: int,
) -> dict[str, Any]:
    url = check.get("detailsUrl") or check.get("link") or ""
    run_id = extract_run_id(url)
    job_id = extract_job_id(url)
    base: dict[str, Any] = {
        "name": check.get("name", ""),
        "detailsUrl": url,
        "runId": run_id,
        "jobId": job_id,
    }

    if run_id is None:
        base["status"] = "external"
        base["note"] = "No GitHub Actions run id detected in details URL."
        return base

    metadata = fetch_run_metadata(run_id, repo, repo_root)
    if metadata is not None:
        base["run"] = metadata

    log_text, log_error, log_status = fetch_check_log(
        run_id=run_id,
        job_id=job_id,
        repo=repo,
        repo_root=repo_root,
    )

    if log_status == "pending":
        base["status"] = "log_pending"
        base["note"] = log_error or "Logs are not available yet."
        return base

    if log_error:
        base["status"] = "log_unavailable"
        base["error"] = log_error
        return base

    base["status"] = "ok"
    base["logSnippet"] = extract_failure_snippet(log_text, max_lines=max_lines, context=context)
    base["logTail"] = tail_lines(log_text, max_lines)
    return base


def extract_run_id(url: str) -> str | None:
    if not url:
        return None
    for pattern in (r"/actions/runs/(\d+)", r"/runs/(\d+)"):
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def extract_job_id(url: str) -> str | None:
    if not url:
        return None
    match = re.search(r"/actions/runs/\d+/job/(\d+)", url)
    if match:
        return match.group(1)
    match = re.search(r"/job/(\d+)", url)
    if match:
        return match.group(1)
    return None


def fetch_run_metadata(run_id: str, repo: str, repo_root: Path | None) -> dict[str, Any] | None:
    result = run_gh_command(
        append_repo_flag(["run", "view", run_id, "--json", ",".join(RUN_METADATA_FIELDS)], repo),
        cwd=repo_root,
    )
    if result.returncode != 0:
        return None
    try:
        data = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    return data


def fetch_check_log(
    *,
    run_id: str,
    job_id: str | None,
    repo: str,
    repo_root: Path | None,
) -> tuple[str, str, str]:
    log_text, log_error = fetch_run_log(run_id, repo, repo_root)
    if not log_error:
        return log_text, "", "ok"

    if is_log_pending_message(log_error) and job_id:
        job_log, job_error = fetch_job_log(job_id, repo, repo_root)
        if job_log:
            return job_log, "", "ok"
        if job_error and is_log_pending_message(job_error):
            return "", job_error, "pending"
        if job_error:
            return "", job_error, "error"
        return "", log_error, "pending"

    if is_log_pending_message(log_error):
        return "", log_error, "pending"
    return "", log_error, "error"


def fetch_run_log(run_id: str, repo: str, repo_root: Path | None) -> tuple[str, str]:
    result = run_gh_command(
        append_repo_flag(["run", "view", run_id, "--log"], repo),
        cwd=repo_root,
    )
    if result.returncode != 0:
        error = (result.stderr or result.stdout or "").strip()
        return "", error or "gh run view failed"
    return result.stdout, ""


def fetch_job_log(job_id: str, repo: str, repo_root: Path | None) -> tuple[str, str]:
    endpoint = f"/repos/{repo}/actions/jobs/{job_id}/logs"
    returncode, stdout_bytes, stderr = run_gh_command_raw(["api", endpoint], cwd=repo_root)
    if returncode != 0:
        message = (stderr or "").strip() or "gh api job logs failed"
        return "", message

    log_text, parse_error = extract_log_from_job_archive(stdout_bytes)
    if parse_error:
        return "", parse_error
    return log_text, ""


def extract_log_from_job_archive(payload: bytes) -> tuple[str, str]:
    if not payload:
        return "", "Job logs endpoint returned empty payload."
    if not zipfile.is_zipfile(io.BytesIO(payload)):
        return payload.decode(errors="replace"), ""

    try:
        with zipfile.ZipFile(io.BytesIO(payload), "r") as archive:
            names = [name for name in archive.namelist() if not name.endswith("/")]
            if not names:
                return "", "Job logs archive contains no files."
            best_text = ""
            for name in names:
                raw = archive.read(name)
                if not raw:
                    continue
                text = raw.decode(errors="replace")
                if len(text) <= len(best_text):
                    continue
                best_text = text
            if not best_text.strip():
                return "", f"Job logs archive is empty or unreadable; entries: {', '.join(names)}"
            return best_text, ""
    except (zipfile.BadZipFile, KeyError, ValueError) as exc:
        return "", f"Unable to parse job log archive: {exc}"


def normalize_field(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def parse_available_fields(message: str) -> list[str]:
    if "Available fields:" not in message:
        return []
    fields: list[str] = []
    in_block = False
    for line in message.splitlines():
        if "Available fields:" in line:
            in_block = True
            _, suffix = line.split(":", 1)
            value = suffix.strip()
            if value:
                fields.extend(field.strip() for field in value.split(",") if field.strip())
            continue
        if not in_block:
            continue
        value = line.strip()
        if not value or value.startswith("Available fields:"):
            continue
        fields.append(value)
    return fields


def is_log_pending_message(message: str) -> bool:
    lowered = message.lower()
    return any(marker in lowered for marker in PENDING_LOG_MARKERS)


def extract_failure_snippet(log_text: str, max_lines: int, context: int) -> str:
    lines = log_text.splitlines()
    if not lines:
        return ""
    marker_index = find_failure_index(lines)
    if marker_index is None:
        return "\n".join(lines[-max_lines:])

    start = max(0, marker_index - context)
    end = min(len(lines), marker_index + context + 1)
    window = lines[start:end]
    if len(window) > max_lines:
        window = window[-max_lines:]
    return "\n".join(window)


def find_failure_index(lines: Sequence[str]) -> int | None:
    for index in range(len(lines) - 1, -1, -1):
        lowered = lines[index].lower()
        if any(marker in lowered for marker in FAILURE_MARKERS):
            return index
    return None


def tail_lines(text: str, max_lines: int) -> str:
    if max_lines <= 0:
        return ""
    lines = text.splitlines()
    return "\n".join(lines[-max_lines:])


def render_results(payload: dict[str, Any]) -> str:
    repo = str(payload.get("repo") or "")
    pr = str(payload.get("pr") or "")
    results = list(payload.get("results") or [])
    if not results:
        return f"PR #{pr} in {repo}: no failing checks detected.\n"

    lines = [f"PR #{pr} in {repo}: {len(results)} failing checks analyzed."]
    for result in results:
        lines.append("-" * 60)
        lines.append(f"Check: {result.get('name', '')}")
        if result.get("detailsUrl"):
            lines.append(f"Details: {result['detailsUrl']}")
        if result.get("status"):
            lines.append(f"Status: {result['status']}")
        run_meta = result.get("run", {})
        if run_meta.get("url"):
            lines.append(f"Run URL: {run_meta['url']}")
        if result.get("jobId"):
            lines.append(f"Job ID: {result['jobId']}")
        if result.get("note"):
            lines.append(f"Note: {result['note']}")
        if result.get("error"):
            lines.append(f"Error fetching logs: {result['error']}")
            continue
        snippet = result.get("logSnippet") or ""
        if snippet:
            lines.append("Failure snippet:")
            lines.append(indent_block(snippet))
        else:
            lines.append("No snippet available.")
    lines.append("-" * 60)
    return "\n".join(lines) + "\n"


def indent_block(text: str, prefix: str = "  ") -> str:
    return "\n".join(f"{prefix}{line}" for line in text.splitlines())


if __name__ == "__main__":
    raise SystemExit(main())
