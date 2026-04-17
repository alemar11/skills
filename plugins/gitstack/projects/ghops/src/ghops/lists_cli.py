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
    repo_memberships,
    repo_view,
    resolve_list,
    viewer_lists,
)


def _positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("Use a positive integer.")
    return number


def _emit(payload: object) -> int:
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


def _print_list_summaries(payload: dict[str, object]) -> int:
    print("GitHub star lists")
    print(f"Total: {payload.get('totalCount', 0)}")
    print(f"Shown: {len(payload.get('items') or [])}")
    for item in payload.get("items") or []:
        if not isinstance(item, dict):
            continue
        visibility = "private" if item.get("isPrivate") else "public"
        print(
            f"- {item.get('name')} ({item.get('slug')}) {visibility} items={item.get('itemCount', 'unknown')}"
        )
    return 0


def _print_list_items(payload: dict[str, object]) -> int:
    list_payload = payload.get("list") or {}
    visibility = "private" if list_payload.get("isPrivate") else "public"
    print(f"List items: {list_payload.get('name')} ({list_payload.get('slug')})")
    print(f"Visibility: {visibility}")
    print(f"Total: {payload.get('totalCount', 0)}")
    print(f"Shown: {len(payload.get('items') or [])}")
    for item in payload.get("items") or []:
        if isinstance(item, dict):
            print(f"- {item.get('nameWithOwner')}")
    return 0


def _print_mutation(payload: dict[str, object]) -> int:
    print(f"Action: {payload.get('action')}")
    status = payload.get("status")
    if status:
        print(f"Status: {status}")
    list_payload = payload.get("list")
    if isinstance(list_payload, dict):
        visibility = "private" if list_payload.get("isPrivate") else "public"
        slug = list_payload.get("slug")
        if slug:
            print(f"List: {list_payload.get('name')} ({slug}) [{visibility}]")
        else:
            print(f"List: {list_payload.get('name')} [{visibility}]")
    if "targetCount" in payload:
        print(f"Targets: {payload.get('targetCount')}")
        print(f"Succeeded: {payload.get('successCount')}")
        print(f"Failed: {payload.get('failureCount')}")
        for item in payload.get("results") or []:
            if not isinstance(item, dict):
                continue
            message = item.get("message") or item.get("status")
            print(f"- {item.get('repo')}: {message}")
    return 0


