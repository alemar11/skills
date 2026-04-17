#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from .user_state import (
    GhError,
    collect_repo_targets,
    graphql,
    list_items,
    repo_view,
    resolve_list,
    viewer_stars,
)


def _positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("Use a positive integer.")
    return number


def _mutate_star(repo_id: str, add: bool) -> None:
    action = "addStar" if add else "removeStar"
    query = f"""
    mutation($starrableId: ID!) {{
      {action}(input: {{starrableId: $starrableId}}) {{
        starrable {{
          __typename
          ... on Repository {{
            id
          }}
        }}
      }}
    }}
    """
    graphql(query, {"starrableId": repo_id})


def _emit(payload: object) -> int:
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


def _print_read_text(payload: dict[str, object]) -> int:
    source = payload.get("source")
    items = payload.get("items") or []
    if source == "list":
        list_payload = payload.get("list") or {}
        visibility = "private" if list_payload.get("isPrivate") else "public"
        print(
            f"Starred repositories in list: {list_payload.get('name')} ({list_payload.get('slug')})"
        )
        print(f"Visibility: {visibility}")
        print(f"Total: {payload.get('totalCount', 0)}")
        print(f"Shown: {len(items)}")
    else:
        print("Starred repositories")
        print(f"Total: {payload.get('totalCount', 0)}")
        print(f"Shown: {len(items)}")
    for item in items:
        if isinstance(item, dict):
            print(f"- {item.get('nameWithOwner')}")
    return 0


def _print_write_text(payload: dict[str, object]) -> int:
    print(f"Action: {payload.get('action')}")
    print(f"Targets: {payload.get('targetCount')}")
    print(f"Succeeded: {payload.get('successCount')}")
    print(f"Failed: {payload.get('failureCount')}")
    for item in payload.get("results") or []:
        if not isinstance(item, dict):
            continue
        message = item.get("message") or item.get("status")
        print(f"- {item.get('repo')}: {message}")
    return 0


def _run_list_stars(args: argparse.Namespace) -> int:
    limit = 0 if args.all else args.limit
    if args.list_id or args.by_list:
        selected_list = resolve_list(list_id=args.list_id, selector=args.by_list)
        list_payload = list_items(str(selected_list["id"]), limit=limit)
        payload = {
            "mode": "list-stars",
            "source": "list",
            "list": {
                "id": list_payload.get("id"),
                "name": list_payload.get("name"),
                "slug": list_payload.get("slug"),
                "description": list_payload.get("description"),
                "isPrivate": list_payload.get("isPrivate"),
            },
            "totalCount": list_payload.get("totalCount", 0),
            "items": list_payload.get("items") or [],
        }
    else:
        stars = viewer_stars(limit=limit)
        payload = {
            "mode": "list-stars",
            "source": "stars",
            "totalCount": stars.get("totalCount", 0),
            "items": stars.get("items") or [],
        }

    if args.json:
        return _emit(payload)
    return _print_read_text(payload)


def _run_write(args: argparse.Namespace, add: bool) -> int:
    repos = collect_repo_targets(args.repo or [], args.repos_file)
    if not repos:
        raise GhError("At least one target repository is required.", 64)

    results: list[dict[str, object]] = []
    failure_count = 0

    for repo in repos:
        result: dict[str, object] = {"repo": repo}
        try:
            repo_payload = repo_view(repo)
            repo_id = str(repo_payload["id"])
            canonical_repo = str(repo_payload["nameWithOwner"])
            already_starred = bool(repo_payload.get("viewerHasStarred"))
            result["repo"] = canonical_repo
            result["url"] = repo_payload.get("url")
            result["wasStarred"] = already_starred

            if add:
                if already_starred:
                    result["status"] = "noop"
                    result["message"] = "already starred"
                elif args.dry_run:
                    result["status"] = "dry-run"
                    result["message"] = "would star"
                else:
                    _mutate_star(repo_id, add=True)
                    result["status"] = "changed"
                    result["message"] = "starred"
            else:
                if not already_starred:
                    result["status"] = "noop"
                    result["message"] = "already unstarred"
                elif args.dry_run:
                    result["status"] = "dry-run"
                    result["message"] = "would unstar"
                else:
                    _mutate_star(repo_id, add=False)
                    result["status"] = "changed"
                    result["message"] = "unstarred"
        except GhError as exc:
            failure_count += 1
            result["status"] = "error"
            result["message"] = str(exc)
        results.append(result)

    payload = {
        "action": "star" if add else "unstar",
        "targetCount": len(repos),
        "successCount": len(repos) - failure_count,
        "failureCount": failure_count,
        "results": results,
    }
    if args.json:
        _emit(payload)
    else:
        _print_write_text(payload)
    return 1 if failure_count else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="List, star, or unstar repositories for the authenticated GitHub account."
    )
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument("--list-stars", action="store_true")
    action_group.add_argument("--star", action="store_true")
    action_group.add_argument("--unstar", action="store_true")

    parser.add_argument("--repo", action="append", default=[], help="Repository in owner/repo format.")
    parser.add_argument("--repos-file", help="Newline-delimited file of owner/repo entries.")
    parser.add_argument("--by-list", help="Exact list slug or exact list name.")
    parser.add_argument("--list-id", help="Exact GitHub user list id.")
    parser.add_argument("--limit", type=_positive_int, default=100, help="Maximum number of items to return.")
    parser.add_argument("--all", action="store_true", help="Fetch all available items for read actions.")
    parser.add_argument("--json", action="store_true", help="Emit normalized JSON output.")
    parser.add_argument("--dry-run", action="store_true", help="Preview write actions without mutating GitHub.")
    return parser


def _validate_args(args: argparse.Namespace) -> None:
    if args.list_stars:
        if args.repo or args.repos_file:
            raise GhError("--list-stars does not accept --repo or --repos-file.", 64)
        if args.by_list and args.list_id:
            raise GhError("Pass either --by-list or --list-id, not both.", 64)
        return

    if args.by_list or args.list_id:
        raise GhError("--star and --unstar do not accept list filters.", 64)
    if args.all:
        raise GhError("--all is only valid with --list-stars.", 64)
    if args.limit != 100:
        raise GhError("--limit is only valid with --list-stars.", 64)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        _validate_args(args)
        if args.list_stars:
            return _run_list_stars(args)
        if args.star:
            return _run_write(args, add=True)
        return _run_write(args, add=False)
    except GhError as exc:
        print(str(exc), file=sys.stderr)
        return exc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
