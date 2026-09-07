from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from . import __version__
from . import attachment, reviews, stack, stars
from .common import GError, envelope, error_envelope, resolve_pr, resolve_repo
from .delivery_status import inspect_delivery_status
from .health import doctor, doctor_text
from .provider_text import worktree_snapshot
from .publish import open_pr, preflight


class Parser(argparse.ArgumentParser):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("allow_abbrev", False)
        super().__init__(*args, **kwargs)

    def error(self, message: str) -> None:
        raise GError("Invalid command arguments.", code="invalid_arguments", exit_code=64)


def parser() -> Parser:
    root = Parser(prog="g", description="Safe local Git and GitHub workflow mechanics for G skills.")
    root.add_argument("--version", action="version", version=__version__)
    root.add_argument("--json", action="store_true", help="Emit a stable JSON envelope.")
    commands = root.add_subparsers(dest="domain")
    commands.add_parser("doctor", help="Check Python, git, gh, authentication, and checkout readiness.")
    repo = commands.add_parser("repo", help="Resolve repository identity.")
    repo_sub = repo.add_subparsers(dest="verb", required=True)
    repo_resolve = repo_sub.add_parser("resolve", help="Resolve owner/repo from an argument or origin.")
    repo_resolve.add_argument("--repo")
    repo_sub.add_parser("snapshot", help="Fingerprint the current Git HEAD and porcelain worktree state.")
    attachment_parser = commands.add_parser(
        "attachment",
        help="Upload files for publication in GitHub issue or pull request content.",
    )
    attachment_sub = attachment_parser.add_subparsers(dest="verb", required=True)
    attachment_upload = attachment_sub.add_parser(
        "upload",
        help="Upload one local file and return its stable GitHub attachment URL.",
    )
    attachment_upload.add_argument("--repo", required=True)
    attachment_upload.add_argument("--file", required=True)
    attachment_upload.add_argument("--name")
    attachment_upload.add_argument("--content-type")
    attachment_upload.add_argument("--dry-run", action="store_true")
    pr = commands.add_parser("pr", help="Resolve pull request context.")
    pr_sub = pr.add_subparsers(dest="verb", required=True)
    pr_resolve = pr_sub.add_parser("resolve", help="Resolve a PR number/URL or current-branch PR.")
    pr_resolve.add_argument("--repo")
    pr_resolve.add_argument("--pr")
    pr_delivery = pr_sub.add_parser("delivery-status", help="Inspect exact-head GitHub delivery readiness read-only.")
    pr_delivery.add_argument("--repo", required=True)
    pr_delivery.add_argument("--pr", required=True, type=int)
    pr_delivery.add_argument("--expected-head")
    reviews_parser = commands.add_parser("reviews", help="Inspect, check, wait for, or respond to PR reviews.")
    reviews_parser.add_argument("args", nargs=argparse.REMAINDER)
    stars_parser = commands.add_parser("stars", help="Manage stars and authenticated-user star lists.")
    stars_parser.add_argument("args", nargs=argparse.REMAINDER)
    stack_parser = commands.add_parser("stack", help="Wrap the GitHub gh-stack extension.")
    stack_sub = stack_parser.add_subparsers(dest="verb", required=True)
    stack_ensure = stack_sub.add_parser("ensure", help="Check or explicitly install github/gh-stack.")
    stack_ensure.add_argument("--install", action="store_true", help="Install the official extension when it is missing.")
    for command in stack.STACK_COMMANDS:
        stack_command = stack_sub.add_parser(command, help=f"Run gh stack {command} without interactive prompts.")
        stack_command.add_argument("args", nargs=argparse.REMAINDER)
    stack_raw = stack_sub.add_parser("raw", help="Run a non-interactive upstream gh stack command.")
    stack_raw.add_argument("args", nargs=argparse.REMAINDER)
    publish = commands.add_parser("publish", help="Preflight and open draft pull requests.")
    publish_sub = publish.add_subparsers(dest="verb", required=True)
    publish_preflight = publish_sub.add_parser("preflight")
    publish_preflight.add_argument("--repo")
    publish_open = publish_sub.add_parser("open")
    publish_open.add_argument("--repo")
    publish_open.add_argument("--title-file", required=True)
    publish_open.add_argument("--body-file", required=True)
    publish_open.add_argument("--base")
    publish_open.add_argument("--draft", action="store_true", default=True)
    publish_open.add_argument("--dry-run", action="store_true")
    publish_open.add_argument("--expected-worktree-fingerprint")
    return root


