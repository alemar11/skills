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

from g import stack
from g.common import GError, Result

SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "g"


class StackContractTests(unittest.TestCase):
    def test_extension_status_accepts_only_official_repository(self) -> None:
        with mock.patch.object(stack.shutil, "which", return_value="/usr/local/bin/gh"), mock.patch.object(
            stack,
            "run",
            return_value=Result(0, "gh stack github/gh-stack v0.0.9\n", ""),
        ) as run:
            status = stack.extension_status()

        self.assertTrue(status["ok"])
        self.assertEqual(status["status"], "ready")
        self.assertEqual(status["repository"], "github/gh-stack")
        self.assertEqual(status["version"], "v0.0.9")
        self.assertEqual(status["publisher_verification"], "not-verified")
        self.assertEqual(run.call_args.args[0], ["gh", "extension", "list"])
        self.assertEqual(run.call_args.kwargs["stdin"], stack.subprocess.DEVNULL)
        self.assertEqual(run.call_args.kwargs["env"]["GIT_TERMINAL_PROMPT"], "0")

    def test_extension_status_reports_missing_gh_without_running_provider(self) -> None:
        with mock.patch.object(stack.shutil, "which", return_value=None), mock.patch.object(stack, "run") as run:
            status = stack.extension_status()

        self.assertFalse(status["ok"])
        self.assertEqual(status["status"], "gh-missing")
        run.assert_not_called()

    def test_extension_status_reports_conflict(self) -> None:
        with mock.patch.object(stack.shutil, "which", return_value="/usr/local/bin/gh"), mock.patch.object(
            stack,
            "run",
            return_value=Result(0, "gh stack someone/gh-stack v1.0.0\n", ""),
        ):
            status = stack.extension_status()

        self.assertFalse(status["ok"])
        self.assertEqual(status["status"], "conflict")
        self.assertEqual(status["repository"], "someone/gh-stack")

    def test_extension_status_ignores_other_installed_extensions(self) -> None:
        with mock.patch.object(stack.shutil, "which", return_value="/usr/local/bin/gh"), mock.patch.object(
            stack,
            "run",
            return_value=Result(0, "gh attach enthus-appdev/gh-attach v0.6.0\n", ""),
        ):
            status = stack.extension_status()

        self.assertEqual(status["status"], "missing")
        self.assertFalse(status["installed"])

    def test_extension_status_fails_closed_on_unparseable_listing(self) -> None:
        with mock.patch.object(stack.shutil, "which", return_value="/usr/local/bin/gh"), mock.patch.object(
            stack,
            "run",
            return_value=Result(0, "unexpected output\n", ""),
        ):
            status = stack.extension_status()

        self.assertEqual(status["status"], "unverified")
        self.assertFalse(status["installed"])
        self.assertEqual(status["reason"], "unparseable-output")

    def test_extension_status_fails_closed_on_partial_stack_listing(self) -> None:
        with mock.patch.object(stack.shutil, "which", return_value="/usr/local/bin/gh"), mock.patch.object(
            stack,
            "run",
            return_value=Result(0, "gh stack\n", ""),
        ):
            status = stack.extension_status()

        self.assertEqual(status["status"], "unverified")
        self.assertEqual(status["reason"], "missing-repository")
        self.assertEqual(status["repository"], stack.EXTENSION_REPOSITORY)
        self.assertIsNone(status["detected_repository"])

    def test_extension_status_rejects_invalid_stack_repository_as_unverified(self) -> None:
        with mock.patch.object(stack.shutil, "which", return_value="/usr/local/bin/gh"), mock.patch.object(
            stack,
            "run",
            return_value=Result(0, "gh stack not-a-repository v1.0.0\n", ""),
        ):
            status = stack.extension_status()

        self.assertEqual(status["status"], "unverified")
        self.assertEqual(status["reason"], "invalid-repository")

    def test_extension_status_preserves_safe_listing_failure_details(self) -> None:
        with mock.patch.object(stack.shutil, "which", return_value="/usr/local/bin/gh"), mock.patch.object(
            stack,
            "run",
            return_value=Result(17, "", "authentication failure"),
        ):
            status = stack.extension_status()

        self.assertEqual(status["status"], "unverified")
        self.assertEqual(status["reason"], "command-failed")
        self.assertEqual(status["list_exit_code"], 17)
        self.assertEqual(status["upstream_command"], ["gh", "extension", "list"])

    def test_extension_status_requires_a_detected_version(self) -> None:
        with mock.patch.object(stack.shutil, "which", return_value="/usr/local/bin/gh"), mock.patch.object(
            stack,
            "run",
            return_value=Result(0, "gh stack github/gh-stack\n", ""),
        ):
            status = stack.extension_status()

        self.assertEqual(status["status"], "unverified")
        self.assertEqual(status["reason"], "missing-version")
        self.assertEqual(status["detected_repository"], "github/gh-stack")

    def test_ensure_surfaces_safe_extension_listing_failure_details(self) -> None:
        status = {
            "status": "unverified",
            "reason": "command-failed",
            "list_exit_code": 17,
            "upstream_command": ["gh", "extension", "list"],
        }
        with mock.patch.object(stack, "extension_status", return_value=status):
            with self.assertRaises(GError) as raised:
                stack.ensure()

        self.assertEqual(raised.exception.code, "extension_unverified")
        self.assertEqual(
            raised.exception.details,
            {
                "upstream_command": ["gh", "extension", "list"],
                "upstream_exit_code": 17,
                "reason": "command-failed",
            },
        )

    def test_ensure_without_install_does_not_run_install(self) -> None:
        missing = {"status": "missing", "repository": "github/gh-stack"}
        with mock.patch.object(stack, "extension_status", return_value=missing), mock.patch.object(stack, "run") as run:
            with self.assertRaises(GError) as raised:
                stack.ensure()

        self.assertEqual(raised.exception.code, "extension_missing")
        run.assert_not_called()

    def test_ensure_install_verifies_the_extension_after_install(self) -> None:
        missing = {"status": "missing", "repository": "github/gh-stack"}
        ready = {
            "status": "ready",
            "ok": True,
            "repository": "github/gh-stack",
            "version": "v0.0.9",
        }
        with mock.patch.object(stack, "extension_status", side_effect=[missing, ready]), mock.patch.object(
            stack,
            "run",
            return_value=Result(0, "installed\n", ""),
        ) as run:
            result = stack.ensure(install=True)

        self.assertEqual(result["action"], "installed")
        self.assertEqual(result["version"], "v0.0.9")
        self.assertEqual(run.call_args.args[0], ["gh", "extension", "install", "github/gh-stack"])

    def test_ensure_does_not_replace_a_conflicting_extension(self) -> None:
        conflict = {"status": "conflict", "repository": "someone/gh-stack"}
        with mock.patch.object(stack, "extension_status", return_value=conflict), mock.patch.object(stack, "run") as run:
            with self.assertRaises(GError) as raised:
                stack.ensure(install=True)

        self.assertEqual(raised.exception.code, "extension_conflict")
        self.assertEqual(
            raised.exception.details,
            {
                "detected_repository": "someone/gh-stack",
                "expected_repository": "github/gh-stack",
            },
        )
        run.assert_not_called()

    def test_ensure_reports_install_failure_without_retrying(self) -> None:
        missing = {"status": "missing", "repository": "github/gh-stack"}
        with mock.patch.object(stack, "extension_status", return_value=missing), mock.patch.object(
            stack,
            "run",
            return_value=Result(12, "", "network failure"),
        ) as run:
            with self.assertRaises(GError) as raised:
                stack.ensure(install=True)

        self.assertEqual(raised.exception.code, "extension_install_failed")
        self.assertEqual(raised.exception.exit_code, 12)
        self.assertEqual(run.call_count, 1)

    def test_execute_forwards_typed_command_and_uses_noninteractive_environment(self) -> None:
        output = io.StringIO()
        with mock.patch.object(stack, "ensure", return_value={"status": "ready"}), mock.patch.object(
            stack,
            "run",
            return_value=Result(0, "pushed\n", ""),
        ) as run, contextlib.redirect_stdout(output):
            code = stack.execute("push", ["--remote", "origin"], json_mode=False)

        self.assertEqual(code, 0)
        self.assertEqual(output.getvalue(), "pushed\n")
        self.assertEqual(run.call_args.args[0], ["gh", "stack", "push", "--remote", "origin"])
        self.assertEqual(run.call_args.kwargs["stdin"], stack.subprocess.DEVNULL)
        self.assertEqual(run.call_args.kwargs["env"]["GH_PAGER"], "cat")
        self.assertEqual(run.call_args.kwargs["env"]["GIT_PAGER"], "cat")
        self.assertEqual(run.call_args.kwargs["env"]["PAGER"], "cat")
        self.assertEqual(run.call_args.kwargs["env"]["GIT_TERMINAL_PROMPT"], "0")

    def test_view_json_is_parsed_and_wrapped(self) -> None:
        output = io.StringIO()
        with mock.patch.object(stack, "ensure", return_value={"status": "ready"}), mock.patch.object(
            stack,
            "run",
            return_value=Result(0, '{"branches": []}\n', ""),
        ) as run, contextlib.redirect_stdout(output):
            code = stack.execute("view", [], json_mode=True)

        self.assertEqual(code, 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["command"], ["stack", "view"])
        self.assertEqual(payload["data"], {"branches": []})
        self.assertEqual(run.call_args.args[0], ["gh", "stack", "view", "--json"])

    def test_raw_view_keeps_the_same_machine_readable_contract(self) -> None:
        output = io.StringIO()
        with mock.patch.object(stack, "ensure", return_value={"status": "ready"}), mock.patch.object(
            stack,
            "run",
            return_value=Result(0, '{"branches": []}\n', ""),
        ) as run, contextlib.redirect_stdout(output):
            code = stack.execute_raw(["--", "view"], json_mode=True)

        self.assertEqual(code, 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["command"], ["stack", "raw"])
        self.assertEqual(payload["data"], {"branches": []})
        self.assertEqual(run.call_args.args[0], ["gh", "stack", "view", "--json"])

    def test_view_invalid_json_is_a_structured_provider_error(self) -> None:
        with mock.patch.object(stack, "ensure", return_value={"status": "ready"}), mock.patch.object(
            stack,
            "run",
            return_value=Result(0, "not-json\n", ""),
        ):
            with self.assertRaises(GError) as raised:
                stack.execute("view", [], json_mode=True)

        self.assertEqual(raised.exception.code, "provider_response_invalid")
        self.assertEqual(raised.exception.exit_code, 65)

    def test_view_help_returns_text_in_json_envelope_without_requesting_stack_data(self) -> None:
        for raw in (False, True):
            for flag in ("--help", "-h"):
                with self.subTest(raw=raw, flag=flag):
                    output = io.StringIO()
                    with mock.patch.object(stack, "ensure", return_value={"status": "ready"}), mock.patch.object(
                        stack, "run", return_value=Result(0, "Usage: gh stack view [flags]\n", "")
                    ) as run, contextlib.redirect_stdout(output):
                        if raw:
                            code = stack.execute_raw(["--", "view", flag], json_mode=True)
                        else:
                            code = stack.execute("view", [flag], json_mode=True)

                    self.assertEqual(code, 0)
                    self.assertEqual(
                        json.loads(output.getvalue())["data"],
                        {"stdout": "Usage: gh stack view [flags]\n", "stderr": None},
                    )
                    self.assertEqual(run.call_args.args[0], ["gh", "stack", "view", flag])

    def test_disabled_help_flag_still_requests_and_parses_stack_json(self) -> None:
        output = io.StringIO()
        with mock.patch.object(stack, "ensure", return_value={"status": "ready"}), mock.patch.object(
            stack, "run", return_value=Result(0, '{"branches": []}\n', "")
        ) as run, contextlib.redirect_stdout(output):
            stack.execute("view", ["--help=false"], json_mode=True)

        self.assertEqual(json.loads(output.getvalue())["data"], {"branches": []})
        self.assertEqual(run.call_args.args[0], ["gh", "stack", "view", "--help=false", "--json"])

    def test_non_view_json_is_wrapped_without_parsing_provider_output(self) -> None:
        output = io.StringIO()
        with mock.patch.object(stack, "ensure", return_value={"status": "ready"}), mock.patch.object(
            stack,
            "run",
            return_value=Result(0, "done\n", "notice\n"),
        ) as run, contextlib.redirect_stdout(output):
            code = stack.execute("push", [], json_mode=True)

        self.assertEqual(code, 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["data"], {"stdout": "done\n", "stderr": "notice"})
        self.assertEqual(run.call_args.args[0], ["gh", "stack", "push"])

    def test_interactive_paths_are_rejected_before_extension_execution(self) -> None:
        cases = [
            ("modify", []),
            ("switch", []),
            ("init", []),
            ("add", []),
            ("checkout", []),
            ("submit", []),
            ("submit", ["--auto=false"]),
            ("merge", ["7"]),
            ("merge", ["--yes", "--merge-method", "squash"]),
            ("merge", ["7", "--yes=false"]),
            ("init", ["--prefix", "feat"]),
            ("init", ["--base", "main", "--prefix", "feat"]),
            ("push", ["--tty"]),
        ]
        for command, args in cases:
            with self.subTest(command=command), mock.patch.object(stack, "ensure") as ensure:
                with self.assertRaises(GError) as raised:
                    stack.execute(command, args, json_mode=False)
            self.assertEqual(raised.exception.code, "interactive_command")
            ensure.assert_not_called()

        with mock.patch.object(stack, "ensure") as ensure:
            with self.assertRaises(GError) as raised:
                stack.execute("unstack", [], json_mode=False)
        self.assertEqual(raised.exception.code, "invalid_arguments")
        ensure.assert_not_called()

    def test_raw_commands_keep_the_interactive_block(self) -> None:
        with mock.patch.object(stack, "ensure") as ensure:
            with self.assertRaises(GError) as raised:
                stack.execute_raw(["--", "switch"], json_mode=False)

        self.assertEqual(raised.exception.code, "interactive_command")
        ensure.assert_not_called()

    def test_unstack_allows_an_explicit_local_cleanup(self) -> None:
        with mock.patch.object(stack, "ensure", return_value={"status": "ready"}), mock.patch.object(
            stack,
            "run",
            return_value=Result(0, "removed\n", ""),
        ) as run:
            code = stack.execute("unstack", ["--local"], json_mode=False)

        self.assertEqual(code, 0)
        self.assertEqual(run.call_args.args[0], ["gh", "stack", "unstack", "--local"])

    def test_upstream_exit_code_is_preserved(self) -> None:
        with mock.patch.object(stack, "ensure", return_value={"status": "ready"}), mock.patch.object(
            stack,
            "run",
            return_value=Result(3, "", "conflict"),
        ):
            with self.assertRaises(GError) as raised:
                stack.execute("rebase", [], json_mode=True)

        self.assertEqual(raised.exception.code, "stack_command_failed")
        self.assertEqual(raised.exception.exit_code, 3)

    def test_json_failure_does_not_emit_untrusted_provider_diagnostic(self) -> None:
        output = io.StringIO()
        errors = io.StringIO()
        with mock.patch.object(stack, "ensure", return_value={"status": "ready"}), mock.patch.object(
            stack,
            "run",
            return_value=Result(7, "", "TOKEN=secret-value"),
        ), contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            with self.assertRaises(GError) as raised:
                stack.execute("push", [], json_mode=True)

        self.assertEqual(raised.exception.code, "stack_command_failed")
        self.assertNotIn("secret-value", str(raised.exception))
        self.assertNotIn("secret-value", json.dumps(raised.exception.details))
        self.assertEqual(errors.getvalue(), "")

    def test_cli_json_failure_has_a_structured_secret_safe_envelope(self) -> None:
        output = io.StringIO()
        errors = io.StringIO()
        with mock.patch.object(stack, "extension_status", return_value={"status": "missing"}), mock.patch.object(
            stack,
            "run",
            return_value=Result(12, "", "Authorization: Bearer secret-value"),
        ), contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            code = __import__("g.cli", fromlist=["main"]).main(
                ["--json", "stack", "ensure", "--install"]
            )

        payload = json.loads(output.getvalue())
        self.assertEqual(code, 12)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["code"], "extension_install_failed")
        self.assertNotIn("secret-value", output.getvalue())
        self.assertNotIn("secret-value", errors.getvalue())

    def test_shipped_artifact_uses_fake_gh_without_installing_or_contacting_github(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fake_gh = root / "gh"
            fake_gh.write_text(
                "#!/usr/bin/env python3\n"
                "import json\n"
                "import os\n"
                "from pathlib import Path\n"
                "import sys\n"
                "root = Path(os.environ['FAKE_GH_ROOT'])\n"
                "args = sys.argv[1:]\n"
                "with (root / 'calls.jsonl').open('a', encoding='utf-8') as stream:\n"
                "    json.dump({'args': args, 'cwd': os.getcwd(), 'pager': os.environ.get('PAGER'), 'git_pager': os.environ.get('GIT_PAGER'), 'gh_pager': os.environ.get('GH_PAGER'), 'git_prompt': os.environ.get('GIT_TERMINAL_PROMPT')}, stream)\n"
                "    stream.write('\\n')\n"
                "if args == ['extension', 'list']:\n"
                "    if (root / 'installed').exists() and os.environ.get('FAKE_GH_MODE') != 'install-failure':\n"
                "        print('gh\\tstack\\tgithub/gh-stack\\tv0.0.9')\n"
                "    raise SystemExit(0)\n"
                "if args == ['extension', 'install', 'github/gh-stack']:\n"
                "    if os.environ.get('FAKE_GH_MODE') == 'install-failure':\n"
                "        print('Authorization: Bearer shipped-secret', file=sys.stderr)\n"
                "        raise SystemExit(12)\n"
                "    (root / 'installed').write_text('installed', encoding='utf-8')\n"
                "    print('installed')\n"
                "    raise SystemExit(0)\n"
                "if args == ['stack', 'view', '--json']:\n"
                "    print('{\"branches\": []}')\n"
                "    raise SystemExit(0)\n"
                "if args == ['stack', 'view', '--help']:\n"
                "    print('Usage: gh stack view [flags]')\n"
                "    raise SystemExit(0)\n"
                "if args in (\n"
                "    ['stack', 'init', '--base', 'main', 'layer-a', 'layer-b'],\n"
                "    ['stack', 'rebase', '--upstack'],\n"
                "    ['stack', 'submit', '--auto'],\n"
                "):\n"
                "    print('ok')\n"
                "    raise SystemExit(0)\n"
                "print('unexpected fake gh arguments', args, file=sys.stderr)\n"
                "raise SystemExit(2)\n",
                encoding="utf-8",
            )
            fake_gh.chmod(0o755)
            environment = os.environ.copy()
            environment["FAKE_GH_ROOT"] = str(root)
            environment["PATH"] = f"{root}:{environment['PATH']}"

            installed = subprocess.run(
                [str(SCRIPT), "--json", "stack", "ensure", "--install"],
                cwd=root,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            viewed = subprocess.run(
                [str(SCRIPT), "--json", "stack", "view", "--json"],
                cwd=root,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            help_result = subprocess.run(
                [str(SCRIPT), "--json", "stack", "raw", "--", "view", "--help"],
                cwd=root,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            initialized = subprocess.run(
                [str(SCRIPT), "--json", "stack", "init", "--base", "main", "layer-a", "layer-b"],
                cwd=root,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            rebased = subprocess.run(
                [str(SCRIPT), "--json", "stack", "rebase", "--upstack"],
                cwd=root,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            submitted = subprocess.run(
                [str(SCRIPT), "--json", "stack", "submit", "--auto"],
                cwd=root,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            failure_environment = environment.copy()
            failure_environment["FAKE_GH_MODE"] = "install-failure"
            failed_install = subprocess.run(
                [str(SCRIPT), "--json", "stack", "ensure", "--install"],
                cwd=root,
                env=failure_environment,
                capture_output=True,
                text=True,
                check=False,
            )

            calls = [
                json.loads(line)
                for line in (root / "calls.jsonl").read_text(encoding="utf-8").splitlines()
            ]

        self.assertEqual(installed.returncode, 0, installed.stderr)
        installed_payload = json.loads(installed.stdout)
        self.assertEqual(installed_payload["data"]["action"], "installed")
        self.assertEqual(installed_payload["data"]["publisher_verification"], "not-verified")
        self.assertEqual(viewed.returncode, 0, viewed.stderr)
        self.assertEqual(json.loads(viewed.stdout)["data"], {"branches": []})
        self.assertEqual(help_result.returncode, 0, help_result.stdout or help_result.stderr)
        self.assertEqual(
            json.loads(help_result.stdout)["data"],
            {"stdout": "Usage: gh stack view [flags]\n", "stderr": None},
        )
        for command in (initialized, rebased, submitted):
            self.assertEqual(command.returncode, 0, command.stderr)
            self.assertEqual(json.loads(command.stdout)["data"], {"stdout": "ok\n", "stderr": None})
        self.assertEqual(failed_install.returncode, 12)
        self.assertEqual(json.loads(failed_install.stdout)["error"]["code"], "extension_install_failed")
        self.assertNotIn("shipped-secret", failed_install.stdout)
        self.assertNotIn("shipped-secret", failed_install.stderr)
        self.assertIn(
            ["extension", "install", "github/gh-stack"],
            [call["args"] for call in calls],
        )
        install_call = next(
            call
            for call in calls
            if call["args"] == ["extension", "install", "github/gh-stack"]
        )
        self.assertEqual(install_call["pager"], "cat")
        self.assertEqual(install_call["git_pager"], "cat")
        self.assertEqual(install_call["gh_pager"], "cat")
        self.assertEqual(install_call["git_prompt"], "0")
        view_call = next(call for call in calls if call["args"][:2] == ["stack", "view"])
        self.assertEqual(view_call["args"], ["stack", "view", "--json"])
        self.assertEqual(view_call["cwd"], str(root.resolve()))
        self.assertEqual(view_call["pager"], "cat")
        self.assertEqual(view_call["git_pager"], "cat")
        self.assertEqual(view_call["gh_pager"], "cat")
        self.assertEqual(view_call["git_prompt"], "0")
        help_call = next(call for call in calls if call["args"] == ["stack", "view", "--help"])
        self.assertEqual(help_call["cwd"], str(root.resolve()))
        self.assertEqual(help_call["git_prompt"], "0")


if __name__ == "__main__":
    unittest.main()
