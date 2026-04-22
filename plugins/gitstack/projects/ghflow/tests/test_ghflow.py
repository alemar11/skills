from __future__ import annotations

import contextlib
import io
import json
import sys
import unittest
import zipfile
from pathlib import Path
from unittest import mock


PROJECT_SRC = Path(__file__).resolve().parents[1] / "src"
if str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))

import ghflow  # noqa: E402
from ghflow import checks  # noqa: E402
from ghflow import runtime  # noqa: E402


class ParseRootArgsTests(unittest.TestCase):
    def test_project_package_exports_main(self) -> None:
        self.assertTrue(callable(ghflow.main))

    def test_match_longest_nested_command(self) -> None:
        parsed = runtime.parse_root_args(["stars", "lists", "delete", "--list", "later"])
        self.assertEqual(parsed["mode"], "command")
        self.assertEqual(parsed["command"], ("stars", "lists", "delete"))
        self.assertEqual(parsed["tail"], ["--list", "later"])

    def test_render_stars_help_includes_direct_verbs_and_nested_group(self) -> None:
        help_text = runtime.render_noun_help(("stars",))
        self.assertIn("ghflow [--json] stars <list|add|remove> [args...]", help_text)
        self.assertIn("ghflow [--json] stars lists <list|items|delete|assign|unassign> [args...]", help_text)

    def test_render_stars_lists_help_is_generated_from_schema(self) -> None:
        help_text = runtime.render_noun_help(("stars", "lists"))
        self.assertIn("stars lists <list|items|delete|assign|unassign>", help_text)

    def test_parse_leaf_help_routes_to_noun_help(self) -> None:
        parsed = runtime.parse_root_args(["reviews", "address", "--help"])
        self.assertEqual(parsed["mode"], "noun_help")
        self.assertEqual(parsed["command"], ("reviews", "address"))

    def test_parse_ci_inspect_command(self) -> None:
        parsed = runtime.parse_root_args(["ci", "inspect", "--pr", "123"])
        self.assertEqual(parsed["mode"], "command")
        self.assertEqual(parsed["command"], ("ci", "inspect"))
        self.assertEqual(parsed["tail"], ["--pr", "123"])

    def test_render_ci_help_mentions_inspect(self) -> None:
        help_text = runtime.render_noun_help(("ci",))
        self.assertIn("ghflow [--json] ci inspect", help_text)

    def test_removed_doctor_command_fails(self) -> None:
        with self.assertRaises(runtime.GhflowError) as ctx:
            runtime.parse_root_args(["doctor"])
        self.assertEqual(ctx.exception.code, "invalid_arguments")

    def test_removed_top_level_lists_command_fails(self) -> None:
        with self.assertRaises(runtime.GhflowError) as ctx:
            runtime.parse_root_args(["lists", "list"])
        self.assertEqual(ctx.exception.code, "invalid_arguments")


class ContractTests(unittest.TestCase):
    def test_reviews_address_requires_selection_when_replying(self) -> None:
        spec = runtime.COMMAND_SPECS[("reviews", "address")]
        with self.assertRaises(runtime.GhflowError) as ctx:
            spec.handler(spec, ["--pr", "123", "--repo", "openai/codex", "--reply-body", "thanks"], False)
        self.assertEqual(ctx.exception.code, "invalid_arguments")


class UtilityTests(unittest.TestCase):
    def test_normalize_remote_url(self) -> None:
        self.assertEqual(
            runtime.normalize_remote_url("https://github.com/openai/codex.git"),
            "openai/codex",
        )
        self.assertEqual(
            runtime.normalize_remote_url("git@github.com:openai/codex.git"),
            "openai/codex",
        )

    def test_filter_runtime_noise_prefers_real_error(self) -> None:
        result = runtime.RunResult(
            1,
            "",
            "\n".join(
                [
                    "gh is installed: 2.89.0.",
                    "Authenticated to github.com as <unknown>.",
                    "Current directory is a git repository.",
                    "gh preflight checks passed.",
                    "HTTP 403: Resource not accessible by personal access token",
                ]
            ),
        )
        self.assertEqual(
            runtime.extract_runtime_error_message(result),
            "HTTP 403: Resource not accessible by personal access token",
        )

    def test_schema_commands_have_help_and_handlers(self) -> None:
        for command_path, spec in runtime.COMMAND_SPECS.items():
            with self.subTest(command_path=command_path):
                self.assertTrue(callable(spec.handler))
        for prefix in runtime.GROUP_HELP_PREFIXES:
            with self.subTest(prefix=prefix):
                help_text = runtime.render_noun_help(prefix)
                self.assertTrue(help_text.startswith("Usage:\n"))


