from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from g import ci as cli


class CiInspectContractTests(unittest.TestCase):
    def test_version(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = cli.main(["--version"])
        self.assertEqual(code, 0)
        self.assertEqual(stdout.getvalue().strip(), "2.18.15")

    def test_json_doctor_shape(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            cli.main(["--json", "doctor"])
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["version"], "2.18.15")
        self.assertIn("git", payload["checks"])
        self.assertIn("gh", payload["checks"])

    def test_invalid_repo_reference(self) -> None:
        with self.assertRaises(cli.InspectionError):
            cli.validate_repo_reference("not-valid")

    def test_json_error_shape(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = cli.main(["--json", "--repo", "bad", "--allow-non-project"])
        self.assertEqual(code, 64)
        payload = json.loads(stdout.getvalue())
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["version"], "2.18.15")
        self.assertEqual(payload["command"], ["inspect"])
        self.assertIn("message", payload["error"])

    def test_fetch_checks_confirms_empty_rollup_after_checks_command_failure(self) -> None:
        gh_results = [
            cli.GhResult(1, "", "no checks reported"),
            cli.GhResult(1, "", "no checks reported"),
            cli.GhResult(0, json.dumps({"statusCheckRollup": []}), ""),
        ]
        with mock.patch.object(cli, "run_gh_command", side_effect=gh_results) as run_gh:
            checks = cli.fetch_checks("21", "owner/repo", None)

        self.assertEqual(checks, [])
        self.assertEqual(
            run_gh.call_args_list[-1].args[0],
            [
                "pr",
                "view",
                "21",
                "--json",
                "statusCheckRollup",
                "--repo",
                "owner/repo",
            ],
        )

    def test_fetch_checks_does_not_mask_nonempty_rollup_failure(self) -> None:
        gh_results = [
            cli.GhResult(1, "", "checks command failed"),
            cli.GhResult(1, "", "checks command failed"),
            cli.GhResult(
                0,
                json.dumps({"statusCheckRollup": [{"name": "build"}]}),
                "",
            ),
        ]
        with (
            mock.patch.object(cli, "run_gh_command", side_effect=gh_results),
            self.assertRaises(cli.InspectionError),
        ):
            cli.fetch_checks("21", "owner/repo", None)

    def test_inspect_pr_failures_reports_no_checks_as_success(self) -> None:
        with (
            mock.patch.object(cli, "ensure_gh_available"),
            mock.patch.object(cli, "resolve_pr", return_value="21"),
            mock.patch.object(cli, "fetch_checks", return_value=[]),
        ):
            payload, exit_code = cli.inspect_pr_failures(
                repo="owner/repo",
                repo_root=None,
                pr_value="21",
                max_lines=160,
                context=30,
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["summary"], "no_checks")
        self.assertEqual(payload["checkCount"], 0)
        self.assertEqual(payload["failingCount"], 0)
        self.assertEqual(payload["results"], [])
        self.assertIn("no checks configured", payload["message"])
        self.assertEqual(
            cli.render_results(payload),
            "PR #21 in owner/repo: no checks configured or reported.\n",
        )

    def test_shipped_artifact_reports_empty_rollup_as_no_checks(self) -> None:
        artifact = Path(__file__).resolve().parents[3] / "scripts" / "g"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fake_gh = root / "gh"
            fake_gh.write_text(
                "#!/usr/bin/env python3\n"
                "import json\n"
                "import sys\n"
                "args = sys.argv[1:]\n"
                "if args == ['auth', 'status']:\n"
                "    raise SystemExit(0)\n"
                "if args[:2] == ['pr', 'checks']:\n"
                "    raise SystemExit(1)\n"
                "if args == ['pr', 'view', '21', '--json', 'statusCheckRollup', '--repo', 'owner/repo']:\n"
                "    print(json.dumps({'statusCheckRollup': []}))\n"
                "    raise SystemExit(0)\n"
                "print('unexpected fake gh arguments', args, file=sys.stderr)\n"
                "raise SystemExit(2)\n",
                encoding="utf-8",
            )
            fake_gh.chmod(0o755)
            environment = os.environ.copy()
            environment["PATH"] = f"{root}:{environment['PATH']}"
            completed = subprocess.run(
                [
                    str(artifact),
                    "--json",
                    "ci",
                    "inspect",
                    "--repo",
                    "owner/repo",
                    "--pr",
                    "21",
                    "--allow-non-project",
                ],
                cwd=root,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(
            completed.returncode,
            0,
            f"stderr:\n{completed.stderr}\nstdout:\n{completed.stdout}",
        )
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["data"]["summary"], "no_checks")
        self.assertEqual(payload["data"]["checkCount"], 0)

    def test_permissions_preflight_reads_actions_and_workflow_settings(self) -> None:
        gh_results = [
            cli.GhResult(0, "", ""),
            cli.GhResult(0, json.dumps({"enabled": True}), ""),
            cli.GhResult(
                0,
                json.dumps(
                    {
                        "default_workflow_permissions": "read",
                        "can_approve_pull_request_reviews": True,
                    }
                ),
                "",
            ),
        ]
        stdout = io.StringIO()
        with (
            mock.patch.object(cli, "which", return_value="/opt/homebrew/bin/gh"),
            mock.patch.object(cli, "run_gh_command", side_effect=gh_results) as run_gh,
            contextlib.redirect_stdout(stdout),
        ):
            code = cli.main(
                [
                    "--json",
                    "permissions",
                    "--repo",
                    "owner/repo",
                    "--allow-non-project",
                ]
            )

        self.assertEqual(code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["command"], ["permissions"])
        data = payload["data"]
        self.assertTrue(data["actions_enabled"])
        self.assertTrue(data["can_approve_pull_request_reviews"])
        self.assertEqual(data["pull_requests_write"]["repository_gate"], "enabled")
        self.assertEqual(data["pull_requests_write"]["effective"], "not-verifiable-before-workflow-run")
        self.assertEqual(data["workflow_authoring"]["status"], "ready")
        self.assertIsNone(data["workflow_authoring"]["warning"])
        self.assertEqual(
            run_gh.call_args_list[1].args[0][:2],
            ["api", "repos/owner/repo/actions/permissions"],
        )
        self.assertEqual(
            run_gh.call_args_list[2].args[0][:2],
            ["api", "repos/owner/repo/actions/permissions/workflow"],
        )

    def test_permissions_preflight_reports_api_denial_without_mutating(self) -> None:
        gh_results = [
            cli.GhResult(0, "", ""),
            cli.GhResult(403, "", "HTTP 403: requires Administration read permission"),
        ]
        stdout = io.StringIO()
        with (
            mock.patch.object(cli, "which", return_value="/opt/homebrew/bin/gh"),
            mock.patch.object(cli, "run_gh_command", side_effect=gh_results),
            contextlib.redirect_stdout(stdout),
        ):
            code = cli.main(
                [
                    "--json",
                    "permissions",
                    "--repo",
                    "owner/repo",
                    "--allow-non-project",
                ]
            )

        self.assertEqual(code, 1)
        payload = json.loads(stdout.getvalue())
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["command"], ["permissions"])
        self.assertIn("Administration read permission", payload["error"]["message"])

    def test_permissions_preflight_warns_but_does_not_block_workflow_authoring(self) -> None:
        gh_results = [
            cli.GhResult(0, "", ""),
            cli.GhResult(0, json.dumps({"enabled": True}), ""),
            cli.GhResult(
                0,
                json.dumps(
                    {
                        "default_workflow_permissions": "read",
                        "can_approve_pull_request_reviews": False,
                    }
                ),
                "",
            ),
        ]
        with (
            mock.patch.object(cli, "which", return_value="/opt/homebrew/bin/gh"),
            mock.patch.object(cli, "run_gh_command", side_effect=gh_results),
        ):
            payload = cli.inspect_actions_permissions(repo="owner/repo", repo_root=None)

        self.assertEqual(payload["pull_requests_write"]["repository_gate"], "blocked")
        self.assertEqual(payload["workflow_authoring"]["status"], "allowed-with-warning")
        self.assertIn("will not work", payload["workflow_authoring"]["warning"])


if __name__ == "__main__":
    unittest.main()