def _forward(module: Any, args: list[str], json_mode: bool, expected: str) -> int:
    forwarded = list(args)
    if forwarded and forwarded[0] == expected:
        forwarded.pop(0)
    if json_mode:
        forwarded.insert(0, "--json")
    return int(module.main(forwarded))


def _emit(data: object, command: list[str], json_mode: bool) -> None:
    if json_mode:
        print(json.dumps(envelope(command, data), indent=2))
    else:
        print(json.dumps(data, indent=2))


def _json_option_index(argv: list[str]) -> int | None:
    """Find the wrapper-level --json without consuming raw upstream flags."""

    raw_separator: int | None = None
    for index in range(len(argv) - 2):
        if argv[index : index + 2] == ["stack", "raw"]:
            try:
                raw_separator = argv.index("--", index + 2)
            except ValueError:
                pass
            break

    for index, argument in enumerate(argv):
        if argument != "--json":
            continue
        if raw_separator is not None and index > raw_separator:
            continue
        return index
    return None


def _normalize_stack_passthrough(argv: list[str]) -> list[str]:
    """Keep option-like gh-stack arguments inside the stack subparser."""

    if len(argv) >= 2 and argv[0] == "--json" and argv[1] == "stack":
        stack_index = 1
    elif argv and argv[0] == "stack":
        stack_index = 0
    else:
        return argv

    verb_index = stack_index + 1
    if verb_index >= len(argv) or argv[verb_index] not in stack.STACK_COMMANDS:
        return argv

    args_index = verb_index + 1
    if args_index >= len(argv) or argv[args_index] == "--":
        return argv
    return [*argv[:args_index], "--", *argv[args_index:]]


def main(argv: list[str] | None = None) -> int:
    raw = list(argv if argv is not None else sys.argv[1:])
    if raw == ["--version"]:
        print(__version__)
        return 0
    json_index = _json_option_index(raw)
    json_mode = json_index is not None
    if json_mode and json_index is not None:
        raw.pop(json_index)
        raw.insert(0, "--json")
    raw = _normalize_stack_passthrough(raw)
    try:
        args = parser().parse_args(raw)
        if args.domain is None:
            parser().print_help()
            return 0
        if args.domain == "doctor":
            payload = doctor()
            print(json.dumps(payload, indent=2) if args.json else doctor_text(payload))
            return 0 if payload["ok"] else 1
        if args.domain == "repo":
            data = resolve_repo(args.repo) if args.verb == "resolve" else worktree_snapshot()
            _emit(data, ["repo", args.verb], args.json)
            return 0
        if args.domain == "attachment":
            data = attachment.upload(
                repo=args.repo,
                file=args.file,
                name=args.name,
                content_type=args.content_type,
                dry_run=args.dry_run,
            )
            _emit(data, ["attachment", args.verb], args.json)
            return 0
        if args.domain == "pr":
            if args.verb == "resolve":
                data = resolve_pr(args.repo, args.pr)
            else:
                data = inspect_delivery_status(args.repo, args.pr, args.expected_head)
            _emit(data, ["pr", args.verb], args.json)
            return 0
        if args.domain == "reviews":
            return _forward(reviews, args.args, args.json, "")
        if args.domain == "stars":
            return _forward(stars, args.args, args.json, "")
        if args.domain == "stack" and args.verb == "ensure":
            data = stack.ensure(install=args.install, json_mode=args.json)
            _emit(data, ["stack", "ensure"], args.json)
            return 0
        if args.domain == "stack" and args.verb == "raw":
            return stack.execute_raw(args.args, json_mode=args.json)
        if args.domain == "stack":
            forwarded = list(args.args)
            if forwarded and forwarded[0] == "--":
                forwarded.pop(0)
            return stack.execute(args.verb, forwarded, json_mode=args.json)
        if args.domain == "publish" and args.verb == "preflight":
            data = preflight(args.repo)
        elif args.domain == "publish" and args.verb == "open":
            data = open_pr(
                repo=args.repo,
                title_file=args.title_file,
                body_file=args.body_file,
                draft=args.draft,
                base=args.base,
                dry_run=args.dry_run,
                expected_worktree_fingerprint=args.expected_worktree_fingerprint,
            )
        else:
            raise GError("Unsupported command.", code="invalid_arguments", exit_code=64)
        _emit(data, ["publish", args.verb], args.json)
        return 0
    except GError as exc:
        command = [item for item in raw if not item.startswith("-")][:2]
        if json_mode:
            print(json.dumps(error_envelope(command, exc), indent=2))
        else:
            print(str(exc), file=sys.stderr)
        return exc.exit_code
if __name__ == "__main__":
    raise SystemExit(main())
