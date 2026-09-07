from __future__ import annotations

import contextlib
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from urllib import error, parse

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from g import attachment, cli
from g.common import GError


class FakeResponse:
    def __init__(self, payload: bytes):
        self.payload = payload

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self, limit: int) -> bytes:
        return self.payload[:limit]


class AttachmentContractTests(unittest.TestCase):
    SVG = b'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16"/>'
    STABLE_URL = "https://github.com/user-attachments/assets/415a5dc8-41ba-4983-b898-c8a2f3afcf44"

    def _file(self, directory: str, name: str = "proof.svg") -> Path:
        path = Path(directory) / name
        path.write_bytes(self.SVG)
        return path

    def _provider_results(self) -> list[mock.Mock]:
        return [
            mock.Mock(
                returncode=0,
                stdout=json.dumps({"id": 1322661653, "full_name": "owner/repo"}).encode(),
                stderr=b"",
            ),
            mock.Mock(returncode=0, stdout=b"github_pat_secret-test\n", stderr=b""),
        ]

    def test_dry_run_is_local_and_returns_only_file_proof(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._file(directory, "file with spaces.svg")
            with mock.patch("g.attachment.subprocess.run") as run, mock.patch(
                "g.attachment.request.urlopen"
            ) as urlopen:
                result = attachment.upload(
                    repo="owner/repo",
                    file=str(path),
                    dry_run=True,
                )

        self.assertEqual(
            result,
            {
                "dry_run": True,
                "repository": "owner/repo",
                "file": {
                    "name": "file with spaces.svg",
                    "content_type": "image/svg+xml",
                    "bytes": len(self.SVG),
                    "sha256": hashlib.sha256(self.SVG).hexdigest(),
                },
                "url": None,
            },
        )
        run.assert_not_called()
        urlopen.assert_not_called()

    def test_upload_resolves_rest_id_and_posts_opaque_binary_body(self) -> None:
        requests = []

        def open_url(upload_request: object, *, timeout: int) -> FakeResponse:
            requests.append((upload_request, timeout))
            return FakeResponse(json.dumps({"url": self.STABLE_URL}).encode())

        with tempfile.TemporaryDirectory() as directory:
            path = self._file(directory, "local.svg")
            with mock.patch(
                "g.attachment.subprocess.run", side_effect=self._provider_results()
            ) as run:
                result = attachment.upload(
                    repo="owner/repo",
                    file=str(path),
                    name="published proof.svg",
                    opener=open_url,
                )

        self.assertEqual(run.call_count, 2)
        self.assertEqual(run.call_args_list[0].args[0], ["gh", "api", "repos/owner/repo"])
        self.assertEqual(run.call_args_list[1].args[0], ["gh", "auth", "token"])
        for call in run.call_args_list:
            self.assertFalse(call.kwargs["shell"])

        self.assertEqual(len(requests), 1)
        upload_request, timeout = requests[0]
        self.assertEqual(timeout, attachment.UPLOAD_TIMEOUT_SECONDS)
        self.assertEqual(upload_request.method, "POST")
        self.assertEqual(upload_request.data, self.SVG)
        query = parse.parse_qs(parse.urlparse(upload_request.full_url).query)
        self.assertEqual(query["name"], ["published proof.svg"])
        self.assertEqual(query["content_type"], ["image/svg+xml"])
        self.assertEqual(query["repository_id"], ["1322661653"])
        self.assertEqual(upload_request.get_header("Authorization"), "Bearer github_pat_secret-test")
        self.assertEqual(result["repository_id"], 1322661653)
        self.assertEqual(result["url"], self.STABLE_URL)
        self.assertNotIn("github_pat_secret-test", json.dumps(result))

    def test_rejects_relative_symlink_empty_and_unknown_type(self) -> None:
        with self.assertRaises(GError) as relative:
            attachment.upload(repo="owner/repo", file="proof.svg", dry_run=True)
        self.assertEqual(relative.exception.code, "invalid_arguments")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            regular = self._file(directory)
            symlink = root / "link.svg"
            symlink.symlink_to(regular)
            with self.assertRaises(GError) as linked:
                attachment.upload(repo="owner/repo", file=str(symlink), dry_run=True)
            self.assertEqual(linked.exception.code, "attachment_file_invalid")

            empty = root / "empty.png"
            empty.touch()
            with self.assertRaises(GError) as empty_error:
                attachment.upload(repo="owner/repo", file=str(empty), dry_run=True)
            self.assertEqual(empty_error.exception.code, "attachment_file_invalid")

            unknown = root / "proof.unknown-extension"
            unknown.write_bytes(b"proof")
            with self.assertRaises(GError) as unknown_error:
                attachment.upload(repo="owner/repo", file=str(unknown), dry_run=True)
            self.assertEqual(unknown_error.exception.code, "invalid_arguments")

    def test_rejects_hostile_name_and_content_type(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._file(directory)
            for name in ("../proof.svg", "proof\n.svg", "proof\\escape.svg"):
                with self.subTest(name=name), self.assertRaises(GError) as raised:
                    attachment.upload(
                        repo="owner/repo",
                        file=str(path),
                        name=name,
                        dry_run=True,
                    )
                self.assertEqual(raised.exception.code, "invalid_arguments")

            with self.assertRaises(GError) as content_type:
                attachment.upload(
                    repo="owner/repo",
                    file=str(path),
                    content_type="image/svg+xml; charset=utf-8",
                    dry_run=True,
                )
            self.assertEqual(content_type.exception.code, "invalid_arguments")

    def test_repository_identity_must_be_numeric_and_exact(self) -> None:
        malformed = mock.Mock(
            returncode=0,
            stdout=json.dumps({"id": "MDQ6UmVwb3NpdG9yeQ==", "full_name": "owner/repo"}).encode(),
            stderr=b"",
        )
        with tempfile.TemporaryDirectory() as directory:
            path = self._file(directory)
            with mock.patch("g.attachment.subprocess.run", return_value=malformed):
                with self.assertRaises(GError) as raised:
                    attachment.upload(repo="owner/repo", file=str(path), opener=mock.Mock())

        self.assertEqual(raised.exception.code, "attachment_repository_invalid")

    def test_http_error_is_redacted_and_typed(self) -> None:
        rejected_body = b'{"message":"secret provider detail"}'
        rejected = error.HTTPError(
            attachment.UPLOAD_ENDPOINT,
            422,
            "Unprocessable Entity",
            None,
            mock.Mock(read=mock.Mock(return_value=rejected_body)),
        )
        with tempfile.TemporaryDirectory() as directory:
            path = self._file(directory)
            with mock.patch(
                "g.attachment.subprocess.run", side_effect=self._provider_results()
            ):
                with self.assertRaises(GError) as raised:
                    attachment.upload(
                        repo="owner/repo",
                        file=str(path),
                        opener=mock.Mock(side_effect=rejected),
                    )

        self.assertEqual(raised.exception.code, "attachment_upload_rejected")
        self.assertEqual(raised.exception.details["http_status"], 422)
        self.assertNotIn("secret provider detail", json.dumps(raised.exception.details))
        self.assertNotIn("github_pat_secret-test", json.dumps(raised.exception.details))

    def test_ambiguous_failure_is_not_retried(self) -> None:
        open_url = mock.Mock(side_effect=error.URLError("connection reset"))
        with tempfile.TemporaryDirectory() as directory:
            path = self._file(directory)
            with mock.patch(
                "g.attachment.subprocess.run", side_effect=self._provider_results()
            ):
                with self.assertRaises(GError) as raised:
                    attachment.upload(repo="owner/repo", file=str(path), opener=open_url)

        self.assertEqual(raised.exception.code, "attachment_upload_unknown")
        open_url.assert_called_once()

    def test_cli_emits_stable_command_envelope(self) -> None:
        payload = {
            "dry_run": True,
            "repository": "owner/repo",
            "file": {"name": "proof.svg"},
            "url": None,
        }
        with mock.patch.object(cli.attachment, "upload", return_value=payload) as upload:
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = cli.main(
                    [
                        "--json",
                        "attachment",
                        "upload",
                        "--repo",
                        "owner/repo",
                        "--file",
                        "/tmp/proof.svg",
                        "--dry-run",
                    ]
                )

        self.assertEqual(code, 0)
        envelope = json.loads(stdout.getvalue())
        self.assertEqual(envelope["command"], ["attachment", "upload"])
        self.assertEqual(envelope["data"], payload)
        upload.assert_called_once_with(
            repo="owner/repo",
            file="/tmp/proof.svg",
            name=None,
            content_type=None,
            dry_run=True,
        )

    def test_shipped_artifact_supports_local_attachment_dry_run(self) -> None:
        artifact = Path(__file__).resolve().parents[3] / "scripts" / "g"
        with tempfile.TemporaryDirectory() as directory:
            path = self._file(directory, "-published proof.svg")
            completed = subprocess.run(
                [
                    str(artifact),
                    "--json",
                    "attachment",
                    "upload",
                    "--repo",
                    "owner/repo",
                    "--file",
                    str(path),
                    "--dry-run",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["version"], "2.18.5")
        self.assertTrue(payload["data"]["dry_run"])
        self.assertEqual(payload["data"]["file"]["name"], "-published proof.svg")


if __name__ == "__main__":
    unittest.main()
