#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Iterable

REPO_PATTERN = re.compile(r"^[^/\s]+/[^/\s]+$")


class GhError(RuntimeError):
    def __init__(self, message: str, returncode: int = 1) -> None:
        super().__init__(message)
        self.returncode = returncode


def _run_gh_json(args: list[str]) -> object:
    proc = subprocess.run(args, text=True, capture_output=True)
    if proc.returncode != 0:
        message = (proc.stderr or proc.stdout or "").strip() or "gh command failed"
        raise GhError(message, proc.returncode)
    try:
        return json.loads(proc.stdout or "null")
    except json.JSONDecodeError as exc:
        raise GhError(f"Failed to parse gh output: {exc}") from exc


def graphql(query: str, variables: dict[str, object] | None = None) -> object:
    cmd = ["gh", "api", "graphql", "-f", f"query={query}"]
    for key, value in (variables or {}).items():
        if isinstance(value, list):
            if not value:
                cmd.extend(["-F", f"{key}[]"])
            else:
                for item in value:
                    cmd.extend(["-F", f"{key}[]={item}"])
        elif value is None:
            cmd.extend(["-F", f"{key}=null"])
        elif isinstance(value, bool):
            cmd.extend(["-F", f"{key}={'true' if value else 'false'}"])
        else:
            cmd.extend(["-F", f"{key}={value}"])
    return _run_gh_json(cmd)


def repo_view(repo: str) -> dict[str, object]:
    validate_repo_reference(repo)
    payload = _run_gh_json(
        [
            "gh",
            "repo",
            "view",
            repo,
            "--json",
            "id,nameWithOwner,viewerHasStarred,url",
        ]
    )
    if not isinstance(payload, dict):
        raise GhError("Unexpected repo view response shape.")
    return payload


def _page_size(limit: int, default: int = 100) -> int:
    if limit <= 0:
        return default
    return min(limit, default)


def validate_repo_reference(repo: str) -> str:
    value = repo.strip()
    if not REPO_PATTERN.match(value):
        raise GhError(f"Invalid repository reference '{repo}'. Use owner/repo.", 64)
    return value


def collect_repo_targets(repos: Iterable[str], repo_file: str | None = None) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []

    def add(repo: str) -> None:
        normalized = validate_repo_reference(repo)
        if normalized not in seen:
            seen.add(normalized)
            ordered.append(normalized)

    for repo in repos:
        if repo.strip():
            add(repo)

    if repo_file:
        try:
            with open(repo_file, "r", encoding="utf-8") as handle:
                for raw_line in handle:
                    line = raw_line.strip()
                    if not line or line.startswith("#"):
                        continue
                    add(line)
        except OSError as exc:
            raise GhError(f"Failed to read repos file '{repo_file}': {exc.strerror or exc}", 66) from exc

    return ordered


def viewer_lists(limit: int = 0) -> dict[str, object]:
    query = """
    query($first: Int!, $after: String) {
      viewer {
        lists(first: $first, after: $after) {
          totalCount
          nodes {
            id
            name
            slug
            description
            isPrivate
            createdAt
            updatedAt
            lastAddedAt
          }
          pageInfo {
            hasNextPage
            endCursor
          }
        }
      }
    }
    """
    items: list[dict[str, object]] = []
    cursor: str | None = None
    total_count = 0
    while True:
        payload = graphql(
            query,
            {"first": _page_size(limit - len(items) if limit > 0 else 0), "after": cursor},
        )
        try:
            lists = payload["data"]["viewer"]["lists"]
        except (TypeError, KeyError) as exc:
            raise GhError("Unexpected viewer lists response shape.") from exc
        total_count = int(lists.get("totalCount") or 0)
        nodes = lists.get("nodes") or []
        for node in nodes:
            if isinstance(node, dict):
                items.append(node)
                if limit > 0 and len(items) >= limit:
                    return {"totalCount": total_count, "items": items}
        page_info = lists.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")
        if not cursor:
            break
    return {"totalCount": total_count, "items": items}


