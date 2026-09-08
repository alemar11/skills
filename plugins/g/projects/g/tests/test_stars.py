from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import tomllib
import unittest
import zipfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from g import star_api, star_lists, stars

SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "g"

def load_stars_module():
    return stars

class StarsContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.stars = load_stars_module()

    def test_shipped_artifact_is_executable_zipapp(self) -> None:
        self.assertTrue(os.access(SCRIPT, os.X_OK))
        self.assertTrue(zipfile.is_zipfile(SCRIPT))
        with SCRIPT.open("rb") as handle:
            self.assertEqual(handle.readline().decode().strip(), "#!/usr/bin/env python3")

    def test_manifest_package_and_shipped_artifact_versions_match(self) -> None:
        plugin_root = Path(__file__).resolve().parents[3]
        manifest = json.loads((plugin_root / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        package = tomllib.loads((Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8"))
        artifact_version = subprocess.check_output([str(SCRIPT), "--version"], text=True).strip()
        self.assertEqual(manifest["version"], "5.0.1")
        self.assertEqual(package["project"]["version"], manifest["version"])
        self.assertEqual(artifact_version, manifest["version"])
        self.assertNotIn("apps", manifest)
        self.assertFalse((plugin_root / ".app.json").exists())

    def test_version(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = self.stars.main(["--version"])
        self.assertEqual(code, 0)
        self.assertEqual(stdout.getvalue().strip(), "5.0.1")

    def test_json_doctor_shape(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            self.stars.main(["--json", "doctor"])
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["version"], "5.0.1")
        self.assertIn("gh", payload["checks"])

    def test_invalid_command_json(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = self.stars.main(["--json", "nope"])
        self.assertEqual(code, 64)
        payload = json.loads(stdout.getvalue())
        self.assertFalse(payload["ok"])

    def test_retired_commands_fail_without_provider_access(self) -> None:
        for command in (["list"], ["add", "owner/repo"], ["remove", "owner/repo"],
                        ["lists", "list"], ["lists", "items", "L1"], ["lists", "delete", "L1"]):
            with self.subTest(command=command), mock.patch.object(stars, "helper_result") as helper:
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(stars.main(["--json", *command]), 64)
                helper.assert_not_called()

    def test_assign_positional_ids_map_to_flags(self) -> None:
        captured: list[str] = []

        def fake_helper(_main, argv):
            captured.extend(argv)
            return stars.RunResult(0, "", "")

        with mock.patch.object(stars, "helper_result", side_effect=fake_helper):
            self.assertEqual(stars.invoke(["lists", "assign", "L1", "owner/repo"], False), 0)
        self.assertEqual(captured[:5], ["--assign", "--list-id", "L1", "--repo", "owner/repo"])


class MembershipTests(unittest.TestCase):
    def run_membership(self, action="assign", *, current=None, starred=True, dry_run=False):
        current = [{"id": "OTHER"}] if current is None else current
        stdout = io.StringIO()
        args = [f"--{action}", "--list-id", "TARGET", "--repo", "owner/repo", "--json"]
        if dry_run:
            args.append("--dry-run")
        with mock.patch.object(star_lists, "resolve_list", return_value={"id": "TARGET"}), \
             mock.patch.object(star_lists, "repo_view", return_value={
                 "id": "R1", "nameWithOwner": "owner/repo", "url": "https://github.com/owner/repo",
                 "viewerHasStarred": starred}), \
             mock.patch.object(star_lists, "repo_memberships", return_value={"R1": current}), \
             mock.patch.object(star_lists, "_update_memberships", return_value=[]) as update, \
             contextlib.redirect_stdout(stdout):
            code = star_lists.main(args)
        return code, json.loads(stdout.getvalue()), update

    def test_assign_preserves_unrelated_memberships(self):
        code, payload, update = self.run_membership()
        self.assertEqual(code, 0)
        update.assert_called_once_with("R1", ["OTHER", "TARGET"])
        self.assertEqual(payload["results"][0]["status"], "changed")

    def test_unassign_preserves_unrelated_memberships(self):
        code, _, update = self.run_membership("unassign", current=[{"id": "OTHER"}, {"id": "TARGET"}])
        self.assertEqual(code, 0)
        update.assert_called_once_with("R1", ["OTHER"])

    def test_assignment_never_stars_an_unstarred_repository(self):
        code, payload, update = self.run_membership(starred=False)
        self.assertEqual(code, 1)
        self.assertEqual(payload["failureCount"], 1)
        update.assert_not_called()

    def test_dry_run_and_noop_never_mutate(self):
        for options in ({"dry_run": True}, {"current": [{"id": "TARGET"}]}):
            with self.subTest(options=options):
                code, _, update = self.run_membership(**options)
                self.assertEqual(code, 0)
                update.assert_not_called()

    def test_membership_lookup_reads_every_list_and_item_page(self):
        calls = []
        def provider(query, variables):
            calls.append(variables.copy())
            after = variables.get("after")
            if "id" not in variables:
                return {"data": {"viewer": {"lists": {
                    "totalCount": 2, "nodes": [{"id": "L2" if after else "L1"}],
                    "pageInfo": {"hasNextPage": not bool(after), "endCursor": "next" if not after else None}}}}}
            list_id = variables["id"]
            return {"data": {"node": {"__typename": "UserList", "id": list_id,
                "items": {"totalCount": 2, "nodes": [{"__typename": "Repository", "id": "R1" if after else "OTHER"}],
                    "pageInfo": {"hasNextPage": not bool(after), "endCursor": "items-next" if not after else None}}}}}
        with mock.patch.object(star_api, "graphql", side_effect=provider):
            result = star_api.repo_memberships(["R1"])
        self.assertEqual([item["id"] for item in result["R1"]], ["L1", "L2"])
        self.assertEqual(len(calls), 6)

    def test_incomplete_membership_inventory_fails_closed(self):
        for page_info in ({"hasNextPage": True, "endCursor": None}, {}):
            payload = {"data": {"viewer": {"lists": {"totalCount": 0, "nodes": [], "pageInfo": page_info}}}}
            with self.subTest(page_info=page_info), mock.patch.object(star_api, "graphql", return_value=payload):
                with self.assertRaises(star_api.GhError):
                    star_api.repo_memberships(["R1"])

    def test_repeated_membership_cursor_fails_closed(self):
        payload = {"data": {"viewer": {"lists": {"totalCount": 0, "nodes": [],
                   "pageInfo": {"hasNextPage": True, "endCursor": "same"}}}}}
        with mock.patch.object(star_api, "graphql", return_value=payload) as query:
            with self.assertRaises(star_api.GhError):
                star_api.repo_memberships(["R1"])
        self.assertEqual(query.call_count, 2)

    def test_unreadable_or_incomplete_collections_prevent_membership_writes(self):
        malformed = [
            None, {}, {"totalCount": 1, "nodes": None},
            {"totalCount": 1, "nodes": [None]},
            {"totalCount": 1, "nodes": [{}]},
            {"totalCount": 1, "nodes": [{"id": ""}]},
            {"totalCount": 1, "nodes": []},
            {"totalCount": 0, "nodes": [{"id": "L1"}]},
            {"totalCount": 2, "nodes": [{"id": "L1"}, {"id": "L1"}]},
            {"totalCount": "1", "nodes": [{"id": "L1"}]},
        ]
        for level in ("lists", "items"):
            for collection in malformed:
                with self.subTest(level=level, collection=collection):
                    connection = dict(collection) if isinstance(collection, dict) else collection
                    if isinstance(connection, dict):
                        connection["pageInfo"] = {"hasNextPage": False}
                    def provider(query, variables):
                        if "id" not in variables:
                            lists = connection if level == "lists" else {
                                "totalCount": 1, "nodes": [{"id": "L1"}],
                                "pageInfo": {"hasNextPage": False}}
                            return {"data": {"viewer": {"lists": lists}}}
                        return {"data": {"node": {"__typename": "UserList", "id": "L1", "items": connection}}}
                    with mock.patch.object(star_lists, "resolve_list", return_value={"id": "TARGET"}), \
                         mock.patch.object(star_lists, "repo_view", return_value={"id": "R1", "nameWithOwner": "owner/repo", "viewerHasStarred": True}), \
                         mock.patch.object(star_api, "graphql", side_effect=provider), \
                         mock.patch.object(star_lists, "_update_memberships") as update, \
                         contextlib.redirect_stderr(io.StringIO()):
                        code = star_lists.main(["--assign", "--list-id", "TARGET", "--repo", "owner/repo"])
                    self.assertNotEqual(code, 0)
                    update.assert_not_called()

    def test_item_identity_and_collection_count_are_verified(self):
        cases = [
            ("OTHER", 0, []),
            ("L1", 1, [{"__typename": "Repository", "id": ""}]),
            ("L1", 1, [{"__typename": "Unknown", "id": "R1"}]),
            ("L1", 2, [{"__typename": "Repository", "id": "R1"}]),
        ]
        for identity, count, nodes in cases:
            payload = {"data": {"node": {"__typename": "UserList", "id": identity,
                       "items": {"totalCount": count, "nodes": nodes, "pageInfo": {"hasNextPage": False}}}}}
            with self.subTest(payload=payload), mock.patch.object(star_api, "graphql", return_value=payload):
                with self.assertRaises(star_api.GhError):
                    star_api.list_items("L1")

    def test_changing_collection_counts_fail_closed(self):
        pages = [{"data": {"viewer": {"lists": {"totalCount": count,
                  "nodes": [{"id": identity}], "pageInfo": page_info}}}}
                 for count, identity, page_info in (
                     (2, "L1", {"hasNextPage": True, "endCursor": "next"}),
                     (3, "L2", {"hasNextPage": False}))]
        with mock.patch.object(star_api, "graphql", side_effect=pages):
            with self.assertRaises(star_api.GhError):
                star_api.viewer_lists()

    def test_graphql_partial_errors_do_not_become_membership_state(self):
        with mock.patch.object(star_api, "_run_gh_json", return_value={"data": {}, "errors": [{"message": "denied"}]}):
            with self.assertRaises(star_api.GhError):
                star_api.graphql("query { viewer { login } }")

    def test_batch_reports_partial_failure(self):
        out = io.StringIO()
        with mock.patch.object(star_lists, "resolve_list", return_value={"id": "TARGET"}), \
             mock.patch.object(star_lists, "repo_view", side_effect=[
                 {"id": "R1", "nameWithOwner": "owner/one", "viewerHasStarred": True},
                 star_api.GhError("inaccessible")]), \
             mock.patch.object(star_lists, "repo_memberships", return_value={"R1": []}), \
             mock.patch.object(star_lists, "_update_memberships", return_value=[]) as update, \
             contextlib.redirect_stdout(out):
            code = star_lists.main(["--assign", "--list-id", "TARGET", "--repo", "owner/one", "--repo", "owner/two", "--json"])
        payload = json.loads(out.getvalue())
        self.assertEqual(code, 1)
        self.assertEqual((payload["successCount"], payload["failureCount"]), (1, 1))
        update.assert_called_once_with("R1", ["TARGET"])


if __name__ == "__main__":
    unittest.main()
