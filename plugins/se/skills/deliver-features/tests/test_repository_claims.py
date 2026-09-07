import json
import os
import sqlite3
import subprocess
import tempfile
import threading
import unittest
from contextlib import closing
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
CLI = SKILL / "scripts/repository-claims"
CLAIM_A = "a" * 32
CLAIM_B = "b" * 32


class RepositoryClaimsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name).resolve() / "registry"
        self.database = self.directory / "repository-claims.sqlite3"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_cli(
        self,
        *arguments: str,
        check: bool = True,
        claim_token: str | None = None,
    ) -> tuple[subprocess.CompletedProcess[str], dict]:
        process = subprocess.run(
            [str(CLI), "--json", "--db", str(self.database), *arguments],
            input=claim_token,
            text=True,
            capture_output=True,
            check=False,
        )
        payload = json.loads(process.stdout)
        if check and process.returncode != 0:
            self.fail(f"CLI failed: {payload}\n{process.stderr}")
        return process, payload

    def acquire(self, token: str = CLAIM_A, *repositories: str) -> dict:
        selected = repositories or ("github:101",)
        arguments = [
            "acquire",
            "--home-project-key",
            "project:testing",
        ]
        for repository in selected:
            arguments.extend(["--repository-key", repository])
        return self.run_cli(*arguments, claim_token=token)[1]["result"]

    def test_version_and_absent_doctor_are_read_only(self) -> None:
        version = subprocess.run(
            [str(CLI), "--version"], text=True, capture_output=True, check=True
        )
        self.assertEqual(version.stdout.strip(), "5.1.2")
        result = self.run_cli("doctor")[1]["result"]
        self.assertEqual(result["status"], "absent")
        self.assertFalse(self.directory.exists())

    def test_exact_schema_delete_journal_and_permissions(self) -> None:
        self.acquire()
        self.assertEqual(self.directory.stat().st_mode & 0o777, 0o700)
        self.assertEqual(self.database.stat().st_mode & 0o777, 0o600)
        with closing(sqlite3.connect(self.database)) as connection, connection:
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 1)
            columns = tuple(
                row[1]
                for row in connection.execute("PRAGMA table_info(repository_claims)")
            )
            self.assertEqual(
                columns,
                (
                    "repository_key",
                    "claim_token",
                    "home_project_key",
                    "orchestrator_task_id",
                    "claimed_at",
                ),
            )
            self.assertNotEqual(connection.execute("PRAGMA journal_mode").fetchone()[0], "wal")

    def test_bind_inspect_and_bound_release_full_group(self) -> None:
        self.acquire(CLAIM_A, "github:101", "github:202")
        bound = self.run_cli(
            "bind",
            "--orchestrator-task-id",
            "task-1",
            claim_token=CLAIM_A,
        )[1]["result"]
        self.assertEqual(bound["disposition"], "bound")
        inspected = self.run_cli(
            "inspect", "--repository-key", "github:101", "--repository-key", "github:202"
        )[1]["result"]
        self.assertEqual(len(inspected["claims"]), 2)
        self.assertTrue(all("claim_token" not in row for row in inspected["claims"]))
        self.assertEqual(
            {row["orchestrator_task_id"] for row in inspected["claims"]}, {"task-1"}
        )
        released = self.run_cli(
            "release",
            "--orchestrator-task-id",
            "task-1",
            claim_token=CLAIM_A,
        )[1]["result"]
        self.assertEqual(released["released_repository_keys"], ["github:101", "github:202"])
        self.assertEqual(self.run_cli("inspect")[1]["result"]["claims"], [])

    def test_overlap_rolls_back_complete_request(self) -> None:
        self.acquire(CLAIM_A, "github:101", "github:202")
        process, payload = self.run_cli(
            "acquire",
            "--home-project-key",
            "project:testing",
            "--repository-key",
            "github:202",
            "--repository-key",
            "github:303",
            check=False,
            claim_token=CLAIM_B,
        )
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(payload["error"]["code"], "repository-claimed")
        self.assertNotIn(CLAIM_A, payload["error"]["message"])
        self.assertEqual(
            self.run_cli("inspect", "--repository-key", "github:303")[1]["result"]["claims"],
            [],
        )

    def test_disjoint_claims_can_coexist(self) -> None:
        self.acquire(CLAIM_A, "github:101")
        self.acquire(CLAIM_B, "github:202")
        claims = self.run_cli("inspect")[1]["result"]["claims"]
        self.assertEqual({row["repository_key"] for row in claims}, {"github:101", "github:202"})
        self.assertTrue(all("claim_token" not in row for row in claims))

    def test_one_orchestrator_task_cannot_bind_multiple_claim_tokens(self) -> None:
        self.acquire(CLAIM_A, "github:101")
        self.acquire(CLAIM_B, "github:202")
        self.run_cli(
            "bind",
            "--orchestrator-task-id",
            "task-1",
            claim_token=CLAIM_A,
        )
        process, payload = self.run_cli(
            "bind",
            "--orchestrator-task-id",
            "task-1",
            check=False,
            claim_token=CLAIM_B,
        )
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(payload["error"]["code"], "orchestrator-already-bound")

    def test_same_claim_reuses_provisional_and_bound_group(self) -> None:
        self.assertEqual(self.acquire(CLAIM_A, "github:101")["disposition"], "acquired")
        self.assertEqual(
            self.acquire(CLAIM_A, "github:101")["disposition"],
            "reconcile-provisional",
        )
        self.run_cli(
            "bind",
            "--orchestrator-task-id",
            "task-1",
            claim_token=CLAIM_A,
        )
        self.assertEqual(self.acquire(CLAIM_A, "github:101")["disposition"], "reuse-bound")

    def test_existing_token_cannot_expand_repository_set(self) -> None:
        self.acquire(CLAIM_A, "github:101")
        process, payload = self.run_cli(
            "acquire",
            "--home-project-key",
            "project:testing",
            "--repository-key",
            "github:101",
            "--repository-key",
            "github:202",
            check=False,
            claim_token=CLAIM_A,
        )
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(payload["error"]["code"], "repository-set-expansion-unsupported")

    def test_bind_is_idempotent_and_conflicting_rebind_fails(self) -> None:
        self.acquire()
        arguments = (
            "bind",
            "--orchestrator-task-id",
            "task-1",
        )
        self.run_cli(*arguments, claim_token=CLAIM_A)
        self.assertEqual(
            self.run_cli(*arguments, claim_token=CLAIM_A)[1]["result"]["disposition"],
            "already-bound",
        )
        process, payload = self.run_cli(
            "bind",
            "--orchestrator-task-id",
            "task-2",
            check=False,
            claim_token=CLAIM_A,
        )
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(payload["error"]["code"], "binding-conflict")

    def test_provisional_release_requires_explicit_assertion(self) -> None:
        self.acquire()
        process, payload = self.run_cli(
            "release", check=False, claim_token=CLAIM_A
        )
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(payload["error"]["code"], "invalid-input")
        result = self.run_cli(
            "release", "--abandon-provisional", claim_token=CLAIM_A
        )[1]["result"]
        self.assertEqual(result["disposition"], "released")

    def test_claim_token_is_a_required_fencing_capability(self) -> None:
        process, payload = self.run_cli(
            "acquire",
            "--home-project-key",
            "project:testing",
            "--repository-key",
            "github:101",
            check=False,
        )
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(payload["error"]["code"], "invalid-input")

        process, payload = self.run_cli(
            "acquire",
            "--home-project-key",
            "project:testing",
            "--repository-key",
            "github:101",
            check=False,
            claim_token="predictable-token",
        )
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(payload["error"]["code"], "invalid-input")
        for command in ("acquire", "bind", "inspect", "release"):
            help_text = subprocess.run(
                [str(CLI), command, "--help"],
                text=True,
                capture_output=True,
                check=True,
            ).stdout
            self.assertNotIn("--claim-token", help_text)

    def test_retired_token_argument_is_rejected_without_echoing_secret(self) -> None:
        process, payload = self.run_cli(
            "acquire",
            "--home-project-key",
            "project:testing",
            "--repository-key",
            "github:101",
            "--claim-token",
            CLAIM_A,
            check=False,
        )
        self.assertEqual(process.returncode, 2)
        self.assertEqual(payload["error"]["code"], "invalid-input")
        self.assertNotIn(CLAIM_A, process.stdout)
        self.assertNotIn(CLAIM_A, process.stderr)
        self.assertEqual(process.stderr, "")
        self.assertFalse(self.directory.exists())

    def test_parser_failures_are_structured_and_read_only(self) -> None:
        cases = (
            (),
            ("unknown-command",),
            ("acquire",),
            ("acquire", "--home-project-key"),
            ("doctor", "--unknown-option"),
            ("doctor", "--json"),
        )
        for arguments in cases:
            with self.subTest(arguments=arguments):
                process = subprocess.run(
                    [
                        str(CLI),
                        "--json",
                        "--db",
                        str(self.database),
                        *arguments,
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(process.returncode, 2)
                self.assertEqual(process.stderr, "")
                self.assertEqual(
                    json.loads(process.stdout)["error"]["code"], "invalid-input"
                )
                self.assertFalse(self.directory.exists())

        malformed_json = subprocess.run(
            [
                str(CLI),
                "--json=invalid",
                "--db",
                str(self.database),
                "doctor",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(malformed_json.returncode, 2)
        self.assertEqual(malformed_json.stderr, "")
        self.assertEqual(
            json.loads(malformed_json.stdout)["error"]["code"], "invalid-input"
        )
        self.assertFalse(self.directory.exists())

    def test_command_receipts_never_disclose_fencing_token(self) -> None:
        acquired = self.acquire()
        self.assertNotIn(CLAIM_A, json.dumps(acquired))
        bound = self.run_cli(
            "bind",
            "--orchestrator-task-id",
            "task-1",
            claim_token=CLAIM_A,
        )[1]["result"]
        self.assertNotIn(CLAIM_A, json.dumps(bound))
        released = self.run_cli(
            "release",
            "--orchestrator-task-id",
            "task-1",
            claim_token=CLAIM_A,
        )[1]["result"]
        self.assertNotIn(CLAIM_A, json.dumps(released))

    def test_release_cannot_remove_part_of_group(self) -> None:
        self.acquire(CLAIM_A, "github:101", "github:202")
        help_text = subprocess.run(
            [str(CLI), "release", "--help"],
            text=True,
            capture_output=True,
            check=True,
        ).stdout
        self.assertNotIn("--repository-key", help_text)
        self.assertIn("--abandon-provisional", help_text)
        self.assertNotIn("--provisional", help_text)
        self.assertNotIn("--claim-token", help_text)
        self.run_cli(
            "release", "--abandon-provisional", claim_token=CLAIM_A
        )
        self.assertEqual(self.run_cli("inspect")[1]["result"]["claims"], [])

    def test_doctor_detects_corrupt_group(self) -> None:
        self.acquire(CLAIM_A, "github:101", "github:202")
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute(
                "UPDATE repository_claims SET home_project_key = 'project:other' "
                "WHERE repository_key = 'github:202'"
            )
        process, payload = self.run_cli("doctor", check=False)
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(payload["error"]["code"], "registry-corrupt")

    def test_doctor_and_inspect_reject_non_text_persisted_values(self) -> None:
        self.acquire()
        blob = sqlite3.Binary(b"not-text")
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute(
                "UPDATE repository_claims SET repository_key = ?, claim_token = ?, "
                "home_project_key = ?, orchestrator_task_id = ?, claimed_at = ?",
                (blob, blob, blob, blob, blob),
            )
        for command in ("doctor", "inspect"):
            with self.subTest(command=command):
                process, payload = self.run_cli(command, check=False)
                self.assertEqual(process.returncode, 2)
                self.assertEqual(payload["error"]["code"], "registry-corrupt")
                self.assertEqual(process.stderr, "")

    def test_doctor_detects_task_bound_to_multiple_claims(self) -> None:
        self.acquire(CLAIM_A, "github:101")
        self.acquire(CLAIM_B, "github:202")
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute(
                "UPDATE repository_claims SET orchestrator_task_id = 'task-1'"
            )
        process, payload = self.run_cli("doctor", check=False)
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(payload["error"]["code"], "registry-corrupt")

    def test_doctor_detects_mixed_null_and_literal_null_task_binding(self) -> None:
        self.acquire(CLAIM_A, "github:101", "github:202")
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute(
                "UPDATE repository_claims SET orchestrator_task_id = '<null>' "
                "WHERE repository_key = 'github:202'"
            )
        process, payload = self.run_cli("doctor", check=False)
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(payload["error"]["code"], "registry-corrupt")

    def test_doctor_rejects_counterfeit_schema(self) -> None:
        self.directory.mkdir(mode=0o700)
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute(
                """
                CREATE TABLE repository_claims (
                    repository_key TEXT,
                    claim_token TEXT PRIMARY KEY,
                    home_project_key TEXT,
                    orchestrator_task_id TEXT,
                    claimed_at TEXT
                ) WITHOUT ROWID
                """
            )
            connection.execute("PRAGMA user_version = 1")
        os.chmod(self.database, 0o600)
        process, payload = self.run_cli("doctor", check=False)
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(payload["error"]["code"], "schema-mismatch")

    def test_doctor_rejects_extra_schema_object(self) -> None:
        self.acquire()
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute(
                """
                CREATE TRIGGER reject_insert BEFORE INSERT ON repository_claims
                BEGIN SELECT RAISE(ABORT, 'unexpected'); END
                """
            )
        process, payload = self.run_cli("doctor", check=False)
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(payload["error"]["code"], "schema-mismatch")

    def test_doctor_rejects_extra_constraint_and_collation(self) -> None:
        self.directory.mkdir(mode=0o700)
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.executescript(
                """
                CREATE TABLE repository_claims (
                    repository_key TEXT PRIMARY KEY COLLATE NOCASE,
                    claim_token TEXT NOT NULL,
                    home_project_key TEXT NOT NULL,
                    orchestrator_task_id TEXT,
                    claimed_at TEXT NOT NULL,
                    CHECK (claim_token != 'blocked')
                ) WITHOUT ROWID;
                PRAGMA user_version = 1;
                """
            )
        os.chmod(self.database, 0o600)
        process, payload = self.run_cli("doctor", check=False)
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(payload["error"]["code"], "schema-mismatch")

    def test_repository_key_rejects_noncanonical_alias(self) -> None:
        for alias in (
            "https://github.com:101",
            "github.com:101",
            "github:owner/repository",
            "github:MDEwOlJlcG9zaXRvcnkxMjk2MjY5",
            "github:01296269",
        ):
            with self.subTest(alias=alias):
                process, payload = self.run_cli(
                    "acquire",
                    "--home-project-key",
                    "project:testing",
                    "--repository-key",
                    alias,
                    check=False,
                    claim_token=CLAIM_A,
                )
                self.assertNotEqual(process.returncode, 0)
                self.assertEqual(payload["error"]["code"], "invalid-input")

    def test_doctor_rejects_noncanonical_persisted_identity(self) -> None:
        self.acquire()
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute(
                "UPDATE repository_claims "
                "SET repository_key = 'github:owner/repository'"
            )
        process, payload = self.run_cli("doctor", check=False)
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(payload["error"]["code"], "registry-corrupt")

    def test_existing_custom_parent_permissions_are_not_changed(self) -> None:
        self.directory.mkdir(mode=0o755)
        os.chmod(self.directory, 0o755)
        process, payload = self.run_cli(
            "acquire",
            "--home-project-key",
            "project:testing",
            "--repository-key",
            "github:101",
            check=False,
            claim_token=CLAIM_A,
        )
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(payload["error"]["code"], "unsafe-database-permissions")
        self.assertEqual(self.directory.stat().st_mode & 0o777, 0o755)
        self.assertFalse(self.database.exists())

    def test_inspect_absent_is_read_only_and_does_not_repair_permissions(self) -> None:
        result = self.run_cli("inspect")[1]["result"]
        self.assertEqual(result, {"claims": [], "database_state": "absent"})
        self.assertFalse(self.directory.exists())

        self.acquire()
        os.chmod(self.database, 0o644)
        process, payload = self.run_cli("inspect", check=False)
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(payload["error"]["code"], "unsafe-database-permissions")
        self.assertEqual(self.database.stat().st_mode & 0o777, 0o644)

    def test_database_path_rejects_nested_symlink_ancestor(self) -> None:
        real = Path(self.temporary.name).resolve() / "real"
        nested = real / "nested"
        nested.mkdir(parents=True)
        alias = Path(self.temporary.name).resolve() / "alias"
        alias.symlink_to(real, target_is_directory=True)
        database = alias / "nested/repository-claims.sqlite3"
        process = subprocess.run(
            [str(CLI), "--json", "--db", str(database), "doctor"],
            text=True,
            capture_output=True,
            check=False,
        )
        payload = json.loads(process.stdout)
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(payload["error"]["code"], "unsafe-database-path")

    def test_concurrent_same_token_acquisition_has_one_insert(self) -> None:
        barrier = threading.Barrier(2)
        results: list[dict] = []

        def invoke() -> None:
            barrier.wait()
            _, payload = self.run_cli(
                "acquire",
                "--home-project-key",
                "project:testing",
                "--repository-key",
                "github:101",
                claim_token=CLAIM_A,
            )
            results.append(payload["result"])

        threads = [threading.Thread(target=invoke) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(
            {result["disposition"] for result in results},
            {"acquired", "reconcile-provisional"},
        )
        claims = self.run_cli("inspect")[1]["result"]["claims"]
        self.assertEqual(len(claims), 1)

    def test_concurrent_orchestrators_cannot_both_claim_repository(self) -> None:
        barrier = threading.Barrier(2)
        results: list[tuple[int, dict]] = []

        def invoke(token: str) -> None:
            barrier.wait()
            process, payload = self.run_cli(
                "acquire",
                "--home-project-key",
                "project:testing",
                "--repository-key",
                "github:101",
                check=False,
                claim_token=token,
            )
            results.append((process.returncode, payload))

        threads = [
            threading.Thread(target=invoke, args=(CLAIM_A,)),
            threading.Thread(target=invoke, args=(CLAIM_B,)),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(sorted(code for code, _ in results), [0, 2])
        errors = [payload["error"]["code"] for code, payload in results if code]
        self.assertEqual(errors, ["repository-claimed"])
        claims = self.run_cli("inspect")[1]["result"]["claims"]
        self.assertEqual(len(claims), 1)


if __name__ == "__main__":
    unittest.main()
