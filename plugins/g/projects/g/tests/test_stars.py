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
from g import stars

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
        self.assertEqual(manifest["version"], "2.18.16")
        self.assertEqual(package["project"]["version"], manifest["version"])
        self.assertEqual(artifact_version, manifest["version"])
        self.assertNotIn("apps", manifest)
        self.assertFalse((plugin_root / ".app.json").exists())

    def test_version(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = self.stars.main(["--version"])
        self.assertEqual(code, 0)
        self.assertEqual(stdout.getvalue().strip(), "2.18.16")

    def test_json_doctor_shape(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            self.stars.main(["--json", "doctor"])
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["version"], "2.18.16")
        self.assertIn("gh", payload["checks"])

    def test_invalid_command_json(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = self.stars.main(["--json", "nope"])
        self.assertEqual(code, 64)
        payload = json.loads(stdout.getvalue())
        self.assertFalse(payload["ok"])

    def test_add_positional_repo_maps_to_repo_flag(self) -> None:
        captured: list[str] = []

        def fake_helper(_main, argv):
            captured.extend(argv)
            return stars.RunResult(0, "", "")

        with mock.patch.object(stars, "helper_result", side_effect=fake_helper):
            self.assertEqual(stars.invoke(["add", "owner/repo"], False), 0)
        self.assertEqual(captured[:3], ["--star", "--repo", "owner/repo"])

    def test_assign_positional_ids_map_to_flags(self) -> None:
        captured: list[str] = []

        def fake_helper(_main, argv):
            captured.extend(argv)
            return stars.RunResult(0, "", "")

        with mock.patch.object(stars, "helper_result", side_effect=fake_helper):
            self.assertEqual(stars.invoke(["lists", "assign", "L1", "owner/repo"], False), 0)
        self.assertEqual(captured[:5], ["--assign", "--list-id", "L1", "--repo", "owner/repo"])


if __name__ == "__main__":
    unittest.main()