def resolve_list(*, list_id: str | None = None, selector: str | None = None) -> dict[str, object]:
    if list_id:
        query = """
        query($id: ID!) {
          node(id: $id) {
            __typename
            ... on UserList {
              id
              name
              slug
              description
              isPrivate
              createdAt
              updatedAt
              lastAddedAt
            }
          }
        }
        """
        payload = graphql(query, {"id": list_id})
        try:
            node = payload["data"]["node"]
        except (TypeError, KeyError) as exc:
            raise GhError("Unexpected list lookup response shape.") from exc
        if not isinstance(node, dict) or node.get("__typename") != "UserList":
            raise GhError(f"List id '{list_id}' was not found.", 66)
        node = dict(node)
        node.pop("__typename", None)
        return node

    if not selector:
        raise GhError("A list selector is required.", 64)

    all_lists = viewer_lists(0).get("items") or []
    slug_matches = [item for item in all_lists if item.get("slug") == selector]
    if len(slug_matches) == 1:
        return slug_matches[0]
    if len(slug_matches) > 1:
        raise GhError(
            f"List selector '{selector}' matched multiple list slugs. Use --list-id.",
            65,
        )

    name_matches = [item for item in all_lists if item.get("name") == selector]
    if len(name_matches) == 1:
        return name_matches[0]
    if len(name_matches) > 1:
        raise GhError(
            f"List selector '{selector}' matched multiple list names. Use --list-id.",
            65,
        )

    raise GhError(f"List selector '{selector}' was not found.", 66)


def list_items(list_id: str, limit: int = 0) -> dict[str, object]:
    query = """
    query($id: ID!, $first: Int!, $after: String) {
      node(id: $id) {
        __typename
        ... on UserList {
          id
          name
          slug
          description
          isPrivate
          createdAt
          updatedAt
          lastAddedAt
          items(first: $first, after: $after) {
            totalCount
            nodes {
              __typename
              ... on Repository {
                id
                nameWithOwner
                url
                viewerHasStarred
              }
            }
            pageInfo {
              hasNextPage
              endCursor
            }
          }
        }
      }
    }
    """
    items: list[dict[str, object]] = []
    cursor: str | None = None
    metadata: dict[str, object] | None = None
    total_count = 0
    while True:
        payload = graphql(
            query,
            {
                "id": list_id,
                "first": _page_size(limit - len(items) if limit > 0 else 0),
                "after": cursor,
            },
        )
        try:
            node = payload["data"]["node"]
        except (TypeError, KeyError) as exc:
            raise GhError("Unexpected list items response shape.") from exc
        if not isinstance(node, dict) or node.get("__typename") != "UserList":
            raise GhError(f"List id '{list_id}' was not found.", 66)
        metadata = {
            "id": node.get("id"),
            "name": node.get("name"),
            "slug": node.get("slug"),
            "description": node.get("description"),
            "isPrivate": bool(node.get("isPrivate")),
            "createdAt": node.get("createdAt"),
            "updatedAt": node.get("updatedAt"),
            "lastAddedAt": node.get("lastAddedAt"),
        }
        item_connection = node.get("items") or {}
        total_count = int(item_connection.get("totalCount") or 0)
        for entry in item_connection.get("nodes") or []:
            if isinstance(entry, dict) and entry.get("__typename") == "Repository":
                cleaned = dict(entry)
                cleaned.pop("__typename", None)
                items.append(cleaned)
                if limit > 0 and len(items) >= limit:
                    metadata["totalCount"] = total_count
                    metadata["items"] = items
                    return metadata
        page_info = item_connection.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")
        if not cursor:
            break
    if metadata is None:
        raise GhError(f"List id '{list_id}' was not found.", 66)
    metadata["totalCount"] = total_count
    metadata["items"] = items
    return metadata


