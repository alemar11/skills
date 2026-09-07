from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from g import cli
from g.common import GError, Result, normalize_remote, resolve_repo
from g.publish import _find_open_pr, open_pr, preflight


class CliContractTests(unittest.TestCase):
    def invoke(self, args: list[str]) -> tuple[int, str]:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = cli.main(args)
        return code, output.getvalue()

    def test_version(self) -> None:
        code, output = self.invoke(["--version"])
        self.assertEqual(code, 0)
        self.assertEqual(output.strip(), "4.0.1")

    def test_json_doctor_shape(self) -> None:
        doctor_payload = {
            "ok": True,
            "provider_ready": True,
            "version": "4.0.1",
            "checks": {
                "gh_stack": {"status": "missing"},
            },
        }
        with mock.patch.object(cli, "doctor", return_value=doctor_payload):
            code, output = self.invoke(["--json", "doctor"])
        payload = json.loads(output)
        self.assertIn(code, {0, 1})
        self.assertEqual(payload["version"], "4.0.1")
        self.assertNotIn("connector", payload["checks"])
        self.assertIn("gh_stack", payload["checks"])

    def test_json_argument_error(self) -> None:
        code, output = self.invoke(["--json", "repo", "resolve", "--repo", "bad"])
        payload = json.loads(output)
        self.assertEqual(code, 64)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["code"], "invalid_arguments")

    def test_stack_raw_preserves_upstream_json_after_separator(self) -> None:
        with mock.patch.object(cli.stack, "execute_raw", return_value=0) as execute:
            code = cli.main(["stack", "raw", "--", "view", "--json"])

        self.assertEqual(code, 0)
        execute.assert_called_once_with(["--", "view", "--json"], json_mode=False)

    def test_stack_raw_accepts_wrapper_json_before_separator(self) -> None:
        with mock.patch.object(cli.stack, "execute_raw", return_value=0) as execute:
            code = cli.main(["stack", "raw", "--json", "--", "view"])

        self.assertEqual(code, 0)
        execute.assert_called_once_with(["--", "view"], json_mode=True)

    def test_typed_stack_arguments_are_forwarded_without_an_explicit_separator(self) -> None:
        cases = [
            (
                ["--json", "stack", "init", "--base", "main", "layer-a", "layer-b"],
                "init",
                ["--base", "main", "layer-a", "layer-b"],
            ),
            (["--json", "stack", "rebase", "--upstack"], "rebase", ["--upstack"]),
            (["--json", "stack", "submit", "--auto"], "submit", ["--auto"]),
            (["--json", "stack", "view", "--json"], "view", ["--json"]),
        ]
        for argv, command, expected_args in cases:
            with self.subTest(argv=argv), mock.patch.object(cli.stack, "execute", return_value=0) as execute:
                code = cli.main(argv)

            self.assertEqual(code, 0)
            execute.assert_called_once_with(command, expected_args, json_mode=True)

    def test_review_mutation_help_requires_g_reservation_only(self) -> None:
        for command in ("request", "comment", "reply", "resolve"):
            output = io.StringIO()
            with contextlib.redirect_stdout(output), self.assertRaises(SystemExit) as raised:
                cli.main(["reviews", command, "--help"])
            self.assertEqual(raised.exception.code, 0)
            self.assertIn("--reservation-file", output.getvalue())
            self.assertNotIn("--ledger-file", output.getvalue())

    def test_plugin_runtime_does_not_reference_external_skill_installations(self) -> None:
        source = Path(__file__).resolve().parents[1] / "src" / "g"
        runtime = "\n".join(
            path.read_text(encoding="utf-8") for path in sorted(source.glob("*.py"))
        )
        for forbidden in (
            "skills/implement-feature", ".agents/skills", ".codex/skills",
            "ledger-cache", "--ledger-file",
        ):
            self.assertNotIn(forbidden, runtime)

    def test_publish_rejects_inline_title_without_echoing_it(self) -> None:
        hostile = "`unsafe` $(command) $HOME"
        code, output = self.invoke([
            "--json", "publish", "open", "--title", hostile, "--body-file", "/tmp/body.md",
        ])
        self.assertEqual(code, 64)
        self.assertNotIn(hostile, output)
        self.assertEqual(json.loads(output)["error"]["code"], "invalid_arguments")

    def test_publish_template_command_was_removed(self) -> None:
        code, output = self.invoke(["--json", "publish", "template"])
        self.assertEqual(code, 64)
        self.assertEqual(json.loads(output)["error"]["code"], "invalid_arguments")

    def test_repo_resolve_json(self) -> None:
        code, output = self.invoke(["repo", "resolve", "--repo", "owner/repo", "--json"])
        payload = json.loads(output)
        self.assertEqual(code, 0)
        self.assertEqual(payload["data"]["repo"], "owner/repo")

    def test_normalize_remote(self) -> None:
        self.assertEqual(normalize_remote("git@github.com:owner/repo.git"), "owner/repo")
        self.assertEqual(normalize_remote("https://github.com/owner/repo.git"), "owner/repo")

    def test_publish_refuses_default_branch(self) -> None:
        state = {"repo": "owner/repo", "root": "/tmp/repo", "branch": "main", "default_branch": "main", "on_default_branch": True, "upstream": None, "dirty": False, "status": [], "existing_pull_request": None}
        with tempfile.TemporaryDirectory() as directory:
            title_file = Path(directory) / "title.txt"
            body_file = Path(directory) / "body.md"
            title_file.write_text("Title", encoding="utf-8")
            body_file.write_text("Body", encoding="utf-8")
            with mock.patch("g.publish.preflight", return_value=state):
                with self.assertRaises(GError) as raised:
                    open_pr(repo=None, title_file=str(title_file), body_file=str(body_file), draft=True, base=None, dry_run=True, expected_worktree_fingerprint=None)
        self.assertEqual(raised.exception.code, "unsafe_branch")

    def test_publish_dry_run(self) -> None:
        state = {"repo": "owner/repo", "root": "/tmp/repo", "branch": "feature", "default_branch": "main", "on_default_branch": False, "upstream": "origin/feature", "dirty": False, "status": [], "existing_pull_request": None}
        with tempfile.TemporaryDirectory() as directory:
            title_file = Path(directory) / "title.txt"
            body_file = Path(directory) / "body.md"
            title_file.write_text("Title", encoding="utf-8")
            body_file.write_text("Body", encoding="utf-8")
            with mock.patch("g.publish.preflight", return_value=state):
                result = open_pr(repo=None, title_file=str(title_file), body_file=str(body_file), draft=True, base="main", dry_run=True, expected_worktree_fingerprint=None)
        self.assertEqual(result["status"], "dry-run")
        self.assertEqual(result["transport"]["endpoint"], "repos/owner/repo/pulls")
        self.assertNotIn("Title", json.dumps(result))

    def test_publish_dry_run_accepts_explicit_non_default_base(self) -> None:
        state = {
            "repo": "owner/repo", "root": "/tmp/repo", "branch": "child",
            "default_branch": "main", "on_default_branch": False,
            "upstream": "origin/child", "dirty": False, "status": [],
            "existing_pull_request": None,
        }
        with tempfile.TemporaryDirectory() as directory:
            title_file = Path(directory) / "title.txt"
            body_file = Path(directory) / "body.md"
            title_file.write_text("Title", encoding="utf-8")
            body_file.write_text("Closes #10", encoding="utf-8")
            with mock.patch("g.publish.preflight", return_value=state):
                result = open_pr(
                    repo=None, title_file=str(title_file), body_file=str(body_file),
                    draft=True, base="parent", dry_run=True,
                    expected_worktree_fingerprint=None,
                )

        self.assertEqual(result["target"]["base"], "parent")

    def test_reused_pr_preserves_existing_base_and_draft_state(self) -> None:
        state = {
            "repo": "owner/repo", "root": "/tmp/repo", "branch": "child",
            "default_branch": "main", "on_default_branch": False,
            "upstream": "origin/child", "dirty": False, "status": [],
            "existing_pull_request": {
                "number": 7, "baseRefName": "parent", "isDraft": False,
            },
        }
        pull = {
            "number": 7,
            "html_url": "https://github.com/owner/repo/pull/7",
            "title": "Title",
            "body": "Closes #10",
            "draft": False,
            "head": {"ref": "child", "repo": {"full_name": "owner/repo"}},
            "base": {"ref": "parent", "repo": {"full_name": "owner/repo"}},
        }
        with tempfile.TemporaryDirectory() as directory:
            title_file = Path(directory) / "title.txt"
            body_file = Path(directory) / "body.md"
            title_file.write_text("Title", encoding="utf-8")
            body_file.write_text("Closes #10", encoding="utf-8")
            with mock.patch("g.publish.preflight", return_value=state), \
                 mock.patch("g.publish._read_pull_request", return_value=pull):
                result = open_pr(
                    repo=None, title_file=str(title_file), body_file=str(body_file),
                    draft=True, base=None, dry_run=False,
                    expected_worktree_fingerprint=None,
                )

        self.assertEqual(result["status"], "reused")
        self.assertEqual(result["pull_request"]["target"]["base"], "parent")
        self.assertFalse(result["pull_request"]["target"]["draft"])

    def test_reused_pr_rejects_explicit_base_drift(self) -> None:
        state = {
            "repo": "owner/repo", "root": "/tmp/repo", "branch": "child",
            "default_branch": "main", "on_default_branch": False,
            "upstream": "origin/child", "dirty": False, "status": [],
            "existing_pull_request": {
                "number": 7, "baseRefName": "parent", "isDraft": True,
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            title_file = Path(directory) / "title.txt"
            body_file = Path(directory) / "body.md"
            title_file.write_text("Title", encoding="utf-8")
            body_file.write_text("Body", encoding="utf-8")
            with mock.patch("g.publish.preflight", return_value=state):
                with self.assertRaises(GError) as raised:
                    open_pr(
                        repo=None, title_file=str(title_file), body_file=str(body_file),
                        draft=True, base="main", dry_run=False,
                        expected_worktree_fingerprint=None,
                    )

        self.assertEqual(raised.exception.code, "pull_request_base_mismatch")

    def test_preflight_keeps_matching_explicit_repo_checkout(self) -> None:
        def fake_checked(command, cwd=None):
            if command[:3] == ["git", "rev-parse", "--show-toplevel"]:
                return Result(0, "/tmp/repo\n", "")
            if command[:4] == ["git", "remote", "get-url", "origin"]:
                return Result(0, "git@github.com:owner/repo.git\n", "")
            if command[:3] == ["gh", "auth", "status"]:
                return Result(0, "", "")
            if command[:3] == ["git", "branch", "--show-current"]:
                return Result(0, "feature\n", "")
            if command[:3] == ["git", "status", "--short"]:
                return Result(0, "## feature...origin/feature\n", "")
            if command[:3] == ["gh", "repo", "view"]:
                return Result(0, "main\n", "")
            if command[:3] == ["git", "rev-list", "--left-right"]:
                return Result(0, "0 0\n", "")
            if command[:3] == ["gh", "pr", "list"]:
                return Result(0, "[]\n", "")
            raise AssertionError(command)

        def fake_run(command, cwd=None):
            if command[-1] == "branch.feature.remote":
                return Result(0, "origin\n", "")
            if command[-1] == "branch.feature.merge":
                return Result(0, "refs/heads/feature\n", "")
            raise AssertionError(command)

        with mock.patch("g.publish.checked", side_effect=fake_checked), \
             mock.patch("g.publish.run", side_effect=fake_run):
            state = preflight("owner/repo")
        self.assertEqual(state["root"], "/tmp/repo")
        self.assertEqual(state["upstream"], "origin/feature")
        self.assertTrue(state["upstream_valid"])

    def test_preflight_rejects_explicit_repo_origin_mismatch(self) -> None:
        with mock.patch(
            "g.publish.checked",
            side_effect=[
                Result(0, "/tmp/repo\n", ""),
                Result(0, "git@github.com:owner/other.git\n", ""),
            ],
        ):
            with self.assertRaises(GError) as raised:
                preflight("owner/repo")
        self.assertEqual(raised.exception.code, "repo_mismatch")

    def test_preflight_rejects_detached_head(self) -> None:
        with mock.patch(
            "g.publish.checked",
            side_effect=[
                Result(0, "/tmp/repo\n", ""),
                Result(0, "git@github.com:owner/repo.git\n", ""),
                Result(0, "", ""),
                Result(0, "\n", ""),
            ],
        ):
            with self.assertRaises(GError) as raised:
                preflight()
        self.assertEqual(raised.exception.code, "unsafe_branch")

    def test_preflight_rejects_wrong_upstream(self) -> None:
        checked_results = [
            Result(0, "/tmp/repo\n", ""),
            Result(0, "git@github.com:owner/repo.git\n", ""),
            Result(0, "", ""),
            Result(0, "feature\n", ""),
            Result(0, "## feature...fork/feature\n", ""),
            Result(0, "main\n", ""),
        ]
        run_results = [
            Result(0, "fork\n", ""),
            Result(0, "refs/heads/feature\n", ""),
        ]
        with mock.patch("g.publish.checked", side_effect=checked_results), \
             mock.patch("g.publish.run", side_effect=run_results):
            with self.assertRaises(GError) as raised:
                preflight()
        self.assertEqual(raised.exception.code, "upstream_mismatch")

    def test_preflight_allows_missing_upstream_before_first_push(self) -> None:
        checked_results = [
            Result(0, "/tmp/repo\n", ""),
            Result(0, "git@github.com:owner/repo.git\n", ""),
            Result(0, "", ""),
            Result(0, "feature\n", ""),
            Result(0, "## feature\n", ""),
            Result(0, "main\n", ""),
            Result(0, "[]\n", ""),
        ]
        with mock.patch("g.publish.checked", side_effect=checked_results), \
             mock.patch("g.publish.run", return_value=Result(1, "", "no upstream")):
            state = preflight()
        self.assertIsNone(state["upstream"])
        self.assertTrue(state["needs_push"])

    def test_preflight_rejects_partial_upstream_configuration(self) -> None:
        checked_results = [
            Result(0, "/tmp/repo\n", ""),
            Result(0, "git@github.com:owner/repo.git\n", ""),
            Result(0, "", ""),
            Result(0, "feature\n", ""),
            Result(0, "## feature\n", ""),
            Result(0, "main\n", ""),
        ]
        run_results = [Result(0, "origin\n", ""), Result(1, "", "missing")]
        with mock.patch("g.publish.checked", side_effect=checked_results), \
             mock.patch("g.publish.run", side_effect=run_results):
            with self.assertRaises(GError) as raised:
                preflight()
        self.assertEqual(raised.exception.code, "upstream_mismatch")

    def test_preflight_marks_ahead_branch_for_push(self) -> None:
        checked_results = [
            Result(0, "/tmp/repo\n", ""),
            Result(0, "git@github.com:owner/repo.git\n", ""),
            Result(0, "", ""),
            Result(0, "feature\n", ""),
            Result(0, "## feature...origin/feature [ahead 2]\n", ""),
            Result(0, "main\n", ""),
            Result(0, "2 0\n", ""),
            Result(0, "[]\n", ""),
        ]
        run_results = [
            Result(0, "origin\n", ""),
            Result(0, "refs/heads/feature\n", ""),
        ]
        with mock.patch("g.publish.checked", side_effect=checked_results), \
             mock.patch("g.publish.run", side_effect=run_results):
            state = preflight()
        self.assertEqual(state["ahead"], 2)
        self.assertTrue(state["needs_push"])

    def test_publish_open_rejects_unpushed_branch(self) -> None:
        state = {
            "repo": "owner/repo", "root": "/tmp/repo", "branch": "feature",
            "default_branch": "main", "on_default_branch": False,
            "upstream": None, "upstream_valid": True, "needs_push": True,
            "dirty": False, "status": [], "existing_pull_request": None,
        }
        with tempfile.TemporaryDirectory() as directory:
            title_file = Path(directory) / "title.txt"
            body_file = Path(directory) / "body.md"
            title_file.write_text("Title", encoding="utf-8")
            body_file.write_text("Body", encoding="utf-8")
            with mock.patch("g.publish.preflight", return_value=state):
                with self.assertRaises(GError) as raised:
                    open_pr(repo=None, title_file=str(title_file), body_file=str(body_file), draft=True, base=None, dry_run=True, expected_worktree_fingerprint=None)
        self.assertEqual(raised.exception.code, "branch_not_pushed")

    def test_open_pr_lookup_requires_verified_head_identity(self) -> None:
        payload = json.dumps([
            {
                "number": 7, "url": "https://github.com/owner/repo/pull/7",
                "title": "PR", "state": "OPEN", "isDraft": True,
                "headRefName": "feature",
                "headRepositoryOwner": {"login": "other"},
                "headRepository": {"name": "repo"},
            }
        ])
        with mock.patch("g.publish.checked", return_value=Result(0, payload, "")):
            with self.assertRaises(GError) as raised:
                _find_open_pr("owner/repo", "feature", Path("/tmp/repo"))
        self.assertEqual(raised.exception.code, "pull_request_mismatch")

    def test_open_pr_lookup_preserves_existing_base_branch(self) -> None:
        payload = json.dumps([
            {
                "number": 7, "url": "https://github.com/owner/repo/pull/7",
                "title": "PR", "state": "OPEN", "isDraft": True,
                "headRefName": "feature", "baseRefName": "main",
                "headRepositoryOwner": {"login": "owner"},
                "headRepository": {"name": "repo"},
            }
        ])
        with mock.patch("g.publish.checked", return_value=Result(0, payload, "")):
            result = _find_open_pr("owner/repo", "feature", Path("/tmp/repo"))
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["baseRefName"], "main")

    def test_open_pr_lookup_rejects_ambiguous_matches(self) -> None:
        payload = json.dumps([{"number": 1}, {"number": 2}])
        with mock.patch("g.publish.checked", return_value=Result(0, payload, "")):
            with self.assertRaises(GError) as raised:
                _find_open_pr("owner/repo", "feature", Path("/tmp/repo"))
        self.assertEqual(raised.exception.code, "ambiguous_pull_request")

    def test_malformed_publish_response_recovers_from_one_exact_head_read_back(self) -> None:
        state = {
            "repo": "owner/repo", "root": "/tmp/repo", "branch": "feature",
            "default_branch": "main", "on_default_branch": False,
            "upstream": "origin/feature", "needs_push": False, "dirty": False,
            "status": [], "existing_pull_request": None,
        }
        pull = {
            "number": 7, "html_url": "https://github.com/owner/repo/pull/7",
            "title": "`title` $HOME", "body": "$(command)\nUnicode ✓",
            "draft": True, "created_at": "2026-07-20T12:00:00Z",
            "user": {"login": "agent"},
            "head": {"ref": "feature", "repo": {"full_name": "owner/repo"}},
            "base": {"ref": "main", "repo": {"full_name": "owner/repo"}},
        }
        with tempfile.TemporaryDirectory() as directory:
            title_file = Path(directory) / "title.txt"
            body_file = Path(directory) / "body.md"
            title_file.write_text(pull["title"], encoding="utf-8")
            body_file.write_text(pull["body"], encoding="utf-8")
            with mock.patch("g.publish.preflight", return_value=state), \
                 mock.patch("g.publish._viewer_login", return_value="agent"), \
                 mock.patch("g.publish.api_request", return_value=Result(0, "not-json", "")) as mutation, \
                 mock.patch("g.publish._find_open_pr", return_value={"number": 7}) as lookup, \
                 mock.patch("g.publish._read_pull_request", return_value=pull) as read_back, \
                 mock.patch("g.publish.datetime") as clock:
                clock.now.return_value = datetime(2026, 7, 20, 12, 0, 0, tzinfo=timezone.utc)
                result = open_pr(
                    repo=None, title_file=str(title_file), body_file=str(body_file),
                    draft=True, base="main", dry_run=False, expected_worktree_fingerprint=None,
                )

        self.assertEqual(result["status"], "recovered")
        self.assertEqual(result["pull_request"]["number"], 7)
        mutation.assert_called_once()
        lookup.assert_called_once()
        read_back.assert_called_once()

    def test_malformed_publish_response_missing_or_mismatched_read_back_is_ambiguous(self) -> None:
        state = {
            "repo": "owner/repo", "root": "/tmp/repo", "branch": "feature",
            "default_branch": "main", "on_default_branch": False,
            "upstream": "origin/feature", "needs_push": False, "dirty": False,
            "status": [], "existing_pull_request": None,
        }
        title = "`title` $HOME"
        body = "$(command)\nUnicode ✓"
        mismatched = {
            "number": 7, "html_url": "https://github.com/owner/repo/pull/7",
            "title": title, "body": "different", "draft": True,
            "created_at": "2026-07-20T12:00:00Z", "user": {"login": "agent"},
            "head": {"ref": "feature", "repo": {"full_name": "owner/repo"}},
            "base": {"ref": "main", "repo": {"full_name": "owner/repo"}},
        }
        with tempfile.TemporaryDirectory() as directory:
            title_file = Path(directory) / "title.txt"
            body_file = Path(directory) / "body.md"
            title_file.write_text(title, encoding="utf-8")
            body_file.write_text(body, encoding="utf-8")
            for lookup_result, read_result in ((None, mismatched), ({"number": 7}, mismatched)):
                with self.subTest(lookup_result=lookup_result), \
                     mock.patch("g.publish.preflight", return_value=state), \
                     mock.patch("g.publish._viewer_login", return_value="agent"), \
                     mock.patch("g.publish.api_request", return_value=Result(0, "not-json", "")), \
                     mock.patch("g.publish._find_open_pr", return_value=lookup_result) as lookup, \
                     mock.patch("g.publish._read_pull_request", return_value=read_result) as read_back, \
                     mock.patch("g.publish.datetime") as clock:
                    clock.now.return_value = datetime(2026, 7, 20, 12, 0, 0, tzinfo=timezone.utc)
                    with self.assertRaises(GError) as raised:
                        open_pr(
                            repo=None, title_file=str(title_file), body_file=str(body_file),
                            draft=True, base="main", dry_run=False, expected_worktree_fingerprint=None,
                        )

                self.assertEqual(raised.exception.code, "provider_write_ambiguous")
                rendered = json.dumps(raised.exception.details, ensure_ascii=False)
                self.assertNotIn(title, rendered)
                self.assertNotIn(body, rendered)
                lookup.assert_called_once()
                self.assertEqual(read_back.call_count, 0 if lookup_result is None else 1)


if __name__ == "__main__":
    unittest.main()
