from __future__ import annotations

import argparse
import json
import sys

from .star_api import (
    GhError,
    collect_repo_targets,
    graphql,
    repo_memberships,
    repo_view,
    resolve_list,
)


def _emit(payload: object) -> int:
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


def _print_mutation(payload: dict[str, object]) -> int:
    print(f"Action: {payload.get('action')}")
    if payload.get("status"):
        print(f"Status: {payload.get('status')}")
    list_payload = payload.get("list")
    if isinstance(list_payload, dict):
        visibility = "private" if list_payload.get("isPrivate") else "public"
        slug = list_payload.get("slug")
        suffix = f" ({slug})" if slug else ""
        print(f"List: {list_payload.get('name')}{suffix} [{visibility}]")
    if "targetCount" in payload:
        print(f"Targets: {payload.get('targetCount')}")
        print(f"Succeeded: {payload.get('successCount')}")
        print(f"Failed: {payload.get('failureCount')}")
        for item in payload.get("results") or []:
            if isinstance(item, dict):
                print(
                    f"- {item.get('repo')}: {item.get('message') or item.get('status')}"
                )
    return 0


def _update_memberships(
    repo_id: str, desired_list_ids: list[str]
) -> list[dict[str, object]]:
    query = """
    mutation($itemId: ID!, $listIds: [ID!]!) {
      updateUserListsForItem(input: {itemId: $itemId, listIds: $listIds}) {
        lists { id name slug }
      }
    }
    """
    payload = graphql(query, {"itemId": repo_id, "listIds": desired_list_ids})
    try:
        lists_payload = payload["data"]["updateUserListsForItem"]["lists"]
    except (TypeError, KeyError) as exc:
        raise GhError("Unexpected update list memberships response shape.") from exc
    return [item for item in lists_payload or [] if isinstance(item, dict)]


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
            result.update(status="error", message=str(exc))
        results.append(result)

    memberships = repo_memberships([str(item["repoId"]) for item in resolved_repos])
    repo_index = {str(item["repo"]): item for item in resolved_repos}
    for result in results:
        repo_name = result.get("repo")
        if result.get("status") == "error" or not isinstance(repo_name, str):
            continue
        repo_record = repo_index[repo_name]
        repo_id = str(repo_record["repoId"])
        current_lists = memberships.get(repo_id, [])
        current_ids = [
            str(item["id"])
            for item in current_lists
            if isinstance(item, dict) and item.get("id")
        ]
        target_id = str(selected_list["id"])

        if assign and not repo_record["viewerHasStarred"]:
            failure_count += 1
            result.update(
                status="error",
                message="repository is not starred by the authenticated user",
            )
            continue
        if not assign and not repo_record["viewerHasStarred"]:
            result.update(status="noop", message="not starred; nothing to remove")
            continue
        if assign and target_id in current_ids:
            result.update(status="noop", message="already assigned to list")
            continue
        if not assign and target_id not in current_ids:
            result.update(status="noop", message="not present in list")
            continue

        desired_ids = (
            current_ids + [target_id]
            if assign
            else [item for item in current_ids if item != target_id]
        )
        if args.dry_run:
            result.update(
                status="dry-run", message="would assign" if assign else "would unassign"
            )
            continue
        try:
            _update_memberships(repo_id, desired_ids)
        except GhError as exc:
            failure_count += 1
            result.update(status="error", message=str(exc))
            continue
        result.update(status="changed", message="assigned" if assign else "unassigned")

    payload = {
        "action": "assign" if assign else "unassign",
        "list": selected_list,
        "targetCount": len(repos),
        "successCount": len(repos) - failure_count,
        "failureCount": failure_count,
        "results": results,
    }
    (_emit if args.json else _print_mutation)(payload)
    return 1 if failure_count else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stars-lists",
        description="Update GitHub star-list memberships for the authenticated account.",
    )
    actions = parser.add_mutually_exclusive_group(required=True)
    for name in ("assign", "unassign"):
        actions.add_argument(f"--{name}", action="store_true")
    parser.add_argument("--list", help="Exact list slug or exact list name.")
    parser.add_argument("--list-id", help="Exact GitHub user list id.")
    parser.add_argument(
        "--repo", action="append", default=[], help="Repository in owner/repo format."
    )
    parser.add_argument(
        "--repos-file", help="Newline-delimited file of owner/repo entries."
    )
    parser.add_argument(
        "--json", action="store_true", help="Emit normalized JSON output."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview write actions without mutating GitHub.",
    )
    return parser


def _ensure_selector(args: argparse.Namespace) -> None:
    if bool(args.list) == bool(args.list_id):
        raise GhError("Pass exactly one of --list or --list-id.", 64)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        _ensure_selector(args)
        return _run_membership(args, assign=bool(args.assign))
    except GhError as exc:
        print(str(exc), file=sys.stderr)
        return exc.returncode
