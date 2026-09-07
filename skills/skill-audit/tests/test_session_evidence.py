from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "session-evidence"
loader = importlib.machinery.SourceFileLoader("session_evidence_script", str(SCRIPT_PATH))
spec = importlib.util.spec_from_loader(loader.name, loader)
assert spec is not None
cli = importlib.util.module_from_spec(spec)
sys.modules[loader.name] = cli
loader.exec_module(cli)


class SessionEvidenceTests(unittest.TestCase):
    def write_session(self, items: list[dict]) -> Path:
        handle = tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", suffix=".jsonl", delete=False
        )
        with handle:
            for item in items:
                handle.write(json.dumps(item) + "\n")
        return Path(handle.name)

    def test_custom_code_mode_call_captures_worker_metadata(self) -> None:
        target_path = "/repo/skills/example-runner/SKILL.md"
        path = self.write_session(
            [
                {
                    "type": "session_meta",
                    "payload": {
                        "session_id": "worker-1",
                        "timestamp": "2026-07-11T10:00:00Z",
                        "cwd": "/repo",
                        "thread_source": "subagent",
                        "forked_from_id": "root-1",
                    },
                },
                {
                    "type": "event_msg",
                    "payload": {"type": "user_message", "message": "Review the work."},
                },
                {
                    "type": "response_item",
                    "payload": {
                        "type": "custom_tool_call",
                        "id": "call-1",
                        "name": "exec",
                        "input": (
                            "const a = await tools.exec_command({cmd:\"sed -n '1,80p' "
                            f"{target_path}\"}}); "
                            "const b = await tools.exec_command("
                            "{cmd:\"scripts/example-runner --mode branch\"});"
                        ),
                    },
                },
                {
                    "type": "response_item",
                    "payload": {"type": "custom_tool_call_output", "output": "ignored"},
                },
                {
                    "type": "session_meta",
                    "payload": {
                        "session_id": "copied-parent-history",
                        "thread_source": "root",
                    },
                },
            ]
        )
        self.addCleanup(path.unlink, missing_ok=True)
        targets = cli.parse_targets(
            ["example-runner"],
            [target_path],
            ["example-runner=scripts/example-runner"],
        )

        records, session_id = cli.scan_file(path, targets, None)

        self.assertEqual(session_id, "worker-1")
        self.assertEqual(
            {record.source for record in records},
            {"opened-skill-doc", "runtime-command"},
        )
        for record in records:
            self.assertEqual(record.item_id, "call-1")
            self.assertEqual(record.transport, "code-mode-custom-tool")
            self.assertEqual(record.thread_source, "subagent")
            self.assertEqual(record.forked_from_id, "root-1")
            self.assertEqual(record.parent_thread_id, "root-1")

    def test_nested_subagent_parent_metadata_is_supported(self) -> None:
        path = self.write_session(
            [
                {
                    "type": "session_meta",
                    "payload": {
                        "id": "worker-2",
                        "session_id": "root-2",
                        "source": {
                            "subagent": {
                                "thread_spawn": {"parent_thread_id": "root-2"}
                            }
                        },
                    },
                },
                {
                    "type": "response_item",
                    "payload": {
                        "type": "custom_tool_call",
                        "name": "exec",
                        "input": "scripts/example-runner --mode local",
                    },
                },
            ]
        )
        self.addCleanup(path.unlink, missing_ok=True)
        targets = cli.parse_targets(
            ["example-runner"], [], ["example-runner=scripts/example-runner"]
        )

        records, session_id = cli.scan_file(path, targets, None)

        self.assertEqual(session_id, "worker-2")
        self.assertEqual(records[0].thread_source, "subagent")
        self.assertEqual(records[0].parent_thread_id, "root-2")
        self.assertIsNone(records[0].forked_from_id)

    def test_direct_function_call_remains_supported(self) -> None:
        path = self.write_session(
            [
                {"type": "session_meta", "payload": {"id": "root-1", "cwd": "/repo"}},
                {
                    "type": "response_item",
                    "payload": {
                        "type": "function_call",
                        "name": "exec_command",
                        "arguments": '{"cmd":"scripts/session-evidence --version"}',
                    },
                },
            ]
        )
        self.addCleanup(path.unlink, missing_ok=True)
        targets = cli.parse_targets(
            ["skill-audit"],
            [],
            ["skill-audit=scripts/session-evidence"],
        )

        records, _ = cli.scan_file(path, targets, None)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].source, "runtime-command")
        self.assertEqual(records[0].transport, "function-call")

    def test_summary_exposes_transport_and_thread_source(self) -> None:
        target = cli.Target("example-runner", ("example-runner",), (), ())
        record = cli.Evidence(
            target="example-runner",
            source="opened-skill-doc",
            timestamp="2026-07-11T10:00:00Z",
            session_id="worker-1",
            cwd="/repo",
            path="session.jsonl",
            transport="code-mode-custom-tool",
            thread_source="subagent",
            forked_from_id="root-1",
            parent_thread_id="root-1",
        )

        summary = cli.summarize(
            [target],
            [record],
            8,
            include_zero=False,
            since=None,
            roots=[Path("/sessions")],
            files_scanned=1,
            sessions_scanned=1,
        )

        data = summary["targets"]["example-runner"]
        self.assertEqual(data["evidence_records"], 1)
        self.assertNotIn("events", data)
        self.assertEqual(data["transports"], {"code-mode-custom-tool": 1})
        self.assertEqual(data["thread_sources"], {"subagent": 1})
        self.assertEqual(data["examples"][0]["forked_from_id"], "root-1")
        self.assertEqual(data["examples"][0]["parent_thread_id"], "root-1")

    def test_copied_item_identity_is_deduplicated_across_sessions(self) -> None:
        records = [
            cli.Evidence(
                target="example-runner",
                source="runtime-command",
                timestamp="2026-07-11T10:00:00Z",
                session_id=session_id,
                cwd="/repo",
                path=f"{session_id}.jsonl",
                item_id="call-shared",
                detail=detail,
            )
            for session_id, detail in (
                ("root-1", "scripts/example-runner --mode local"),
                ("worker-copy", "copied detail should not create another record"),
            )
        ]

        deduped = cli.dedupe(records)

        self.assertEqual(len(deduped), 1)
        self.assertEqual(deduped[0].session_id, "root-1")

    def test_legacy_calls_with_distinct_details_are_retained(self) -> None:
        records = [
            cli.Evidence(
                target="example-runner",
                source="runtime-command",
                timestamp="2026-07-11T10:00:00Z",
                session_id="root-1",
                cwd="/repo",
                path="root-1.jsonl",
                prompt="Review this branch",
                detail=detail,
            )
            for detail in (
                "scripts/example-runner --mode local",
                "scripts/example-runner --mode branch",
            )
        ]

        self.assertEqual(len(cli.dedupe(records)), 2)

    def test_scan_json_uses_v1_envelope_and_evidence_records(self) -> None:
        path = self.write_session(
            [
                {
                    "type": "session_meta",
                    "payload": {"id": "root-1", "cwd": "/repo"},
                },
                {
                    "timestamp": "2026-07-11T10:00:00Z",
                    "type": "event_msg",
                    "payload": {
                        "type": "user_message",
                        "id": "user-1",
                        "message": "Use $skill-audit",
                    },
                },
            ]
        )
        self.addCleanup(path.unlink, missing_ok=True)

        result = subprocess.run(
            [
                str(SCRIPT_PATH),
                "--json",
                "scan",
                "--target",
                "skill-audit",
                "--root",
                str(path),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["version"], "1.0.0")
        self.assertEqual(payload["command"], ["scan"])
        self.assertTrue(payload["ok"])
        target = payload["data"]["targets"]["skill-audit"]
        self.assertEqual(target["evidence_records"], 1)
        self.assertNotIn("events", target)
        self.assertEqual(target["examples"][0]["item_id"], "user-1")

    def test_version_and_doctor_use_v1_contract(self) -> None:
        version = subprocess.run(
            [str(SCRIPT_PATH), "--version"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(version.returncode, 0, version.stderr)
        self.assertEqual(version.stdout.strip(), "session-evidence 1.0.0")

        doctor = subprocess.run(
            [str(SCRIPT_PATH), "--json", "doctor"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(doctor.returncode, 0, doctor.stderr)
        payload = json.loads(doctor.stdout)
        self.assertEqual(payload["version"], "1.0.0")
        self.assertEqual(payload["command"], ["doctor"])
        self.assertTrue(payload["ok"])


if __name__ == "__main__":
    unittest.main()
