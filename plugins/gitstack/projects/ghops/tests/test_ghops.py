from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock


PROJECT_SRC = Path(__file__).resolve().parents[1] / "src"
if str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))

import ghops  # noqa: E402
from ghops import runtime  # noqa: E402


class ParseRootArgsTests(unittest.TestCase):
    def test_project_package_exports_main(self) -> None:
        self.assertTrue(callable(ghops.main))

    def test_parse_global_json_doctor(self) -> None:
        parsed = runtime.parse_root_args(["--json", "doctor"])
        self.assertEqual(parsed["mode"], "doctor")
        self.assertTrue(parsed["json"])

    def test_match_longest_nested_command(self) -> None:
        parsed = runtime.parse_root_args(["issues", "labels", "create", "--name", "bug"])
        self.assertEqual(parsed["mode"], "command")
        self.assertEqual(parsed["command"], ("issues", "labels", "create"))
        self.assertEqual(parsed["tail"], ["--name", "bug"])

    def test_render_issues_help_is_generated_from_schema(self) -> None:
        help_text = runtime.render_noun_help(("issues",))
        self.assertIn("issues labels <list|create|update|delete>", help_text)
        self.assertIn("issues milestones list", help_text)

    def test_parse_leaf_help_routes_to_noun_help(self) -> None:
        parsed = runtime.parse_root_args(["issues", "view", "--help"])
        self.assertEqual(parsed["mode"], "noun_help")
        self.assertEqual(parsed["command"], ("issues", "view"))


class ContractTests(unittest.TestCase):
    def test_reactions_add_requires_positional_value(self) -> None:
        spec = runtime.COMMAND_SPECS[("reactions", "add")]
        with self.assertRaises(runtime.GhopsError) as ctx:
            spec.handler(spec, ["--repo", "openai/codex", "--resource", "issue", "--number", "1"], False)
        self.assertEqual(ctx.exception.code, "invalid_arguments")

    def test_actions_inspect_json_rejects_job_logs_mode(self) -> None:
        with self.assertRaises(runtime.GhopsError) as ctx:
            runtime.maybe_allows_json_inspect(["--run-id", "123", "--job-id", "456"])
        self.assertEqual(ctx.exception.code, "invalid_arguments")

    def test_request_get_rejects_mutating_flag_variants(self) -> None:
        spec = runtime.COMMAND_SPECS[("request", "get")]
        for tail in (
            ["/repos/foo/bar", "--method", "POST"],
            ["/repos/foo/bar", "--method=POST"],
            ["/repos/foo/bar", "-XPOST"],
            ["/repos/foo/bar", "--input=@payload.json"],
            ["/repos/foo/bar", "-Fkey=value"],
            ["/repos/foo/bar", "--raw-field=key=value"],
        ):
            with self.subTest(tail=tail):
                with self.assertRaises(runtime.GhopsError) as ctx:
                    spec.handler(spec, tail, True)
                self.assertEqual(ctx.exception.code, "invalid_arguments")


class DoctorTests(unittest.TestCase):
    def test_collect_doctor_data_without_gh(self) -> None:
        with mock.patch.object(runtime, "shutil_which", return_value=None):
            with mock.patch.object(runtime, "run") as run_mock:
                run_mock.return_value = runtime.RunResult(1, "", "")
                data = runtime.collect_doctor_data()
        self.assertFalse(data["gh"]["installed"])
        self.assertFalse(data["auth"]["authenticated"])
        self.assertFalse(data["ready"])

    def test_collect_doctor_data_with_repo_and_auth(self) -> None:
        def fake_run(command: list[str], *, cwd=None, input_text=None) -> runtime.RunResult:
            command_key = tuple(command)
            responses = {
                ("gh", "--version"): runtime.RunResult(0, "gh version 2.70.0 (2024-01-01)\n", ""),
                ("gh", "auth", "status", "--hostname", runtime.HOST): runtime.RunResult(
                    0,
                    "",
                    "Logged in to github.com as octocat\n",
                ),
                ("git", "rev-parse", "--is-inside-work-tree"): runtime.RunResult(0, "true\n", ""),
                ("git", "rev-parse", "--abbrev-ref", "HEAD"): runtime.RunResult(0, "feature/test\n", ""),
                ("git", "remote", "get-url", "origin"): runtime.RunResult(
                    0,
                    "git@github.com:openai/codex.git\n",
                    "",
                ),
            }
            return responses[command_key]

        with mock.patch.object(runtime, "shutil_which", return_value="/opt/homebrew/bin/gh"):
            with mock.patch.object(runtime, "run", side_effect=fake_run):
                data = runtime.collect_doctor_data()

        self.assertTrue(data["gh"]["installed"])
        self.assertEqual(data["gh"]["version"], "2.70.0")
        self.assertTrue(data["auth"]["authenticated"])
        self.assertEqual(data["auth"]["login"], "octocat")
        self.assertTrue(data["project"]["is_git_repo"])
        self.assertEqual(data["project"]["resolved_repo"], "openai/codex")
        self.assertTrue(data["ready"])


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


if __name__ == "__main__":
    unittest.main()
