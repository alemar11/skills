from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SOURCE = Path(__file__).resolve().parents[1] / "src"


class RetiredCommandsTests(unittest.TestCase):
    def test_removed_commands_cannot_contact_a_provider(self) -> None:
        commands = [
            ["repo", "resolve", "--repo", "owner/repo"],
            ["pr", "resolve", "--repo", "owner/repo", "--pr", "1"],
            ["stars", "list"],
            ["stars", "add", "owner/repo"],
            ["stars", "remove", "owner/repo"],
            ["stars", "lists", "list"],
            ["stars", "lists", "items", "UL_test"],
            ["stars", "lists", "delete", "UL_test"],
            ["pr", "delivery-status", "--repo", "owner/repo", "--pr", "1"],
            ["ci", "inspect", "--repo", "owner/repo", "--pr", "1"],
            ["ci", "permissions", "--repo", "owner/repo"],
            ["portfolio", "scan", "--repo", "owner/repo"],
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            log = root / "provider-called"
            fake = root / "gh"
            fake.write_text("#!/bin/sh\nprintf called >> \"$PROVIDER_LOG\"\nexit 97\n")
            fake.chmod(0o755)
            env = dict(os.environ, PATH=str(root), PYTHONPATH=str(SOURCE), PROVIDER_LOG=str(log))
            for command in commands:
                with self.subTest(command=command):
                    result = subprocess.run(
                        [sys.executable, "-m", "g", "--json", *command],
                        env=env, cwd=root, capture_output=True, text=True,
                    )
                    self.assertEqual(result.returncode, 64, result.stderr)
                    self.assertEqual(json.loads(result.stdout)["error"]["code"], "invalid_arguments")
                    self.assertFalse(log.exists(), "Removed command invoked gh")


if __name__ == "__main__":
    unittest.main()