class CiInspectRuntimeTests(unittest.TestCase):
    def test_ci_inspect_json_success_returns_zero(self) -> None:
        payload = {
            "repo": "openai/codex",
            "pr": "123",
            "failingCount": 0,
            "results": [],
            "summary": "no_failing_checks",
        }
        stdout = io.StringIO()
        with (
            contextlib.redirect_stdout(stdout),
            mock.patch.object(runtime, "is_git_repo", return_value=False),
            mock.patch.object(runtime.checks, "inspect_pr_failures", return_value=(payload, 0)),
        ):
            exit_code = runtime.main(
                ["--json", "ci", "inspect", "--repo", "openai/codex", "--allow-non-project"]
            )
        body = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertTrue(body["ok"])
        self.assertEqual(body["command"], ["ci", "inspect"])
        self.assertEqual(body["data"]["summary"], "no_failing_checks")

    def test_ci_inspect_json_failures_return_nonzero_with_data(self) -> None:
        payload = {
            "repo": "openai/codex",
            "pr": "123",
            "failingCount": 1,
            "results": [{"name": "test", "status": "ok"}],
            "summary": "failing_checks",
        }
        stdout = io.StringIO()
        with (
            contextlib.redirect_stdout(stdout),
            mock.patch.object(runtime, "is_git_repo", return_value=False),
            mock.patch.object(runtime.checks, "inspect_pr_failures", return_value=(payload, 1)),
        ):
            exit_code = runtime.main(
                ["--json", "ci", "inspect", "--repo", "openai/codex", "--allow-non-project"]
            )
        body = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 1)
        self.assertFalse(body["ok"])
        self.assertEqual(body["command"], ["ci", "inspect"])
        self.assertEqual(body["error"]["code"], "failing_checks")
        self.assertEqual(body["data"]["failingCount"], 1)


class ChecksTests(unittest.TestCase):
    def test_extract_run_id_and_job_id(self) -> None:
        url = "https://github.com/openai/codex/actions/runs/123456789/job/987654321"
        self.assertEqual(checks.extract_run_id(url), "123456789")
        self.assertEqual(checks.extract_job_id(url), "987654321")

    def test_parse_available_fields_from_gh_error(self) -> None:
        message = "\n".join(
            [
                "Unknown JSON field: detailsUrl",
                "Available fields:",
                "name",
                "state",
                "bucket",
                "link",
            ]
        )
        self.assertEqual(
            checks.parse_available_fields(message),
            ["name", "state", "bucket", "link"],
        )

    def test_external_check_stays_report_only(self) -> None:
        result = checks.analyze_check(
            {"name": "Buildkite", "detailsUrl": "https://buildkite.example/job/1"},
            repo="openai/codex",
            repo_root=None,
            max_lines=80,
            context=20,
        )
        self.assertEqual(result["status"], "external")
        self.assertIn("No GitHub Actions run id", result["note"])

    def test_extract_failure_snippet_prefers_failure_marker_window(self) -> None:
        log_text = "\n".join(
            [
                "step 1",
                "step 2",
                "AssertionError: boom",
                "step 4",
                "step 5",
            ]
        )
        snippet = checks.extract_failure_snippet(log_text, max_lines=3, context=1)
        self.assertEqual(snippet, "\n".join(["step 2", "AssertionError: boom", "step 4"]))

    def test_extract_log_from_job_archive_reads_zip_payload(self) -> None:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("job.txt", "line 1\nline 2\n")
        text, error = checks.extract_log_from_job_archive(buffer.getvalue())
        self.assertEqual(error, "")
        self.assertIn("line 2", text)


if __name__ == "__main__":
    unittest.main()
