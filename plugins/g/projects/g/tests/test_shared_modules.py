from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from g.integrity import canonical_json, fingerprint, text_fingerprint
from g.repository import is_repo_reference, normalize_remote


class RepositoryTests(unittest.TestCase):
    def test_normalize_remote_handles_supported_git_url_forms(self) -> None:
        self.assertEqual(
            normalize_remote("git@github.com:owner/repo.git"), "owner/repo"
        )
        self.assertEqual(
            normalize_remote("https://github.com/owner/repo.git"), "owner/repo"
        )
        self.assertEqual(
            normalize_remote("ssh://github.com/owner/repo.git"), "owner/repo"
        )

    def test_repository_reference_requires_exact_owner_and_name(self) -> None:
        self.assertTrue(is_repo_reference("owner/repo"))
        self.assertFalse(is_repo_reference("owner/repo/extra"))
        self.assertFalse(is_repo_reference("owner only"))


class IntegrityTests(unittest.TestCase):
    def test_fingerprint_uses_canonical_key_order(self) -> None:
        left = {"b": 2, "a": 1}
        right = {"a": 1, "b": 2}

        self.assertEqual(canonical_json(left), '{"a":1,"b":2}')
        self.assertEqual(fingerprint(left), fingerprint(right))
        self.assertEqual(fingerprint(left), text_fingerprint(canonical_json(left)))


if __name__ == "__main__":
    unittest.main()
