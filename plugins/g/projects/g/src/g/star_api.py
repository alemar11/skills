from __future__ import annotations

import json
import subprocess
from collections.abc import Iterable

from .repository import is_repo_reference


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
    payload = _run_gh_json(cmd)
    if isinstance(payload, dict) and payload.get("errors"):
        raise GhError("GitHub returned GraphQL errors; membership state is unverified.")
    return payload


def repo_view(repo: str) -> dict[str, object]:
    validate_repo_reference(repo)
    payload = _run_gh_json(
        ["gh", "repo", "view", repo, "--json", "id,nameWithOwner,viewerHasStarred,url"]
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
    if not is_repo_reference(value):
        raise GhError(f"Invalid repository reference '{repo}'. Use owner/repo.", 64)
    return value


def collect_repo_targets(
    repos: Iterable[str], repo_file: str | None = None
) -> list[str]:
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
            raise GhError(
                f"Failed to read repos file '{repo_file}': {exc.strerror or exc}", 66
            ) from exc

    return ordered


def _next_cursor(page_info: object, seen: set[str]) -> str | None:
    if not isinstance(page_info, dict) or not isinstance(page_info.get("hasNextPage"), bool):
        raise GhError("Missing pagination evidence; membership state is unverified.")
    if not page_info["hasNextPage"]:
        return None
    cursor = page_info.get("endCursor")
    if not isinstance(cursor, str) or not cursor or cursor in seen:
        raise GhError("Incomplete pagination; membership state is unverified.")
    seen.add(cursor)
    return cursor


def _collection_page(
    connection: object, expected_count: int | None, seen_ids: set[str],
    *, repository_items: bool = False,
) -> tuple[int, list[dict[str, object]]]:
    if not isinstance(connection, dict):
        raise GhError("Unreadable collection; membership state is unverified.")
    count = connection.get("totalCount")
    nodes = connection.get("nodes")
    if type(count) is not int or count < 0 or not isinstance(nodes, list):
        raise GhError("Invalid collection shape; membership state is unverified.")
    if expected_count is not None and count != expected_count:
        raise GhError("Collection changed during pagination; membership state is unverified.")
    for node in nodes:
        if not isinstance(node, dict):
            raise GhError("Unreadable collection item; membership state is unverified.")
        identity = node.get("id")
        if not isinstance(identity, str) or not identity.strip() or identity in seen_ids:
            raise GhError("Missing or duplicate item identity; membership state is unverified.")
        if repository_items and node.get("__typename") != "Repository":
            raise GhError("Unrecognized list item; membership state is unverified.")
        seen_ids.add(identity)
    if len(seen_ids) > count:
        raise GhError("Collection count mismatch; membership state is unverified.")
    return count, nodes


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
          pageInfo { hasNextPage endCursor }
        }
      }
    }
    """
    items: list[dict[str, object]] = []
    cursor: str | None = None
    seen_cursors: set[str] = set()
    total_count: int | None = None
    seen_ids: set[str] = set()
    while True:
        payload = graphql(
            query,
            {
                "first": _page_size(limit - len(items) if limit > 0 else 0),
                "after": cursor,
            },
        )
        try:
            lists = payload["data"]["viewer"]["lists"]
        except (TypeError, KeyError) as exc:
            raise GhError("Unexpected viewer lists response shape.") from exc
        total_count, nodes = _collection_page(lists, total_count, seen_ids)
        for node in nodes:
            items.append(node)
            if limit > 0 and len(items) >= limit:
                return {"totalCount": total_count, "items": items}
        cursor = _next_cursor(lists.get("pageInfo"), seen_cursors)
        if cursor is None:
            if len(items) != total_count:
                raise GhError("Incomplete collection; membership state is unverified.")
            break
    return {"totalCount": total_count, "items": items}


def resolve_list(
    *, list_id: str | None = None, selector: str | None = None
) -> dict[str, object]:
    if list_id:
        query = """
        query($id: ID!) {
          node(id: $id) {
            __typename
            ... on UserList {
              id name slug description isPrivate createdAt updatedAt lastAddedAt
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
          id name slug description isPrivate createdAt updatedAt lastAddedAt
          items(first: $first, after: $after) {
            totalCount
            nodes {
              __typename
              ... on Repository { id nameWithOwner url viewerHasStarred }
            }
            pageInfo { hasNextPage endCursor }
          }
        }
      }
    }
    """
    items: list[dict[str, object]] = []
    cursor: str | None = None
    seen_cursors: set[str] = set()
    metadata: dict[str, object] | None = None
    total_count: int | None = None
    seen_ids: set[str] = set()
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
        if node.get("id") != list_id:
            raise GhError("List identity mismatch; membership state is unverified.")
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
        item_connection = node.get("items")
        total_count, nodes = _collection_page(
            item_connection, total_count, seen_ids, repository_items=True
        )
        for entry in nodes:
            cleaned = dict(entry)
            cleaned.pop("__typename", None)
            items.append(cleaned)
            if limit > 0 and len(items) >= limit:
                metadata["totalCount"] = total_count
                metadata["items"] = items
                return metadata
        cursor = _next_cursor(item_connection.get("pageInfo"), seen_cursors)
        if cursor is None:
            if len(items) != total_count:
                raise GhError("Incomplete collection; membership state is unverified.")
            break
    if metadata is None:
        raise GhError(f"List id '{list_id}' was not found.", 66)
    metadata["totalCount"] = total_count
    metadata["items"] = items
    return metadata


def repo_memberships(repo_ids: Iterable[str]) -> dict[str, list[dict[str, object]]]:
    targets = [repo_id for repo_id in repo_ids if repo_id]
    memberships: dict[str, list[dict[str, object]]] = {
        repo_id: [] for repo_id in targets
    }
    if not targets:
        return memberships
    for user_list in viewer_lists(0)["items"]:
        list_id = user_list["id"]
        payload = list_items(list_id, 0)
        list_summary = {
            "id": payload.get("id"),
            "name": payload.get("name"),
            "slug": payload.get("slug"),
        }
        for item in payload["items"]:
            repo_id = item["id"]
            if repo_id in memberships:
                memberships[repo_id].append(list_summary)
    return memberships