def viewer_stars(limit: int = 0) -> dict[str, object]:
    query = """
    query($first: Int!, $after: String) {
      viewer {
        starredRepositories(
          first: $first
          after: $after
          orderBy: {field: STARRED_AT, direction: DESC}
        ) {
          totalCount
          nodes {
            id
            nameWithOwner
            url
            viewerHasStarred
          }
          pageInfo {
            hasNextPage
            endCursor
          }
        }
      }
    }
    """
    items: list[dict[str, object]] = []
    cursor: str | None = None
    total_count = 0
    while True:
        payload = graphql(
            query,
            {"first": _page_size(limit - len(items) if limit > 0 else 0), "after": cursor},
        )
        try:
            connection = payload["data"]["viewer"]["starredRepositories"]
        except (TypeError, KeyError) as exc:
            raise GhError("Unexpected starred repositories response shape.") from exc
        total_count = int(connection.get("totalCount") or 0)
        for node in connection.get("nodes") or []:
            if isinstance(node, dict):
                items.append(node)
                if limit > 0 and len(items) >= limit:
                    return {"totalCount": total_count, "items": items}
        page_info = connection.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")
        if not cursor:
            break
    return {"totalCount": total_count, "items": items}


def repo_memberships(repo_ids: Iterable[str]) -> dict[str, list[dict[str, object]]]:
    targets = [repo_id for repo_id in repo_ids if repo_id]
    memberships: dict[str, list[dict[str, object]]] = {repo_id: [] for repo_id in targets}
    if not targets:
        return memberships

    for user_list in viewer_lists(0).get("items") or []:
        list_id = user_list.get("id")
        if not isinstance(list_id, str) or not list_id:
            continue
        payload = list_items(list_id, 0)
        list_summary = {
            "id": payload.get("id"),
            "name": payload.get("name"),
            "slug": payload.get("slug"),
        }
        for item in payload.get("items") or []:
            if not isinstance(item, dict):
                continue
            repo_id = item.get("id")
            if isinstance(repo_id, str) and repo_id in memberships:
                memberships[repo_id].append(list_summary)
    return memberships


def _emit(payload: object) -> int:
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Shared GitHub user-state helpers.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    viewer_stars_parser = subparsers.add_parser("viewer-stars")
    viewer_stars_parser.add_argument("--limit", type=int, default=0)

    viewer_lists_parser = subparsers.add_parser("viewer-lists")
    viewer_lists_parser.add_argument("--limit", type=int, default=0)

    resolve_list_parser = subparsers.add_parser("resolve-list")
    resolve_list_parser.add_argument("--list")
    resolve_list_parser.add_argument("--list-id")

    list_items_parser = subparsers.add_parser("list-items")
    list_items_parser.add_argument("--list-id", required=True)
    list_items_parser.add_argument("--limit", type=int, default=0)

    repo_memberships_parser = subparsers.add_parser("repo-memberships")
    repo_memberships_parser.add_argument("--repo-id", action="append", default=[])

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "viewer-stars":
            return _emit(viewer_stars(limit=max(args.limit, 0)))
        if args.command == "viewer-lists":
            return _emit(viewer_lists(limit=max(args.limit, 0)))
        if args.command == "resolve-list":
            if bool(args.list) == bool(args.list_id):
                raise GhError("Pass exactly one of --list or --list-id.", 64)
            return _emit(resolve_list(list_id=args.list_id, selector=args.list))
        if args.command == "list-items":
            return _emit(list_items(args.list_id, limit=max(args.limit, 0)))
        if args.command == "repo-memberships":
            return _emit(repo_memberships(args.repo_id))
    except GhError as exc:
        print(str(exc), file=sys.stderr)
        return exc.returncode
    raise GhError(f"Unsupported command: {args.command}", 64)


if __name__ == "__main__":
    raise SystemExit(main())
