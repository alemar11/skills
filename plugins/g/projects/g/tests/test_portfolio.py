from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from g import portfolio as cli

class PortfolioScanContractTests(unittest.TestCase):
    def test_version(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = cli.main(["--version"])
        self.assertEqual(code, 0)
        self.assertEqual(stdout.getvalue().strip(), "2.18.5")

    def test_json_doctor_shape(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            cli.main(["--json", "doctor"])
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["version"], "2.18.5")
        self.assertIn("git", payload["checks"])
        self.assertIn("gh", payload["checks"])

    def test_validate_repo(self) -> None:
        self.assertEqual(cli.validate_repo("owner/repo"), "owner/repo")
        with self.assertRaises(cli.PortfolioError):
            cli.validate_repo("bad")


if __name__ == "__main__":
    unittest.main()