def _create_list(name: str, description: str | None, is_private: bool) -> dict[str, object]:
    query = """
    mutation($name: String!, $description: String, $isPrivate: Boolean) {
      createUserList(
        input: {name: $name, description: $description, isPrivate: $isPrivate}
      ) {
        list {
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
    payload = graphql(
        query,
        {"name": name, "description": description, "isPrivate": is_private},
    )
    try:
        created_list = payload["data"]["createUserList"]["list"]
    except (TypeError, KeyError) as exc:
        raise GhError("Unexpected create list response shape.") from exc
    if not isinstance(created_list, dict):
        raise GhError("GitHub did not return the created list.")
    return created_list


def _delete_list(list_id: str) -> None:
    query = """
    mutation($listId: ID!) {
      deleteUserList(input: {listId: $listId}) {
        user {
          login
        }
      }
    }
    """
    graphql(query, {"listId": list_id})


def _update_list_memberships(repo_id: str, desired_list_ids: list[str]) -> list[dict[str, object]]:
    query = """
    mutation($itemId: ID!, $listIds: [ID!]!) {
      updateUserListsForItem(input: {itemId: $itemId, listIds: $listIds}) {
        lists {
          id
          name
          slug
        }
      }
    }
    """
    payload = graphql(query, {"itemId": repo_id, "listIds": desired_list_ids})
    try:
        lists_payload = payload["data"]["updateUserListsForItem"]["lists"]
    except (TypeError, KeyError) as exc:
        raise GhError("Unexpected update list memberships response shape.") from exc
    return [item for item in lists_payload or [] if isinstance(item, dict)]


def _run_list_lists(args: argparse.Namespace) -> int:
    limit = 0 if args.all else args.limit
    lists_payload = viewer_lists(limit=limit)
    lists = lists_payload.get("items") or []
    enriched_items = []
    for item in lists:
        if not isinstance(item, dict):
            continue
        items_payload = list_items(str(item["id"]), limit=1)
        enriched = dict(item)
        enriched["itemCount"] = items_payload.get("totalCount", 0)
        enriched_items.append(enriched)
    payload = {
        "action": "list-lists",
        "totalCount": lists_payload.get("totalCount", len(enriched_items)),
        "items": enriched_items,
    }
    if args.json:
        return _emit(payload)
    return _print_list_summaries(payload)


def _run_list_items(args: argparse.Namespace) -> int:
    limit = 0 if args.all else args.limit
    selected_list = resolve_list(list_id=args.list_id, selector=args.list)
    items_payload = list_items(str(selected_list["id"]), limit=limit)
    payload = {
        "action": "list-items",
        "list": {
            "id": items_payload.get("id"),
            "name": items_payload.get("name"),
            "slug": items_payload.get("slug"),
            "description": items_payload.get("description"),
            "isPrivate": items_payload.get("isPrivate"),
        },
        "totalCount": items_payload.get("totalCount", 0),
        "items": items_payload.get("items") or [],
    }
    if args.json:
        return _emit(payload)
    return _print_list_items(payload)


def _run_create(args: argparse.Namespace) -> int:
    list_payload = {
        "name": args.name,
        "slug": None,
        "description": args.description or "",
        "isPrivate": args.visibility == "private",
    }
    if args.dry_run:
        payload = {"action": "create", "status": "dry-run", "list": list_payload}
    else:
        created = _create_list(args.name, args.description, args.visibility == "private")
        payload = {"action": "create", "status": "created", "list": created}
    if args.json:
        return _emit(payload)
    return _print_mutation(payload)


def _run_delete(args: argparse.Namespace) -> int:
    selected_list = resolve_list(list_id=args.list_id, selector=args.list)
    if args.dry_run:
        payload = {"action": "delete", "status": "dry-run", "list": selected_list}
    else:
        _delete_list(str(selected_list["id"]))
        payload = {"action": "delete", "status": "deleted", "list": selected_list}
    if args.json:
        return _emit(payload)
    return _print_mutation(payload)


def _run_membership(args: argparse.Namespace, assign: bool) -> int:
    selected_list = resolve_list(list_id=args.list_id, selector=args.list)
    repos = collect_repo_targets(args.repo or [], args.repos_file)
    if not repos:
        raise GhError("At least one target repository is required.", 64)

    resolved_repos: list[dict[str, object]] = []
    results: list[dict[str, object]] = []
    failure_count = 0

    for repo in repos:
        result: dict[str, object] = {"repo": repo}
        try:
            repo_payload = repo_view(repo)
            repo_record = {
                "repo": str(repo_payload["nameWithOwner"]),
                "repoId": str(repo_payload["id"]),
                "url": repo_payload.get("url"),
                "viewerHasStarred": bool(repo_payload.get("viewerHasStarred")),
            }
            resolved_repos.append(repo_record)
            result.update(repo_record)
        except GhError as exc:
            failure_count += 1
            result["status"] = "error"
            result["message"] = str(exc)
        results.append(result)

    memberships = repo_memberships([item["repoId"] for item in resolved_repos])
    repo_index = {item["repo"]: item for item in resolved_repos}

    for result in results:
        repo_name = result.get("repo")
        if result.get("status") == "error" or not isinstance(repo_name, str):
            continue
        repo_record = repo_index[repo_name]
        current_lists = memberships.get(repo_record["repoId"], [])
        current_list_ids = [str(item["id"]) for item in current_lists if isinstance(item, dict) and item.get("id")]
        target_list_id = str(selected_list["id"])

        if assign and not repo_record["viewerHasStarred"]:
            failure_count += 1
            result["status"] = "error"
            result["message"] = "repository is not starred by the authenticated user"
            continue

        if not assign and not repo_record["viewerHasStarred"]:
            result["status"] = "noop"
            result["message"] = "not starred; nothing to remove"
            continue

        if assign:
            if target_list_id in current_list_ids:
                result["status"] = "noop"
                result["message"] = "already assigned to list"
                continue
            desired_list_ids = current_list_ids + [target_list_id]
        else:
            if target_list_id not in current_list_ids:
                result["status"] = "noop"
                result["message"] = "not present in list"
                continue
            desired_list_ids = [item for item in current_list_ids if item != target_list_id]

        if args.dry_run:
            result["status"] = "dry-run"
            result["message"] = "would assign" if assign else "would unassign"
            continue

        try:
            _update_list_memberships(repo_record["repoId"], desired_list_ids)
        except GhError as exc:
            failure_count += 1
            result["status"] = "error"
            result["message"] = str(exc)
            continue

        result["status"] = "changed"
        result["message"] = "assigned" if assign else "unassigned"

    payload = {
        "action": "assign" if assign else "unassign",
        "list": selected_list,
        "targetCount": len(repos),
        "successCount": len(repos) - failure_count,
        "failureCount": failure_count,
        "results": results,
    }
    if args.json:
        _emit(payload)
    else:
        _print_mutation(payload)
    return 1 if failure_count else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage GitHub star lists and repository membership for the authenticated account."
    )
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument("--list-lists", action="store_true")
    action_group.add_argument("--list-items", action="store_true")
    action_group.add_argument("--create", action="store_true")
    action_group.add_argument("--delete", action="store_true")
    action_group.add_argument("--assign", action="store_true")
    action_group.add_argument("--unassign", action="store_true")

    parser.add_argument("--list", help="Exact list slug or exact list name.")
    parser.add_argument("--list-id", help="Exact GitHub user list id.")
    parser.add_argument("--name", help="List name for create.")
    parser.add_argument("--description", help="Optional list description for create.")
    parser.add_argument("--repo", action="append", default=[], help="Repository in owner/repo format.")
    parser.add_argument("--repos-file", help="Newline-delimited file of owner/repo entries.")
    parser.add_argument("--limit", type=_positive_int, default=100, help="Maximum number of items to return.")
    parser.add_argument("--all", action="store_true", help="Fetch all available items for read actions.")
    visibility_group = parser.add_mutually_exclusive_group()
    visibility_group.add_argument("--private", dest="visibility", action="store_const", const="private")
    visibility_group.add_argument("--public", dest="visibility", action="store_const", const="public")
    parser.set_defaults(visibility="public")
    parser.add_argument("--json", action="store_true", help="Emit normalized JSON output.")
    parser.add_argument("--dry-run", action="store_true", help="Preview write actions without mutating GitHub.")
    return parser


def _ensure_selector(args: argparse.Namespace) -> None:
    if bool(args.list) == bool(args.list_id):
        raise GhError("Pass exactly one of --list or --list-id.", 64)


def _validate_args(args: argparse.Namespace) -> None:
    if args.list_lists:
        if args.list or args.list_id or args.repo or args.repos_file or args.name or args.description:
            raise GhError("--list-lists only supports read flags.", 64)
        return

    if args.list_items:
        _ensure_selector(args)
        if args.repo or args.repos_file or args.name or args.description:
            raise GhError("--list-items only supports a list selector and read flags.", 64)
        return

    if args.create:
        if not args.name:
            raise GhError("--create requires --name.", 64)
        if args.list or args.list_id or args.repo or args.repos_file:
            raise GhError("--create does not accept existing list selectors or repo targets.", 64)
        if args.all:
            raise GhError("--all is only valid with read actions.", 64)
        if args.limit != 100:
            raise GhError("--limit is only valid with read actions.", 64)
        return

    if args.delete:
        _ensure_selector(args)
        if args.repo or args.repos_file or args.name or args.description:
            raise GhError("--delete does not accept repo targets or create-only flags.", 64)
        if args.all:
            raise GhError("--all is only valid with read actions.", 64)
        if args.limit != 100:
            raise GhError("--limit is only valid with read actions.", 64)
        return

    if args.assign or args.unassign:
        _ensure_selector(args)
        if args.name or args.description:
            raise GhError("--assign and --unassign do not accept create-only flags.", 64)
        if args.all:
            raise GhError("--all is only valid with read actions.", 64)
        if args.limit != 100:
            raise GhError("--limit is only valid with read actions.", 64)
        return


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        _validate_args(args)
        if args.list_lists:
            return _run_list_lists(args)
        if args.list_items:
            return _run_list_items(args)
        if args.create:
            return _run_create(args)
        if args.delete:
            return _run_delete(args)
        if args.assign:
            return _run_membership(args, assign=True)
        return _run_membership(args, assign=False)
    except GhError as exc:
        print(str(exc), file=sys.stderr)
        return exc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
