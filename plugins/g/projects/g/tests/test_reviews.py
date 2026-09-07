from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from g import reviews as cli
from g.common import GError, Result
from g.provider_text import ProviderText
from g.review_request import build_request, parse_request, receipt, validate_receipt
from g.review_mutation import (
    add_operation_marker,
    build_reservation,
    operation_id_for_mutation,
    operation_id_for_request,
    packet_fingerprint,
    text_fingerprint,
    thread_identity_fingerprint,
)
from g.review_thread import build_reply_receipt, validate_reply_receipt, validate_resolution_receipt
from g.terminal_evidence import validate_terminal_evidence_receipt
from g.ready_review import build_ready_trigger

class ReviewsContractTests(unittest.TestCase):
    HOSTILE = "`ticks` $(command) ${HOME} $PATH 'single' \"double\"\n-leading\nUnicode ✓ 🚀"

    def setUp(self) -> None:
        def reservation(*_args, **kwargs):
            kind = kwargs["kind"]
            operation_id = "a" * 32
            if kind == "review-request":
                operation_id = operation_id_for_request(
                    kwargs["repo"], kwargs["pr"], kwargs["head"],
                    kwargs["request_key"], kwargs["request_fingerprint"],
                )
            return {
                "schema": "g-review-provider-mutation:v1",
                "reservation_id": "b" * 64,
                "operation_id": operation_id,
                "head_sha": kwargs.get("head") or "b" * 40,
                "body_fingerprint": kwargs.get("body_fingerprint") or "c" * 64,
            }

        self._reservation_patch = mock.patch.object(cli, "_require_reservation", side_effect=reservation)
        self._consume_patch = mock.patch.object(cli, "_consume_reservation")
        self._marked_body_patch = mock.patch.object(cli, "_marked_body", side_effect=lambda body, packet: body)
        self._marker_match_patch = mock.patch.object(cli, "_marker_matches", return_value=True)
        self._reservation_patch.start()
        self._consume_patch.start()
        self._marked_body_patch.start()
        self._marker_match_patch.start()
        self._head_patch = mock.patch.object(cli, "_verify_pr_head")
        self._head_patch.start()
        self.addCleanup(self._reservation_patch.stop)
        self.addCleanup(self._consume_patch.stop)
        self.addCleanup(self._marked_body_patch.stop)
        self.addCleanup(self._marker_match_patch.stop)
        self.addCleanup(self._head_patch.stop)

    def provider_body(self) -> ProviderText:
        return ProviderText("body", self.HOSTILE.encode("utf-8"), self.HOSTILE)

    def frozen_clock(self):
        patcher = mock.patch.object(cli, "datetime")
        clock = patcher.start()
        self.addCleanup(patcher.stop)
        clock.now.return_value = datetime(2026, 7, 20, 12, 0, 0, tzinfo=timezone.utc)
        return clock

    def automated_review_api(
        self, *, reviews=None, inline=None, comments=None, reactions=None,
        issue_reactions=None,
    ):
        payloads = {
            "pulls/12/reviews": reviews or [],
            "pulls/12/comments": inline or [],
            "issues/12/comments": comments or [],
            "issues/12/reactions": issue_reactions or [],
            "issues/comments/99/reactions": reactions or [],
        }

        def read(endpoint: str):
            for suffix, payload in payloads.items():
                if endpoint.endswith(suffix):
                    return payload
            self.fail(f"Unexpected endpoint: {endpoint}")

        return read

    def canonical_request(
        self,
        head: str,
        *,
        comment_id: int = 99,
        created_at: str = "2026-07-15T13:00:00Z",
        request_key: str | None = None,
    ) -> dict[str, object]:
        plan = build_request("codex", "owner/repo", 12, head, request_key or f"request-{comment_id}")
        return {
            "id": comment_id,
            "body": plan.body,
            "html_url": f"https://github.com/owner/repo/pull/12#issuecomment-{comment_id}",
            "issue_url": "https://api.github.com/repos/owner/repo/issues/12",
            "created_at": created_at,
            "user": {"login": "agent"},
        }

    def canonical_receipt(self, head: str, *, comment_id: int = 99, created_at: str = "2026-07-15T13:00:00Z") -> dict[str, object]:
        request = self.canonical_request(head, comment_id=comment_id, created_at=created_at)
        plan = build_request("codex", "owner/repo", 12, head, f"request-{comment_id}")
        return receipt(plan, request, status="posted")

    def ready_trigger(self, head: str, *, ready_at: str = "2026-07-20T12:05:00Z") -> dict[str, object]:
        return build_ready_trigger(
            provider="codex",
            repository="owner/repo",
            pr_number=12,
            head_sha=head,
            ready_event_id="event-123",
            ready_ref="https://github.com/owner/repo/pull/12#event-123",
            ready_at=ready_at,
            base_branch="main",
            body_fingerprint=text_fingerprint("body"),
        )

    def finding(self, *, comment_id: int = 55, head: str | None = None) -> dict[str, object]:
        return {
            "id": comment_id,
            "node_id": f"PRRC_finding_{comment_id}",
            "html_url": f"https://github.com/owner/repo/pull/12#discussion_r{comment_id}",
            "pull_request_url": "https://api.github.com/repos/owner/repo/pulls/12",
            "commit_id": head or "a" * 40,
            "created_at": "2026-07-20T11:00:00Z",
        }

    def reply(self, body: ProviderText, *, comment_id: int = 56, parent_id: int = 55) -> dict[str, object]:
        return {
            "id": comment_id,
            "node_id": f"PRRC_reply_{comment_id}",
            "html_url": f"https://github.com/owner/repo/pull/12#discussion_r{comment_id}",
            "pull_request_url": "https://api.github.com/repos/owner/repo/pulls/12",
            "in_reply_to_id": parent_id,
            "user": {"login": "agent"},
            "body": body.text,
            "created_at": "2026-07-20T12:00:00Z",
        }

    def thread(self, *, resolved: bool = False, outdated: bool = False, head: str | None = None) -> dict[str, object]:
        return {
            "thread_id": "PRRT_thread_55",
            "is_resolved": resolved,
            "is_outdated": outdated,
            "viewer_can_resolve": True,
            "repository": "owner/repo",
            "pr_number": 12,
            "pr_state": "open",
            "head_sha": head or "b" * 40,
            "path": "src/example.py",
            "line": 12,
            "start_line": 12,
            "comments": [
                {"id": "PRRC_finding_55", "databaseId": 55},
                {"id": "PRRC_reply_56", "databaseId": 56},
            ],
        }

    def reply_receipt(self, body: ProviderText) -> dict[str, object]:
        return build_reply_receipt(
            repository="owner/repo",
            pr_number=12,
            finding_head_sha="a" * 40,
            reply_head_sha="b" * 40,
            thread_id="PRRT_thread_55",
            finding=self.finding(),
            reply=self.reply(body),
            body_fingerprint=body.sha256,
            status="replied",
        )

    def test_version(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = cli.main(["--version"])
        self.assertEqual(code, 0)
        self.assertEqual(stdout.getvalue().strip(), "2.18.20")

    def test_json_doctor_shape(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            cli.main(["--json", "doctor"])
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["version"], "2.18.20")
        self.assertIn("git", payload["checks"])
        self.assertIn("gh", payload["checks"])

    def test_positive_int(self) -> None:
        self.assertEqual(cli.positive_int("12", "pr"), 12)
        with self.assertRaises(cli.ReviewError):
            cli.positive_int("0", "pr")

    def test_duration_seconds(self) -> None:
        self.assertEqual(cli.duration_seconds("15m", "timeout"), 900)
        self.assertEqual(cli.duration_seconds("30s", "interval"), 30)
        with self.assertRaises(cli.ReviewError):
            cli.duration_seconds("0s", "timeout")

    def test_request_builder_and_parser_are_strict_and_typed(self) -> None:
        head = "a" * 40
        plan = build_request("codex", "owner/repo", 12, head, "run-01")
        self.assertEqual(
            plan.body,
            f"@codex review {head}\n\n<!-- g-codex-review-request:v1\nrequest_key=run-01\nrequest_fingerprint={plan.request_fingerprint}\n-->\n\n<!-- g-review-provider-mutation:v1\noperation_id={plan.operation_id if hasattr(plan, 'operation_id') else operation_id_for_request('owner/repo', 12, head, 'run-01', plan.request_fingerprint)}\n-->" ,
        )
        self.assertEqual(parse_request(plan.body, "codex", "owner/repo", 12).classification, "canonical")
        self.assertEqual(parse_request("@codex review", "codex", "owner/repo", 12).classification, "unbound")
        self.assertEqual(
            parse_request(f"@codex review {head[:8]}", "codex", "owner/repo", 12).classification,
            "unbound",
        )
        self.assertEqual(
            parse_request(plan.body.replace("request_key=run-01", "request_key=run-02"), "codex", "owner/repo", 12).classification,
            "invalid",
        )
        malformed = parse_request(
            plan.body.replace("request_fingerprint=", "request_fingerprint=0"),
            "codex",
            "owner/repo",
            12,
        )
        self.assertEqual(malformed.classification, "invalid")
        self.assertEqual(malformed.head_sha, head)
        self.assertEqual(
            parse_request(plan.body + "\n", "codex", "owner/repo", 12).classification,
            "invalid",
        )

    def test_typed_request_dry_run_never_accepts_caller_body_text(self) -> None:
        head = "b" * 40
        with mock.patch.object(cli, "_verify_pr_target", return_value={"number": 12, "head": {"sha": head}}), \
             mock.patch.object(cli, "gh_api_paginated_list", return_value=[]), \
             mock.patch.object(cli, "require_worktree", return_value=None), \
             mock.patch.object(cli, "api_request") as mutation:
            action = cli.request_automated_review("owner/repo", 12, "codex", head, "run-02", True, None)
        self.assertEqual(action["status"], "dry-run")
        self.assertEqual(action["request"]["request_key"], "run-02")
        self.assertRegex(action["request"]["request_fingerprint"], r"^[0-9a-f]{64}$")
        self.assertRegex(action["request"]["body_fingerprint"], r"^[0-9a-f]{64}$")
        mutation.assert_not_called()

    def test_typed_request_posts_once_and_returns_complete_receipt(self) -> None:
        head = "c" * 40
        plan = build_request("codex", "owner/repo", 12, head, "run-03")
        item = {
            "id": 401,
            "html_url": "https://github.com/owner/repo/pull/12#issuecomment-401",
            "issue_url": "https://api.github.com/repos/owner/repo/issues/12",
            "user": {"login": "agent"},
            "body": plan.body,
            "created_at": "2026-07-20T12:00:00Z",
        }
        self.frozen_clock()
        with mock.patch.object(cli, "_verify_pr_target", return_value={"number": 12, "head": {"sha": head}}), \
             mock.patch.object(cli, "gh_api_paginated_list", return_value=[]), \
             mock.patch.object(cli, "require_worktree", return_value=None), \
             mock.patch.object(cli, "_viewer_login", return_value="agent"), \
             mock.patch.object(cli, "api_request", return_value=Result(0, json.dumps(item), "")) as mutation:
            action = cli.request_automated_review("owner/repo", 12, "codex", head, "run-03", False, None)
        self.assertEqual(action["status"], "posted")
        request = action["request"]
        self.assertEqual(request["comment_id"], 401)
        self.assertEqual(request["provider_request_id"]["value"], "401")
        self.assertRegex(request["identity_fingerprint"], r"^[0-9a-f]{64}$")
        self.assertEqual(mutation.call_count, 1)
        self.assertEqual(mutation.call_args.args[2]["body"], plan.body)

    def test_receipt_validation_binds_all_fingerprints_and_provider_identity(self) -> None:
        head = "c" * 40
        saved = self.canonical_receipt(head)
        self.assertIs(
            validate_receipt(saved, provider="codex", repository="owner/repo", pr_number=12),
            saved,
        )
        for field in ("request_fingerprint", "body_fingerprint", "identity_fingerprint"):
            with self.subTest(field=field):
                invalid = {**saved, field: "0" * 64}
                with self.assertRaises(ValueError):
                    validate_receipt(
                        invalid,
                        provider="codex",
                        repository="owner/repo",
                        pr_number=12,
                    )

    def test_terminal_evidence_returns_one_exact_fingerprinted_receipt(self) -> None:
        head = "e" * 40
        request = self.canonical_request(head)
        saved = self.canonical_receipt(head)
        artifact = {
            "id": 101,
            "html_url": "https://github.com/owner/repo/pull/12#issuecomment-101",
            "user": {"login": "chatgpt-codex-connector[bot]"},
            "body": f"Codex Review: No issues found.\n\n**Reviewed commit:** `{head[:10]}`",
            "created_at": "2026-07-15T13:05:00Z",
        }
        self.frozen_clock()
        with mock.patch.object(
                 cli,
                 "gh_json",
                 side_effect=[{"head": {"sha": head}}, {"head": {"sha": head}}],
             ) as head_reads, \
             mock.patch.object(
                 cli,
                 "gh_api_paginated_list",
                 side_effect=[[], [], [request, artifact]],
             ), \
             mock.patch.object(cli, "_api_object", side_effect=[request, artifact]):
            result = cli.terminal_provider_evidence("owner/repo", 12, "codex", head, saved)

        self.assertEqual(result["schema"], "g-terminal-provider-evidence:v1")
        self.assertEqual(result["outcome"], "clean")
        self.assertEqual(result["resolved_head_sha"], head)
        self.assertEqual(result["request_identity_fingerprint"], saved["identity_fingerprint"])
        self.assertNotIn("body", result)
        self.assertIs(validate_terminal_evidence_receipt(result), result)
        self.assertEqual(head_reads.call_count, 2)

    def test_terminal_evidence_rejects_head_drift_after_exact_artifact_check(self) -> None:
        head = "e" * 40
        drifted_head = "f" * 40
        request = self.canonical_request(head)
        saved = self.canonical_receipt(head)
        artifact = {
            "id": 101,
            "html_url": "https://github.com/owner/repo/pull/12#issuecomment-101",
            "user": {"login": "chatgpt-codex-connector[bot]"},
            "body": f"Codex Review: No issues found.\n\n**Reviewed commit:** `{head[:10]}`",
            "created_at": "2026-07-15T13:05:00Z",
        }
        with mock.patch.object(
                 cli,
                 "gh_json",
                 side_effect=[
                     {"head": {"sha": head}},
                     {"head": {"sha": drifted_head}},
                 ],
             ) as head_reads, \
             mock.patch.object(
                 cli,
                 "gh_api_paginated_list",
                 side_effect=[[], [], [request, artifact]],
             ), \
             mock.patch.object(cli, "_api_object", side_effect=[request, artifact]), \
             mock.patch.object(cli, "build_terminal_evidence_receipt") as build_receipt, \
             self.assertRaises(cli.ReviewError) as raised:
            cli.terminal_provider_evidence("owner/repo", 12, "codex", head, saved)

        self.assertEqual(raised.exception.code, "terminal_evidence_head_drift")
        self.assertEqual(raised.exception.exit_code, 3)
        self.assertEqual(head_reads.call_count, 2)
        build_receipt.assert_not_called()

    def test_terminal_evidence_rejects_invalid_final_head_proof(self) -> None:
        head = "e" * 40
        request = self.canonical_request(head)
        saved = self.canonical_receipt(head)
        artifact = {
            "id": 101,
            "html_url": "https://github.com/owner/repo/pull/12#issuecomment-101",
            "user": {"login": "chatgpt-codex-connector[bot]"},
            "body": f"Codex Review: No issues found.\n\n**Reviewed commit:** `{head[:10]}`",
            "created_at": "2026-07-15T13:05:00Z",
        }
        with mock.patch.object(
                 cli,
                 "gh_json",
                 side_effect=[{"head": {"sha": head}}, {"head": {"sha": "invalid"}}],
             ), \
             mock.patch.object(
                 cli,
                 "gh_api_paginated_list",
                 side_effect=[[], [], [request, artifact]],
             ), \
             mock.patch.object(cli, "_api_object", side_effect=[request, artifact]), \
             mock.patch.object(cli, "build_terminal_evidence_receipt") as build_receipt, \
             self.assertRaises(cli.ReviewError) as raised:
            cli.terminal_provider_evidence("owner/repo", 12, "codex", head, saved)

        self.assertEqual(raised.exception.code, "terminal_evidence_invalid")
        self.assertEqual(raised.exception.exit_code, 4)
        build_receipt.assert_not_called()

    def test_terminal_evidence_rejects_ambiguous_or_conflicting_lineage(self) -> None:
        head = "e" * 40
        request = self.canonical_request(head)
        saved = self.canonical_receipt(head)
        artifact = {
            "id": 101,
            "html_url": "https://github.com/owner/repo/pull/12#issuecomment-101",
            "user": {"login": "chatgpt-codex-connector[bot]"},
            "body": f"Codex Review: No issues found.\n\n**Reviewed commit:** `{head[:10]}`",
            "created_at": "2026-07-15T13:05:00Z",
        }
        later_request = self.canonical_request(
            head,
            comment_id=102,
            created_at="2026-07-15T13:06:00Z",
        )
        cases = {
            "later-request": ([], [], [request, artifact, later_request]),
            "duplicate-artifact": ([], [], [request, artifact, {**artifact, "id": 103, "html_url": "https://github.com/owner/repo/pull/12#issuecomment-103"}]),
            "inline-finding": ([], [{**self.finding(head=head), "created_at": "2026-07-15T13:04:00Z", "user": {"login": "chatgpt-codex-connector[bot]"}}], [request, artifact]),
            "formal-conflict": ([{"id": 7, "user": {"login": "chatgpt-codex-connector[bot]"}, "commit_id": head, "submitted_at": "2026-07-15T13:04:00Z", "state": "CHANGES_REQUESTED", "body": "Found issues"}], [], [request, artifact]),
        }
        for name, payloads in cases.items():
            with self.subTest(name=name), \
                 mock.patch.object(cli, "gh_json", return_value={"head": {"sha": head}}), \
                 mock.patch.object(cli, "gh_api_paginated_list", side_effect=list(payloads)), \
                 mock.patch.object(cli, "_api_object", return_value=request), \
                 self.assertRaises(cli.ReviewError) as raised:
                cli.terminal_provider_evidence("owner/repo", 12, "codex", head, saved)
            self.assertEqual(raised.exception.code, "terminal_evidence_ambiguous")

    def test_terminal_evidence_reproves_request_and_current_head(self) -> None:
        head = "e" * 40
        saved = self.canonical_receipt(head)
        edited = {**self.canonical_request(head), "body": "@codex review"}
        with mock.patch.object(cli, "gh_json", return_value={"head": {"sha": head}}), \
             mock.patch.object(cli, "_api_object", return_value=edited), \
             self.assertRaises(cli.ReviewError) as request_mismatch:
            cli.terminal_provider_evidence("owner/repo", 12, "codex", head, saved)
        self.assertEqual(request_mismatch.exception.code, "terminal_evidence_request_mismatch")

        with mock.patch.object(cli, "gh_json", return_value={"head": {"sha": "f" * 40}}), \
             self.assertRaises(cli.ReviewError) as head_drift:
            cli.terminal_provider_evidence("owner/repo", 12, "codex", head, saved)
        self.assertEqual(head_drift.exception.code, "terminal_evidence_head_drift")

    def test_uncertain_typed_request_recovers_once_or_returns_request_unknown(self) -> None:
        head = "d" * 40
        plan = build_request("codex", "owner/repo", 12, head, "run-04")
        item = {
            "id": 402,
            "html_url": "https://github.com/owner/repo/pull/12#issuecomment-402",
            "issue_url": "https://api.github.com/repos/owner/repo/issues/12",
            "user": {"login": "agent"},
            "body": plan.body,
            "created_at": "2026-07-20T12:00:00Z",
        }
        self.frozen_clock()
        with mock.patch.object(cli, "_verify_pr_target", return_value={"number": 12, "head": {"sha": head}}), \
             mock.patch.object(cli, "gh_api_paginated_list", side_effect=[[], [item]]) as listing, \
             mock.patch.object(cli, "require_worktree", return_value=None), \
             mock.patch.object(cli, "_viewer_login", return_value="agent"), \
             mock.patch.object(cli, "api_request", return_value=Result(0, "not-json", "")) as mutation:
            action = cli.request_automated_review("owner/repo", 12, "codex", head, "run-04", False, None)
        self.assertEqual(action["status"], "recovered")
        self.assertEqual(action["request"]["comment_id"], 402)
        self.assertEqual(mutation.call_count, 1)
        self.assertEqual(listing.call_count, 2)

        with mock.patch.object(cli, "_verify_pr_target", return_value={"number": 12, "head": {"sha": head}}), \
             mock.patch.object(cli, "gh_api_paginated_list", side_effect=[[], []]) as listing, \
             mock.patch.object(cli, "require_worktree", return_value=None), \
             mock.patch.object(cli, "_viewer_login", return_value="agent"), \
             mock.patch.object(cli, "api_request", return_value=Result(0, "not-json", "")) as mutation, \
             self.assertRaises(cli.ReviewError) as raised:
            cli.request_automated_review("owner/repo", 12, "codex", head, "run-04", False, None)
        self.assertEqual(raised.exception.code, "request_unknown")
        self.assertEqual(mutation.call_count, 1)
        self.assertEqual(listing.call_count, 2)

    def test_typed_request_blocks_unbound_conflicting_and_duplicate_requests(self) -> None:
        head = "e" * 40
        different = self.canonical_request(head, comment_id=2, request_key="other-run")
        exact = self.canonical_request(head, comment_id=3, request_key="run-05")
        duplicate = self.canonical_request(head, comment_id=4, request_key="run-05")
        for comments, expected in (([different], "invalid_request"), ([exact, duplicate], "ambiguous_request")):
            with self.subTest(expected=expected), \
                 mock.patch.object(cli, "_verify_pr_target", return_value={"number": 12, "head": {"sha": head}}), \
                 mock.patch.object(cli, "gh_api_paginated_list", return_value=comments), \
                 mock.patch.object(cli, "require_worktree", return_value=None), \
                 mock.patch.object(cli, "api_request") as mutation, \
                 self.assertRaises(cli.ReviewError) as raised:
                cli.request_automated_review("owner/repo", 12, "codex", head, "run-05", False, None)
            self.assertEqual(raised.exception.code, expected)
            mutation.assert_not_called()

    def test_typed_request_ignores_historical_unbound_and_different_head_requests(self) -> None:
        head = "e" * 40
        old_head = "f" * 40
        historical_plain = {"id": 1, "body": "@codex review"}
        historical_typed = self.canonical_request(old_head, comment_id=2, request_key="old-run")
        plan = build_request("codex", "owner/repo", 12, head, "run-06")
        created = {
            "id": 6,
            "html_url": "https://github.com/owner/repo/pull/12#issuecomment-6",
            "issue_url": "https://api.github.com/repos/owner/repo/issues/12",
            "user": {"login": "agent"},
            "body": plan.body,
            "created_at": "2026-07-20T12:00:00Z",
        }
        self.frozen_clock()
        with mock.patch.object(cli, "_verify_pr_target", return_value={"number": 12, "head": {"sha": head}}), \
             mock.patch.object(cli, "gh_api_paginated_list", return_value=[historical_plain, historical_typed]), \
             mock.patch.object(cli, "require_worktree", return_value=None), \
             mock.patch.object(cli, "_viewer_login", return_value="agent"), \
             mock.patch.object(cli, "api_request", return_value=Result(0, json.dumps(created), "")) as mutation:
            action = cli.request_automated_review("owner/repo", 12, "codex", head, "run-06", False, None)

        self.assertEqual(action["status"], "posted")
        self.assertEqual(action["request"]["comment_id"], 6)
        mutation.assert_called_once()

    def test_invalid_typed_marker_conflicts_only_for_its_full_head(self) -> None:
        head = "e" * 40
        old_head = "f" * 40
        plan = build_request("codex", "owner/repo", 12, head, "run-07")
        invalid_current = {
            **self.canonical_request(head, comment_id=7, request_key="old-current"),
            "body": plan.body.replace("request_fingerprint=", "request_fingerprint=0"),
        }
        invalid_old = {
            **self.canonical_request(old_head, comment_id=8, request_key="old-head"),
            "body": self.canonical_request(old_head, comment_id=8, request_key="old-head")["body"].replace(
                "request_fingerprint=", "request_fingerprint=0"
            ),
        }

        conflict, exact = cli._request_conflicts([invalid_current], plan)
        self.assertEqual(conflict, "invalid")
        self.assertEqual(exact, [])
        conflict, exact = cli._request_conflicts([invalid_old], plan)
        self.assertIsNone(conflict)
        self.assertEqual(exact, [])

    def test_identity_bound_waiter_requires_complete_receipt(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = cli.main(["--json", "wait", "--provider", "codex", "--repo", "owner/repo", "--pr", "12"])
        self.assertEqual(code, 64)
        self.assertEqual(json.loads(stdout.getvalue())["error"]["code"], "request_binding_required")

    def test_wait_returns_binding_failure_without_timeout(self) -> None:
        with mock.patch.object(
            cli,
            "check_automated_review",
            return_value={"request_binding": "unbound", "review_state": None},
        ), mock.patch.object(cli.time, "sleep") as sleep:
            payload, exit_code = cli.wait_for_automated_review(
                "owner/repo", 12, "codex", None, 120, 1, 2, self.canonical_receipt("a" * 40)
            )
        self.assertEqual(exit_code, 4)
        self.assertEqual(payload["request_binding"], "unbound")
        sleep.assert_not_called()

    def test_comment_dry_run_json_shape(self) -> None:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8") as handle:
            handle.write("`ticks` $(command) $HOME 'quotes' \"double\"\nUnicode ✓")
            handle.flush()
            stdout = io.StringIO()
            with mock.patch.object(cli, "_verify_pr_target", return_value={"number": 12}), \
                 mock.patch.object(cli, "require_worktree", return_value=None), \
                 contextlib.redirect_stdout(stdout):
                code = cli.main(
                    [
                        "--json", "comment", "--repo", "owner/repo", "--pr", "12",
                        "--body-file", handle.name, "--head", "b" * 40,
                        "--request-key", "run-warning", "--request-fingerprint", "a" * 64,
                        "--reservation-file", "/tmp/review-warning-reservation.json",
                        "--dry-run",
                    ]
                )
        self.assertEqual(code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["version"], "2.18.20")
        self.assertEqual(payload["command"], ["comment"])
        self.assertEqual(payload["data"]["repo"], "owner/repo")
        self.assertEqual(payload["data"]["pr"], 12)
        self.assertEqual(payload["data"]["action"]["status"], "dry-run")
        rendered = json.dumps(payload, ensure_ascii=False)
        self.assertNotIn("ticks", rendered)
        self.assertNotIn("command", rendered.replace('"command": ["comment"]', ""))

    def test_address_is_read_only(self) -> None:
        entry = {
            "index": 1,
            "type": "review_comment",
            "comment_id": 123456,
            "author": "reviewer",
            "updated": "2026-07-10T00:00:00Z",
            "body": "Please clarify this.",
            "body_preview": "Please clarify this.",
            "path": "src/example.py",
            "line": 12,
            "start_line": 12,
            "is_resolved": False,
            "is_outdated": False,
        }
        stdout = io.StringIO()
        with mock.patch.object(cli, "collect_entries", return_value=[entry]), contextlib.redirect_stdout(stdout):
            code = cli.main(["--json", "address", "--repo", "owner/repo", "--pr", "12"])
        self.assertEqual(code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["version"], "2.18.20")
        self.assertNotIn("actions", payload["data"])

    def test_reply_dry_run_is_one_target_and_file_backed(self) -> None:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8") as handle:
            handle.write("Fixed `x` and $(not-run).")
            handle.flush()
            stdout = io.StringIO()
            head = "b" * 40
            parent = self.finding(comment_id=123456)
            thread = {**self.thread(head=head), "thread_id": "PRRT_thread_123456"}
            with mock.patch.object(cli, "_verify_pr_head"), \
                 mock.patch.object(cli, "_api_object", return_value=parent), \
                 mock.patch.object(cli, "_finding_thread", return_value=thread), \
                 mock.patch.object(cli, "require_worktree", return_value=None), \
                 contextlib.redirect_stdout(stdout):
                code = cli.main([
                    "--json", "reply", "--repo", "owner/repo", "--pr", "12",
                    "--head", head, "--comment-id", "123456", "--body-file", handle.name,
                    "--request-key", "run-reply", "--request-fingerprint", "a" * 64,
                    "--reservation-file", "/tmp/review-reply-reservation.json",
                    "--dry-run",
                ])
        self.assertEqual(code, 0)
        payload = json.loads(stdout.getvalue())
        action = payload["data"]["action"]
        self.assertEqual(action["target"]["finding_comment_id"], 123456)
        self.assertEqual(action["transport"]["endpoint"], "repos/owner/repo/pulls/12/comments/123456/replies")
        self.assertNotIn("not-run", json.dumps(payload))

    def test_inline_provider_text_flags_are_rejected(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        hostile = "`unsafe` $(command) $HOME"
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = cli.main([
                "--json", "comment", "--repo", "owner/repo", "--pr", "12", "--body", hostile,
            ])
        self.assertEqual(code, 64)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["error"]["code"], "invalid_arguments")
        self.assertNotIn(hostile, stdout.getvalue() + stderr.getvalue())

    def test_malformed_comment_response_recovers_from_one_unique_read_back(self) -> None:
        self.frozen_clock()
        body = self.provider_body()
        item = {
            "id": 41, "html_url": "https://github.com/owner/repo/issues/12#issuecomment-41",
            "issue_url": "https://api.github.com/repos/owner/repo/issues/12",
            "user": {"login": "agent"}, "body": body.text,
            "created_at": "2026-07-20T12:00:00Z",
        }
        unprovable_responses = (
            "not-json",
            "[]",
            json.dumps({"body": body.text}),
            json.dumps({**item, "user": "agent"}),
            json.dumps({**item, "issue_url": "https://api.github.com/repos/owner/other/issues/12"}),
            json.dumps({**item, "body": "different"}),
            json.dumps({**item, "body": "\ud800"}),
        )
        for response in unprovable_responses:
            with self.subTest(response=response[:20]), \
                 mock.patch.object(cli, "_verify_pr_target", return_value={"number": 12}), \
                 mock.patch.object(cli, "require_worktree", return_value=None), \
                 mock.patch.object(cli, "_viewer_login", return_value="agent"), \
                 mock.patch.object(cli, "api_request", return_value=Result(0, response, "")) as mutation, \
                 mock.patch.object(cli, "gh_api_paginated_list", return_value=[item]) as read_back:
                action = cli.post_conversation_comment("owner/repo", 12, body, False, None)

            self.assertEqual(action["status"], "recovered")
            self.assertEqual(action["id"], 41)
            mutation.assert_called_once()
            read_back.assert_called_once()

    def test_malformed_comment_response_with_missing_read_back_is_ambiguous_and_redacted(self) -> None:
        self.frozen_clock()
        body = self.provider_body()
        with mock.patch.object(cli, "_verify_pr_target", return_value={"number": 12}), \
             mock.patch.object(cli, "require_worktree", return_value=None), \
             mock.patch.object(cli, "_viewer_login", return_value="agent"), \
             mock.patch.object(cli, "api_request", return_value=Result(0, "not-json", "")), \
             mock.patch.object(cli, "gh_api_paginated_list", return_value=[]) as read_back, \
             self.assertRaises(cli.ReviewError) as raised:
            cli.post_conversation_comment("owner/repo", 12, body, False, None)

        self.assertEqual(raised.exception.code, "provider_write_ambiguous")
        self.assertEqual(raised.exception.details["response"]["code"], "provider_response_invalid")
        self.assertNotIn(body.text, json.dumps(raised.exception.details, ensure_ascii=False))
        read_back.assert_called_once()

    def test_recovered_comment_preserves_identity_when_worktree_post_check_fails(self) -> None:
        self.frozen_clock()
        body = self.provider_body()
        item = {
            "id": 42, "html_url": "https://github.com/owner/repo/issues/12#issuecomment-42",
            "issue_url": "https://api.github.com/repos/owner/repo/issues/12",
            "user": {"login": "agent"}, "body": body.text,
            "created_at": "2026-07-20T12:00:00Z",
        }
        before = {"fingerprint": "a" * 64}
        drift = GError(
            "The provider mutation completed, but the Git worktree fingerprint changed.",
            code="provider_write_partial_success", exit_code=65,
        )
        with mock.patch.object(cli, "_verify_pr_target", return_value={"number": 12}), \
             mock.patch.object(cli, "require_worktree", return_value=before), \
             mock.patch.object(cli, "_viewer_login", return_value="agent"), \
             mock.patch.object(cli, "api_request", return_value=Result(0, "not-json", "")), \
             mock.patch.object(cli, "gh_api_paginated_list", return_value=[item]), \
             mock.patch.object(cli, "verify_worktree_unchanged", side_effect=drift), \
             self.assertRaises(cli.ReviewError) as raised:
            cli.post_conversation_comment("owner/repo", 12, body, False, before["fingerprint"])

        self.assertEqual(raised.exception.code, "provider_write_partial_success")
        self.assertEqual(raised.exception.details["action"]["status"], "recovered")
        self.assertEqual(raised.exception.details["action"]["id"], 42)
        self.assertNotIn(body.text, json.dumps(raised.exception.details, ensure_ascii=False))

    def test_malformed_reply_response_recovers_and_duplicate_read_back_is_ambiguous(self) -> None:
        self.frozen_clock()
        body = self.provider_body()
        parent = self.finding()
        item = self.reply(body)
        head = "b" * 40
        common = [
            mock.patch.object(cli, "_verify_pr_head"),
            mock.patch.object(cli, "_api_object", return_value=parent),
            mock.patch.object(cli, "_finding_thread", return_value=self.thread(head=head)),
            mock.patch.object(cli, "require_worktree", return_value=None),
            mock.patch.object(cli, "_viewer_login", return_value="agent"),
            mock.patch.object(cli, "api_request", return_value=Result(0, "[]", "")),
        ]
        with common[0], common[1], common[2], common[3], common[4], common[5], \
             mock.patch.object(cli, "gh_api_paginated_list", return_value=[item]) as read_back:
            action = cli.reply_to_review_comment("owner/repo", 12, head, 55, body, False, None)
        self.assertEqual(action["status"], "recovered")
        self.assertEqual(action["reply"]["thread_id"], "PRRT_thread_55")
        validate_reply_receipt(action["reply"])
        read_back.assert_called_once()

        with mock.patch.object(cli, "_verify_pr_head"), \
             mock.patch.object(cli, "_api_object", return_value=parent), \
             mock.patch.object(cli, "_finding_thread", return_value=self.thread(head=head)), \
             mock.patch.object(cli, "require_worktree", return_value=None), \
             mock.patch.object(cli, "_viewer_login", return_value="agent"), \
             mock.patch.object(cli, "api_request", return_value=Result(0, "[]", "")), \
             mock.patch.object(cli, "gh_api_paginated_list", return_value=[item, item]) as duplicate, \
             self.assertRaises(cli.ReviewError) as raised:
            cli.reply_to_review_comment("owner/repo", 12, head, 55, body, False, None)
        self.assertEqual(raised.exception.code, "provider_write_ambiguous")
        duplicate.assert_called_once()

    def test_reply_rejects_reply_parent_and_fails_closed_on_post_write_head_drift(self) -> None:
        self.frozen_clock()
        body = self.provider_body()
        head = "b" * 40
        reply_parent = {**self.finding(), "in_reply_to_id": 54}
        with mock.patch.object(cli, "_verify_pr_head"), \
             mock.patch.object(cli, "_api_object", return_value=reply_parent), \
             self.assertRaises(cli.ReviewError) as invalid_parent:
            cli.reply_to_review_comment("owner/repo", 12, head, 55, body, True, None)
        self.assertEqual(invalid_parent.exception.code, "review_reply_parent_invalid")

        drift = cli.ReviewError("head moved", code="head_drift", exit_code=3)
        with mock.patch.object(cli, "_verify_pr_head", side_effect=[None, drift]) as verify_head, \
             mock.patch.object(cli, "_api_object", return_value=self.finding()), \
             mock.patch.object(cli, "_finding_thread", return_value=self.thread(head=head)), \
             mock.patch.object(cli, "require_worktree", return_value=None), \
             mock.patch.object(cli, "_viewer_login", return_value="agent"), \
             mock.patch.object(cli, "api_request", return_value=Result(0, json.dumps(self.reply(body)), "")), \
             self.assertRaises(cli.ReviewError) as head_drift:
            cli.reply_to_review_comment("owner/repo", 12, head, 55, body, False, None)
        self.assertEqual(verify_head.call_count, 2)
        self.assertEqual(head_drift.exception.code, "reply_head_drift")
        self.assertTrue(head_drift.exception.details["mutation_attempted"])
        self.assertTrue(head_drift.exception.details["mutation_may_have_applied"])

    def test_thread_discovery_paginates_threads_and_comments_and_matches_node_id(self) -> None:
        thread_pages = [
            {"data": {"repository": {"pullRequest": {"reviewThreads": {
                "nodes": [{"id": "PRRT_other"}],
                "pageInfo": {"hasNextPage": True, "endCursor": "next"},
            }}}}},
            {"data": {"repository": {"pullRequest": {"reviewThreads": {
                "nodes": [{"id": "PRRT_thread_55"}],
                "pageInfo": {"hasNextPage": False, "endCursor": None},
            }}}}},
        ]
        other = {**self.thread(), "thread_id": "PRRT_other", "comments": []}
        wanted = self.thread()
        with mock.patch.object(cli, "graphql", side_effect=thread_pages) as graphql:
            self.assertEqual(cli._review_thread_ids("owner/repo", 12), ["PRRT_other", "PRRT_thread_55"])
        self.assertEqual(graphql.call_count, 2)
        with mock.patch.object(cli, "_review_thread_ids", return_value=["PRRT_other", "PRRT_thread_55"]), \
             mock.patch.object(cli, "_review_thread_context", side_effect=[other, wanted]):
            selected = cli._finding_thread("owner/repo", 12, 55, "PRRC_finding_55")
        self.assertEqual(selected["thread_id"], "PRRT_thread_55")

    def test_address_exposes_typed_thread_fingerprint_for_prepare(self) -> None:
        wanted = self.thread()
        with mock.patch.object(cli, "_review_thread_ids", return_value=["PRRT_thread_55"]), \
             mock.patch.object(cli, "_review_thread_context", return_value=wanted):
            entries = cli.review_threads("owner/repo", 12, include_resolved=False)
        self.assertEqual(entries[0]["head_sha"], wanted["head_sha"])
        self.assertEqual(
            entries[0]["thread_fingerprint"],
            thread_identity_fingerprint(
                "owner/repo",
                12,
                wanted["head_sha"],
                "PRRT_thread_55",
                [
                    {"node_id": "PRRC_finding_55", "comment_id": 55},
                    {"node_id": "PRRC_reply_56", "comment_id": 56},
                ],
            ),
        )

    def test_resolution_dry_run_and_already_resolved_require_typed_reply(self) -> None:
        body = self.provider_body()
        saved = self.reply_receipt(body)
        with mock.patch.object(cli, "_validate_reply_remote", return_value=(saved, self.thread())), \
             mock.patch.object(cli, "require_worktree", return_value=None):
            action = cli.resolve_review_thread("owner/repo", 12, "b" * 40, saved, True, None)
        self.assertEqual(action["status"], "dry-run")
        self.assertFalse(action["mutation_attempted"])
        self.assertFalse(action["mutation_may_have_applied"])

        with mock.patch.object(cli, "_validate_reply_remote", return_value=(saved, self.thread(resolved=True))), \
             mock.patch.object(cli, "require_worktree", return_value=None):
            action = cli.resolve_review_thread("owner/repo", 12, "b" * 40, saved, False, None)
        self.assertEqual(action["status"], "already-resolved")
        self.assertFalse(action["mutation_attempted"])
        self.assertFalse(action["mutation_may_have_applied"])
        validate_resolution_receipt(action["resolution"])

    def test_resolution_success_and_ambiguous_response_recovery(self) -> None:
        self.frozen_clock()
        body = self.provider_body()
        saved = self.reply_receipt(body)
        resolved = self.thread(resolved=True)
        response = {
            "data": {"resolveReviewThread": {"thread": {
                "id": resolved["thread_id"],
                "isResolved": True,
                "isOutdated": False,
                "viewerCanResolve": True,
                "repository": {"nameWithOwner": "owner/repo"},
                "pullRequest": {"number": 12, "state": "OPEN", "headRefOid": "b" * 40},
            }}}
        }
        with mock.patch.object(cli, "_validate_reply_remote", return_value=(saved, self.thread())), \
             mock.patch.object(cli, "require_worktree", return_value=None), \
             mock.patch.object(cli, "graphql_request", return_value=Result(0, json.dumps(response), "")), \
             mock.patch.object(cli, "_review_thread_context", return_value=resolved) as exact_read_back:
            action = cli.resolve_review_thread("owner/repo", 12, "b" * 40, saved, False, None)
        self.assertEqual(action["status"], "resolved")
        self.assertTrue(action["mutation_attempted"])
        self.assertFalse(action["mutation_may_have_applied"])
        exact_read_back.assert_called_once_with("PRRT_thread_55")
        validate_resolution_receipt(action["resolution"])

        for mutation_result in (
            Result(1, "", "transport failed"),
            Result(0, "not-json", ""),
        ):
            with self.subTest(mutation_result=mutation_result), \
                 mock.patch.object(cli, "_validate_reply_remote", return_value=(saved, self.thread())), \
                 mock.patch.object(cli, "require_worktree", return_value=None), \
                 mock.patch.object(cli, "graphql_request", return_value=mutation_result), \
                 mock.patch.object(cli, "_review_thread_context", return_value=resolved) as read_back:
                action = cli.resolve_review_thread("owner/repo", 12, "b" * 40, saved, False, None)
            self.assertEqual(action["status"], "recovered")
            self.assertTrue(action["mutation_attempted"])
            self.assertFalse(action["mutation_may_have_applied"])
            read_back.assert_called_once_with("PRRT_thread_55")

    def test_resolution_response_mismatch_never_recovers_from_readback(self) -> None:
        body = self.provider_body()
        saved = self.reply_receipt(body)
        resolved = self.thread(resolved=True)
        for thread_id, response_head, code in (
            ("PRRT_other", "b" * 40, "review_thread_mismatch"),
            ("PRRT_thread_55", "c" * 40, "resolution_head_drift"),
        ):
            mismatched_response = {
                "data": {"resolveReviewThread": {"thread": {
                    "id": thread_id,
                    "isResolved": True,
                    "isOutdated": False,
                    "viewerCanResolve": True,
                    "repository": {"nameWithOwner": "owner/repo"},
                    "pullRequest": {"number": 12, "state": "OPEN", "headRefOid": response_head},
                }}}
            }
            with self.subTest(code=code), \
                 mock.patch.object(cli, "_validate_reply_remote", return_value=(saved, self.thread())), \
                 mock.patch.object(cli, "require_worktree", return_value=None), \
                 mock.patch.object(cli, "graphql_request", return_value=Result(0, json.dumps(mismatched_response), "")), \
                 mock.patch.object(cli, "_review_thread_context", return_value=resolved) as read_back, \
                 self.assertRaises(cli.ReviewError) as raised:
                cli.resolve_review_thread("owner/repo", 12, "b" * 40, saved, False, None)
            self.assertEqual(raised.exception.code, code)
            self.assertTrue(raised.exception.details["mutation_attempted"])
            self.assertTrue(raised.exception.details["mutation_may_have_applied"])
            read_back.assert_called_once_with("PRRT_thread_55")

    def test_resolution_readback_transport_failure_is_uncertain_after_attempt(self) -> None:
        body = self.provider_body()
        saved = self.reply_receipt(body)
        with mock.patch.object(cli, "_validate_reply_remote", return_value=(saved, self.thread())), \
             mock.patch.object(cli, "require_worktree", return_value=None), \
             mock.patch.object(cli, "graphql_request", return_value=Result(1, "", "transport failed")), \
             mock.patch.object(cli, "_review_thread_context", side_effect=cli.ReviewError("transport", code="command_failed")), \
             self.assertRaises(cli.ReviewError) as raised:
            cli.resolve_review_thread("owner/repo", 12, "b" * 40, saved, False, None)
        self.assertEqual(raised.exception.code, "resolution_unknown")
        self.assertTrue(raised.exception.details["mutation_attempted"])
        self.assertTrue(raised.exception.details["mutation_may_have_applied"])
        self.assertEqual(raised.exception.details["read_back"]["code"], "command_failed")

    def test_resolution_uncertainty_and_head_drift_fail_closed(self) -> None:
        body = self.provider_body()
        saved = self.reply_receipt(body)
        for read_back, code in (
            (self.thread(resolved=False), "resolution_unknown"),
            (self.thread(resolved=True, head="c" * 40), "resolution_head_drift"),
        ):
            with self.subTest(code=code), \
                 mock.patch.object(cli, "_validate_reply_remote", return_value=(saved, self.thread())), \
                 mock.patch.object(cli, "require_worktree", return_value=None), \
                 mock.patch.object(cli, "graphql_request", return_value=Result(1, "", "failed")), \
                 mock.patch.object(cli, "_review_thread_context", return_value=read_back), \
                 self.assertRaises(cli.ReviewError) as raised:
                cli.resolve_review_thread("owner/repo", 12, "b" * 40, saved, False, None)
            self.assertEqual(raised.exception.code, code)
            self.assertTrue(raised.exception.details["mutation_may_have_applied"])

    def test_resolution_rejects_wrong_pr_wrong_thread_and_missing_reply(self) -> None:
        body = self.provider_body()
        saved = self.reply_receipt(body)
        with self.assertRaises(cli.ReviewError) as wrong_pr:
            cli.resolve_review_thread("owner/repo", 99, "b" * 40, saved, True, None)
        self.assertEqual(wrong_pr.exception.code, "review_thread_mismatch")

        with self.assertRaises(cli.ReviewError) as missing:
            cli.resolve_review_thread("owner/repo", 12, "b" * 40, None, True, None)
        self.assertEqual(missing.exception.code, "reply_receipt_invalid")

        thread = self.thread()
        thread["comments"] = [thread["comments"][0]]
        with mock.patch.object(cli, "_verify_pr_head"), \
             mock.patch.object(cli, "_api_object", side_effect=[self.finding(), self.reply(body=body)]), \
             mock.patch.object(cli, "_review_thread_context", return_value=thread), \
             self.assertRaises(cli.ReviewError) as wrong_thread:
            cli.resolve_review_thread("owner/repo", 12, "b" * 40, saved, True, None)
        self.assertEqual(wrong_thread.exception.code, "evidence_reply_not_found")

    def test_reply_receipt_rejects_identity_changes(self) -> None:
        saved = self.reply_receipt(self.provider_body())
        for field, value in (
            ("finding_node_id", "PRRC_other"),
            ("reply_node_id", "PRRC_other"),
            ("reply_author", "other"),
            ("body_fingerprint", "0" * 64),
        ):
            changed = {**saved, field: value}
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_reply_receipt(changed)

    def test_malformed_edit_response_recovers_and_mismatched_read_back_is_ambiguous(self) -> None:
        body = self.provider_body()
        current = {
            "id": 61, "html_url": "https://github.com/owner/repo/issues/12#issuecomment-61",
            "issue_url": "https://api.github.com/repos/owner/repo/issues/12",
            "user": {"login": "agent"}, "body": "old",
        }
        updated = {**current, "body": body.text}
        with mock.patch.object(cli, "_api_object", side_effect=[current, updated]) as read_object, \
             mock.patch.object(cli, "require_worktree", return_value=None), \
             mock.patch.object(cli, "_viewer_login", return_value="agent"), \
             mock.patch.object(cli, "api_request", return_value=Result(0, "not-json", "")):
            action = cli.edit_comment("owner/repo", 12, 61, "conversation", body, False, None)
        self.assertEqual(action["status"], "recovered")
        self.assertEqual(read_object.call_count, 2)

        mismatched = {**updated, "id": 62}
        with mock.patch.object(cli, "_api_object", side_effect=[current, mismatched]) as read_object, \
             mock.patch.object(cli, "require_worktree", return_value=None), \
             mock.patch.object(cli, "_viewer_login", return_value="agent"), \
             mock.patch.object(cli, "api_request", return_value=Result(0, "not-json", "")), \
             self.assertRaises(cli.ReviewError) as raised:
            cli.edit_comment("owner/repo", 12, 61, "conversation", body, False, None)
        self.assertEqual(raised.exception.code, "provider_write_ambiguous")
        self.assertNotIn(body.text, json.dumps(raised.exception.details, ensure_ascii=False))
        self.assertEqual(read_object.call_count, 2)

    def test_malformed_review_response_recovers_and_duplicate_read_back_is_ambiguous(self) -> None:
        self.frozen_clock()
        body = self.provider_body()
        head = "a" * 40
        review = {
            "id": 71, "html_url": "https://github.com/owner/repo/pull/12#pullrequestreview-71",
            "pull_request_url": "https://api.github.com/repos/owner/repo/pulls/12",
            "user": {"login": "agent"}, "state": "APPROVED", "body": body.text,
            "commit_id": head, "submitted_at": "2026-07-20T12:00:00Z",
        }
        with mock.patch.object(cli, "_verify_pr_target", return_value={"number": 12, "head": {"sha": head}}), \
             mock.patch.object(cli, "require_worktree", return_value=None), \
             mock.patch.object(cli, "_viewer_login", return_value="agent"), \
             mock.patch.object(cli, "api_request", return_value=Result(0, "not-json", "")), \
             mock.patch.object(cli, "gh_api_paginated_list", return_value=[review]) as read_back:
            action = cli.submit_review("owner/repo", 12, "approve", body, False, None)
        self.assertEqual(action["status"], "recovered")
        read_back.assert_called_once()

        with mock.patch.object(cli, "_verify_pr_target", return_value={"number": 12, "head": {"sha": head}}), \
             mock.patch.object(cli, "require_worktree", return_value=None), \
             mock.patch.object(cli, "_viewer_login", return_value="agent"), \
             mock.patch.object(cli, "api_request", return_value=Result(0, "not-json", "")), \
             mock.patch.object(cli, "gh_api_paginated_list", return_value=[review, review]) as duplicate, \
             self.assertRaises(cli.ReviewError) as raised:
            cli.submit_review("owner/repo", 12, "approve", body, False, None)
        self.assertEqual(raised.exception.code, "provider_write_ambiguous")
        duplicate.assert_called_once()

    def test_check_codex_reports_findings_for_expected_head(self) -> None:
        head = "a" * 40
        request = self.canonical_request(head, created_at="2026-07-11T12:01:00Z")
        review = {"id": 7, "user": {"login": "chatgpt-codex-connector[bot]"}, "commit_id": head, "submitted_at": "2026-07-11T12:02:00Z"}
        finding = {"id": 8, "user": {"login": "chatgpt-codex-connector[bot]"}, "commit_id": head, "created_at": "2026-07-11T12:03:00Z"}
        with mock.patch.object(cli, "gh_json", return_value={"head": {"sha": head}}), mock.patch.object(
            cli,
            "gh_api_paginated_list",
            side_effect=self.automated_review_api(reviews=[review], inline=[finding], comments=[request]),
        ):
            payload = cli.check_automated_review("owner/repo", 12, "codex", head)

        self.assertEqual(payload["review_state"], "findings")
        self.assertEqual(payload["request_binding"], "recognized")
        self.assertEqual(payload["review"]["findings"], 1)
        self.assertEqual(payload["review"]["finding_comment_ids"], [8])

    def test_ready_review_ignores_pre_ready_clean_and_reports_post_ready_finding(self) -> None:
        head = "a" * 40
        pre_ready_clean = {
            "id": 100,
            "user": {"login": "chatgpt-codex-connector[bot]"},
            "body": f"Codex Review: Didn't find any major issues.\n\n**Reviewed commit:** `{head[:10]}`",
            "created_at": "2026-07-20T12:01:00Z",
        }
        post_ready_finding = {
            "id": 101,
            "user": {"login": "chatgpt-codex-connector[bot]"},
            "body": f"Codex Review: findings.\n\n[P2] address this finding.\n\n**Reviewed commit:** `{head[:10]}`",
            "created_at": "2026-07-20T12:06:00Z",
        }
        pull = {"head": {"sha": head}, "draft": False, "base": {"ref": "main"}, "body": "body"}
        with mock.patch.object(cli, "gh_json", return_value=pull), mock.patch.object(
            cli,
            "gh_api_paginated_list",
            side_effect=self.automated_review_api(comments=[pre_ready_clean, post_ready_finding]),
        ):
            payload = cli.check_ready_automated_review("owner/repo", 12, "codex", head, self.ready_trigger(head))

        self.assertEqual(payload["review_state"], "findings")
        self.assertEqual(payload["terminal_comment"]["count"], 1)
        self.assertEqual(payload["certificate"]["review_state"], "findings")

    def test_ready_review_requires_ready_pr_and_current_body(self) -> None:
        head = "b" * 40
        pull = {"head": {"sha": head}, "draft": True, "base": {"ref": "main"}, "body": "body"}
        with mock.patch.object(cli, "gh_json", return_value=pull), mock.patch.object(
            cli,
            "gh_api_paginated_list",
            side_effect=self.automated_review_api(),
        ):
            payload = cli.check_ready_automated_review("owner/repo", 12, "codex", head, self.ready_trigger(head))

        self.assertEqual(payload["review_state"], "stale")
        self.assertEqual(payload["error_code"], "head_drift")

    def test_ready_review_accepts_post_ready_provider_thumb_up_on_pr(self) -> None:
        head = "b" * 40
        pull = {
            "head": {"sha": head}, "draft": False, "base": {"ref": "main"},
            "body": "body", "html_url": "https://github.com/owner/repo/pull/12",
        }
        reactions = [
            {
                "id": 90, "content": "+1", "created_at": "2026-07-20T12:04:00Z",
                "user": {"login": "chatgpt-codex-connector[bot]"},
            },
            {
                "id": 91, "content": "+1", "created_at": "2026-07-20T12:06:00Z",
                "user": {"login": "someone-else"},
            },
            {
                "id": 92, "content": "+1", "created_at": "2026-07-20T12:07:00Z",
                "user": {"login": "chatgpt-codex-connector[bot]"},
            },
        ]
        with mock.patch.object(cli, "gh_json", return_value=pull), mock.patch.object(
            cli,
            "gh_api_paginated_list",
            side_effect=self.automated_review_api(issue_reactions=reactions),
        ):
            payload = cli.check_ready_automated_review(
                "owner/repo", 12, "codex", head, self.ready_trigger(head)
            )

        self.assertEqual(payload["review_state"], "clean")
        self.assertEqual(payload["evidence"]["kind"], "clean-reaction")
        self.assertEqual(payload["evidence"]["object_id"], 92)
        self.assertEqual(payload["evidence"]["head"], head)
        self.assertEqual(payload["clean_reaction"], {"count": 1, "latest_id": 92})
        self.assertEqual(payload["certificate"]["review_state"], "clean")

    def test_ready_trigger_rejects_tampered_fingerprint(self) -> None:
        trigger = self.ready_trigger("c" * 40)
        trigger["ready_event_id"] = "tampered"
        with self.assertRaises(cli.ReviewError):
            cli.check_ready_automated_review("owner/repo", 12, "codex", "c" * 40, trigger)

    def test_check_codex_counts_only_top_level_inline_findings(self) -> None:
        head = "a" * 40
        request = self.canonical_request(head, created_at="2026-07-11T12:01:00Z")
        review = {"id": 7, "user": {"login": "chatgpt-codex-connector[bot]"}, "commit_id": head, "submitted_at": "2026-07-11T12:02:00Z"}
        finding = {"id": 8, "user": {"login": "chatgpt-codex-connector[bot]"}, "commit_id": head, "created_at": "2026-07-11T12:03:00Z"}
        provider_reply = {"id": 9, "in_reply_to_id": 8, "user": {"login": "chatgpt-codex-connector[bot]"}, "commit_id": head, "created_at": "2026-07-11T12:04:00Z"}
        with mock.patch.object(cli, "gh_json", return_value={"head": {"sha": head}}), mock.patch.object(
            cli,
            "gh_api_paginated_list",
            side_effect=self.automated_review_api(reviews=[review], inline=[finding, provider_reply], comments=[request]),
        ):
            payload = cli.check_automated_review("owner/repo", 12, "codex", head)

        self.assertEqual(payload["review_state"], "findings")
        self.assertEqual(payload["review"]["findings"], 1)
        self.assertEqual(payload["review"]["finding_comment_ids"], [8])

    def test_identity_bound_check_fetches_receipt_comment_id(self) -> None:
        head = "a" * 40
        request = self.canonical_request(head, created_at="2026-07-11T12:01:00Z")
        saved = self.canonical_receipt(head, created_at="2026-07-11T12:01:00Z")
        with mock.patch.object(cli, "gh_json", return_value={"head": {"sha": head}}), mock.patch.object(
            cli,
            "gh_api_paginated_list",
            side_effect=self.automated_review_api(comments=[request]),
        ), mock.patch.object(cli, "_api_object", return_value=request) as exact_comment:
            payload = cli.check_automated_review("owner/repo", 12, "codex", head, saved)

        self.assertEqual(payload["request_binding"], "recognized")
        self.assertEqual(payload["request"]["comment_id"], request["id"])
        self.assertEqual(payload["request"], saved)
        self.assertEqual(payload["request"]["status"], "posted")
        exact_comment.assert_called_once_with("repos/owner/repo/issues/comments/99")

    def test_identity_bound_check_ignores_historical_unbound_and_different_head_requests(self) -> None:
        head = "a" * 40
        old_head = "b" * 40
        exact = self.canonical_request(head, comment_id=99, created_at="2026-07-11T12:01:00Z")
        saved = self.canonical_receipt(head, comment_id=99, created_at="2026-07-11T12:01:00Z")
        historical_plain = {"id": 97, "body": "@codex review", "created_at": "2026-07-01T12:00:00Z"}
        historical_typed = self.canonical_request(old_head, comment_id=98, request_key="old-run")
        with mock.patch.object(cli, "gh_json", return_value={"head": {"sha": head}}), mock.patch.object(
            cli,
            "gh_api_paginated_list",
            side_effect=self.automated_review_api(comments=[historical_plain, historical_typed, exact]),
        ), mock.patch.object(cli, "_api_object", return_value=exact):
            payload = cli.check_automated_review("owner/repo", 12, "codex", head, saved)

        self.assertEqual(payload["request_binding"], "recognized")
        self.assertEqual(payload["review_state"], "pending")
        self.assertEqual(payload["request"], saved)
        self.assertNotIn("status", payload["request_observation"])

    def test_check_codex_reports_acknowledged_request(self) -> None:
        head = "b" * 40
        request = self.canonical_request(head, created_at="2026-07-11T12:01:00Z")
        eyes = [{"content": "eyes", "user": {"login": "chatgpt-codex-connector[bot]"}}]
        with mock.patch.object(cli, "gh_json", return_value={"head": {"sha": head}}), mock.patch.object(
            cli,
            "gh_api_paginated_list",
            side_effect=self.automated_review_api(comments=[request], reactions=eyes),
        ):
            payload = cli.check_automated_review("owner/repo", 12, "codex", head)

        self.assertEqual(payload["review_state"], "acknowledged")
        self.assertTrue(payload["request_observation"]["acknowledged"])
        self.assertEqual(payload["request"]["kind"], "observed-request")
        self.assertNotIn("status", payload["request"])
        self.assertNotIn("identity_fingerprint", payload["request"])

    def test_check_codex_detects_terminal_clean_conversation_comment(self) -> None:
        head = "f5dc037d8d3978df85a6e59f68ebad38e75953b0"
        request = self.canonical_request(head)
        result = {
            "id": 100,
            "user": {"login": "chatgpt-codex-connector[bot]"},
            "body": (
                "Codex Review: Didn't find any major issues. Keep it up!\n\n"
                "**Reviewed commit:** `f5dc037d8d`"
            ),
            "created_at": "2026-07-15T13:12:20Z",
        }
        with mock.patch.object(cli, "gh_json", return_value={"head": {"sha": head}}), mock.patch.object(
            cli,
            "gh_api_paginated_list",
            side_effect=self.automated_review_api(comments=[request, result]),
        ):
            payload = cli.check_automated_review("owner/repo", 12, "codex", head)

        self.assertEqual(payload["review_state"], "clean")
        self.assertEqual(payload["evidence"]["kind"], "provider-comment")
        self.assertEqual(payload["evidence"]["object_id"], 100)
        self.assertEqual(payload["terminal_comment"]["reviewed_head"], "f5dc037d8d")
        self.assertRegex(payload["observation_fingerprint"], r"^[0-9a-f]{64}$")

    def test_check_codex_detects_terminal_findings_conversation_comment(self) -> None:
        head = "a" * 40
        request = self.canonical_request(head)
        result = {
            "id": 100,
            "user": {"login": "chatgpt-codex-connector[bot]"},
            "body": f"Codex Review: Found issues to address.\n\n**Reviewed commit:** `{head[:10]}`",
            "created_at": "2026-07-15T13:01:00Z",
        }
        with mock.patch.object(cli, "gh_json", return_value={"head": {"sha": head}}), mock.patch.object(
            cli,
            "gh_api_paginated_list",
            side_effect=self.automated_review_api(comments=[request, result]),
        ):
            payload = cli.check_automated_review("owner/repo", 12, "codex", head)

        self.assertEqual(payload["review_state"], "findings")
        self.assertEqual(payload["evidence"]["kind"], "provider-comment")
        self.assertEqual(payload["review"]["findings"], 0)
        self.assertEqual(payload["review"]["finding_comment_ids"], [])

    def test_check_codex_detects_terminal_error_conversation_comment(self) -> None:
        head = "a" * 40
        request = self.canonical_request(head)
        result = {
            "id": 100,
            "user": {"login": "chatgpt-codex-connector[bot]"},
            "body": f"Codex Review: Review failed because the service encountered an error.\n\n**Reviewed commit:** `{head[:10]}`",
            "created_at": "2026-07-15T13:01:00Z",
        }
        with mock.patch.object(cli, "gh_json", return_value={"head": {"sha": head}}), mock.patch.object(
            cli,
            "gh_api_paginated_list",
            side_effect=self.automated_review_api(comments=[request, result]),
        ):
            payload = cli.check_automated_review("owner/repo", 12, "codex", head)

        self.assertEqual(payload["review_state"], "error")
        self.assertEqual(payload["evidence"]["kind"], "provider-comment")

    def test_check_codex_ignores_authenticated_nonterminal_status_comment(self) -> None:
        head = "a" * 40
        request = self.canonical_request(head)
        status = {
            "id": 100,
            "user": {"login": "chatgpt-codex-connector[bot]"},
            "body": f"Codex Review: Review is still in progress.\n\n**Reviewed commit:** `{head[:10]}`",
            "created_at": "2026-07-15T13:01:00Z",
        }
        with mock.patch.object(cli, "gh_json", return_value={"head": {"sha": head}}), mock.patch.object(
            cli,
            "gh_api_paginated_list",
            side_effect=self.automated_review_api(comments=[request, status]),
        ):
            payload = cli.check_automated_review("owner/repo", 12, "codex", head)

        self.assertEqual(payload["review_state"], "pending")
        self.assertEqual(payload["terminal_comment"]["count"], 0)

    def test_check_codex_rejects_terminal_result_after_overlapping_same_head_requests(self) -> None:
        head = "a" * 40
        first_request = self.canonical_request(head, comment_id=98)
        second_request = self.canonical_request(head, created_at="2026-07-15T13:01:00Z")
        result = {
            "id": 100,
            "user": {"login": "chatgpt-codex-connector[bot]"},
            "body": f"Codex Review: No findings.\n\n**Reviewed commit:** `{head[:10]}`",
            "created_at": "2026-07-15T13:02:00Z",
        }
        with mock.patch.object(cli, "gh_json", return_value={"head": {"sha": head}}), mock.patch.object(
            cli,
            "gh_api_paginated_list",
            side_effect=self.automated_review_api(
                comments=[first_request, second_request, result]
            ),
        ):
            payload = cli.check_automated_review("owner/repo", 12, "codex", head)

        self.assertEqual(payload["request_binding"], "ambiguous")
        self.assertIsNone(payload["review_state"])

    def test_check_codex_allows_sequential_completed_same_head_requests(self) -> None:
        head = "a" * 40
        first_request = self.canonical_request(head, comment_id=97)
        first_result = {
            "id": 98,
            "user": {"login": "chatgpt-codex-connector[bot]"},
            "body": f"Codex Review: No findings.\n\n**Reviewed commit:** `{head[:10]}`",
            "created_at": "2026-07-15T13:00:30Z",
        }
        second_request = self.canonical_request(head, created_at="2026-07-15T13:01:00Z", request_key="request-99")
        second_result = {
            "id": 100,
            "user": {"login": "chatgpt-codex-connector[bot]"},
            "body": f"Codex Review: No findings.\n\n**Reviewed commit:** `{head[:10]}`",
            "created_at": "2026-07-15T13:02:00Z",
        }
        with mock.patch.object(cli, "gh_json", return_value={"head": {"sha": head}}), mock.patch.object(
            cli,
            "gh_api_paginated_list",
            side_effect=self.automated_review_api(
                comments=[
                    first_request,
                    first_result,
                    second_request,
                    second_result,
                ]
            ),
        ):
            payload = cli.check_automated_review("owner/repo", 12, "codex", head)

        self.assertEqual(payload["request_binding"], "ambiguous")
        self.assertIsNone(payload["review_state"])

    def test_check_codex_keeps_new_request_pending_after_older_formal_review(self) -> None:
        head = "a" * 40
        old_review = {
            "id": 97,
            "user": {"login": "chatgpt-codex-connector[bot]"},
            "commit_id": head,
            "submitted_at": "2026-07-15T13:00:30Z",
        }
        new_request = self.canonical_request(head, created_at="2026-07-15T13:01:00Z")
        with mock.patch.object(cli, "gh_json", return_value={"head": {"sha": head}}), mock.patch.object(
            cli,
            "gh_api_paginated_list",
            side_effect=self.automated_review_api(
                reviews=[old_review],
                comments=[new_request],
            ),
        ):
            payload = cli.check_automated_review("owner/repo", 12, "codex", head)

        self.assertEqual(payload["review_state"], "pending")
        self.assertEqual(payload["review"]["count"], 0)
        self.assertEqual(payload["review"]["latest_id"], None)

    def test_check_codex_ignores_terminal_comment_before_latest_request(self) -> None:
        head = "a" * 40
        result = {
            "id": 98,
            "user": {"login": "chatgpt-codex-connector[bot]"},
            "body": f"Codex Review: No findings.\n\n**Reviewed commit:** `{head[:10]}`",
            "created_at": "2026-07-15T12:59:00Z",
        }
        request = self.canonical_request(head)
        with mock.patch.object(cli, "gh_json", return_value={"head": {"sha": head}}), mock.patch.object(
            cli,
            "gh_api_paginated_list",
            side_effect=self.automated_review_api(comments=[result, request]),
        ):
            payload = cli.check_automated_review("owner/repo", 12, "codex", head)

        self.assertEqual(payload["review_state"], "pending")
        self.assertEqual(payload["terminal_comment"]["count"], 0)

    def test_check_codex_ignores_spoofed_terminal_comment(self) -> None:
        head = "a" * 40
        request = self.canonical_request(head)
        spoof = {
            "id": 100,
            "user": {"login": "human-reviewer"},
            "body": f"Codex Review: No findings.\n\n**Reviewed commit:** `{head[:10]}`",
            "created_at": "2026-07-15T13:01:00Z",
        }
        with mock.patch.object(cli, "gh_json", return_value={"head": {"sha": head}}), mock.patch.object(
            cli,
            "gh_api_paginated_list",
            side_effect=self.automated_review_api(comments=[request, spoof]),
        ):
            payload = cli.check_automated_review("owner/repo", 12, "codex", head)

        self.assertEqual(payload["review_state"], "pending")

    def test_check_codex_rejects_conflicting_terminal_evidence(self) -> None:
        head = "a" * 40
        request = self.canonical_request(head)
        review = {
            "id": 7,
            "user": {"login": "chatgpt-codex-connector[bot]"},
            "commit_id": head,
            "submitted_at": "2026-07-15T13:01:00Z",
        }
        result = {
            "id": 100,
            "user": {"login": "chatgpt-codex-connector[bot]"},
            "body": f"Codex Review: Found issues to address.\n\n**Reviewed commit:** `{head[:10]}`",
            "created_at": "2026-07-15T13:02:00Z",
        }
        with mock.patch.object(cli, "gh_json", return_value={"head": {"sha": head}}), mock.patch.object(
            cli,
            "gh_api_paginated_list",
            side_effect=self.automated_review_api(reviews=[review], comments=[request, result]),
        ):
            with self.assertRaises(cli.ReviewError) as raised:
                cli.check_automated_review("owner/repo", 12, "codex", head)

        self.assertEqual(raised.exception.code, "ambiguous_review_evidence")

    def test_check_codex_emits_canonical_not_requested_state(self) -> None:
        head = "c" * 40
        with mock.patch.object(cli, "gh_json", return_value={"head": {"sha": head}}), mock.patch.object(
            cli,
            "gh_api_paginated_list",
            side_effect=self.automated_review_api(),
        ):
            payload = cli.check_automated_review("owner/repo", 12, "codex", head)

        self.assertEqual(payload["review_state"], "not-requested")
        self.assertNotIn("not_requested", json.dumps(payload))

    def test_check_codex_rejects_stale_review(self) -> None:
        head = "c" * 40
        old_head = "d" * 40
        old_review = {"id": 7, "user": {"login": "chatgpt-codex-connector[bot]"}, "commit_id": old_head}
        with mock.patch.object(cli, "gh_json", return_value={"head": {"sha": head}}), mock.patch.object(
            cli,
            "gh_api_paginated_list",
            side_effect=self.automated_review_api(reviews=[old_review]),
        ):
            payload = cli.check_automated_review("owner/repo", 12, "codex", head)

        self.assertEqual(payload["review_state"], "not-requested")
        self.assertEqual(payload["request_binding"], "absent")

    def test_check_never_marks_a_non_current_head_clean(self) -> None:
        current_head = "e" * 40
        expected_head = "f" * 40
        old_review = {"id": 7, "user": {"login": "chatgpt-codex-connector[bot]"}, "commit_id": expected_head}
        with mock.patch.object(cli, "gh_json", return_value={"head": {"sha": current_head}}), mock.patch.object(
            cli,
            "gh_api_paginated_list",
            side_effect=self.automated_review_api(reviews=[old_review]),
        ):
            payload = cli.check_automated_review("owner/repo", 12, "codex", expected_head)

        self.assertEqual(payload["review_state"], "stale")
        self.assertFalse(payload["head_is_current"])

    def test_check_head_drift_wins_over_invalid_saved_binding(self) -> None:
        requested_head = "f" * 40
        current_head = "e" * 40
        saved = self.canonical_receipt(requested_head)
        edited = {**self.canonical_request(requested_head), "body": "@codex review"}
        with mock.patch.object(cli, "gh_json", return_value={"head": {"sha": current_head}}), mock.patch.object(
            cli,
            "gh_api_paginated_list",
            side_effect=self.automated_review_api(),
        ), mock.patch.object(cli, "_api_object", return_value=edited):
            payload = cli.check_automated_review("owner/repo", 12, "codex", requested_head, saved)

        self.assertEqual(payload["request_binding"], "invalid")
        self.assertEqual(payload["review_state"], "stale")
        self.assertFalse(payload["head_is_current"])

        with mock.patch.object(cli, "resolve_repo", return_value="owner/repo"), mock.patch.object(
            cli, "check_automated_review", return_value=payload
        ), contextlib.redirect_stdout(io.StringIO()):
            code = cli.main([
                "--json", "check", "--provider", "codex", "--repo", "owner/repo",
                "--pr", "12", "--head", requested_head,
            ])
        self.assertEqual(code, 3)

    def test_check_rejects_ambiguous_head_prefix(self) -> None:
        with mock.patch.object(cli, "gh_json", return_value={"head": {"sha": "a" * 40}}):
            with self.assertRaises(cli.ReviewError) as raised:
                cli.check_automated_review("owner/repo", 12, "codex", "a")

        self.assertEqual(raised.exception.code, "invalid_arguments")

    def test_plain_review_request_is_not_bound_to_a_head(self) -> None:
        head = "b" * 40
        request = {"id": 99, "body": "@codex review", "created_at": "2026-07-11T12:01:00Z"}
        with mock.patch.object(cli, "gh_json", return_value={"head": {"sha": head}}), mock.patch.object(
            cli,
            "gh_api_paginated_list",
            side_effect=self.automated_review_api(comments=[request]),
        ):
            payload = cli.check_automated_review("owner/repo", 12, "codex", head)

        self.assertIsNone(payload["review_state"])
        self.assertEqual(payload["request_binding"], "unbound")
        self.assertEqual(payload["failure_kind"], "request-correlation-failure")
        self.assertEqual(payload["error_code"], "request_unbound")

    def test_saved_request_failure_classification_is_machine_stable(self) -> None:
        head = "b" * 40
        saved = self.canonical_receipt(head)
        edited = {**self.canonical_request(head), "body": "@codex review"}
        with mock.patch.object(cli, "gh_json", return_value={"head": {"sha": head}}), \
             mock.patch.object(
                 cli,
                 "gh_api_paginated_list",
                 side_effect=self.automated_review_api(),
             ), \
             mock.patch.object(cli, "_api_object", return_value=edited):
            payload = cli.check_automated_review("owner/repo", 12, "codex", head, saved)
        self.assertEqual(payload["request_binding"], "invalid")
        self.assertEqual(payload["failure_kind"], "request-correlation-failure")
        self.assertEqual(payload["error_code"], "request_correlation_failure")

        with mock.patch.object(cli, "gh_json", return_value={"head": {"sha": head}}), \
             mock.patch.object(
                 cli,
                 "gh_api_paginated_list",
                 side_effect=self.automated_review_api(),
             ), \
             mock.patch.object(
                 cli,
                 "_api_object",
                 side_effect=cli.ReviewError("api unavailable", code="api_error", exit_code=4),
             ):
            payload = cli.check_automated_review("owner/repo", 12, "codex", head, saved)
        self.assertEqual(payload["request_binding"], "unknown")
        self.assertEqual(payload["failure_kind"], "provider-api-failure")
        self.assertEqual(payload["error_code"], "api_error")

    def test_review_request_rejects_different_sha_with_same_prefix(self) -> None:
        head = "abcdef0" + "1" * 33
        other_head = "abcdef0" + "2" * 33
        request = {"body": f"@codex review {other_head}"}

        self.assertEqual(parse_request(request["body"], "codex", "owner/repo", 12).classification, "unbound")

    def test_review_request_accepts_bounded_sha_prefix_after_command(self) -> None:
        head = "abcdef0" + "1" * 33
        request = {"body": "@codex review\nPlease check updated head abcdef01."}

        self.assertEqual(parse_request(request["body"], "codex", "owner/repo", 12).classification, "unbound")

    def test_wait_times_out_pending_review(self) -> None:
        pending = {"request_binding": "recognized", "review_state": "pending", "repo": "owner/repo", "pr": 12}
        with mock.patch.object(cli, "check_automated_review", return_value=pending), mock.patch.object(
            cli.time, "monotonic", side_effect=[0.0, 0.0, 2.0]
        ), mock.patch.object(cli.time, "sleep"):
            payload, exit_code = cli.wait_for_automated_review("owner/repo", 12, "codex", None, 1, 1, 1, self.canonical_receipt("a" * 40))

        self.assertEqual(exit_code, 124)
        self.assertTrue(payload["timed_out"])

    def test_wait_counts_only_changed_observations_as_transitions(self) -> None:
        pending = {
            "request_binding": "recognized",
            "review_state": "pending",
            "repo": "owner/repo",
            "pr": 12,
            "observation_fingerprint": "a" * 64,
        }
        clean = {
            "request_binding": "recognized",
            "review_state": "clean",
            "repo": "owner/repo",
            "pr": 12,
            "observation_fingerprint": "b" * 64,
        }
        with mock.patch.object(
            cli,
            "check_automated_review",
            side_effect=[pending, pending, clean],
        ), mock.patch.object(
            cli.time,
            "monotonic",
            side_effect=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ), mock.patch.object(cli.time, "sleep") as sleep:
            payload, exit_code = cli.wait_for_automated_review(
                "owner/repo", 12, "codex", None, 10, 1, 2, self.canonical_receipt("a" * 40)
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["attempts"], 3)
        self.assertEqual(payload["state_transitions"], 2)
        self.assertEqual(payload["unchanged_attempts"], 1)
        self.assertEqual(sleep.call_count, 2)

    def test_wait_stops_immediately_on_terminal_provider_error(self) -> None:
        error = {
            "request_binding": "recognized",
            "review_state": "error",
            "repo": "owner/repo",
            "pr": 12,
            "observation_fingerprint": "a" * 64,
        }
        with mock.patch.object(
            cli,
            "check_automated_review",
            return_value=error,
        ), mock.patch.object(
            cli.time,
            "monotonic",
            side_effect=[0.0, 0.0],
        ), mock.patch.object(cli.time, "sleep") as sleep:
            payload, exit_code = cli.wait_for_automated_review(
                "owner/repo", 12, "codex", None, 10, 1, 2, self.canonical_receipt("a" * 40)
            )

        self.assertEqual(exit_code, 4)
        self.assertEqual(payload["attempts"], 1)
        sleep.assert_not_called()

    def test_wait_head_drift_wins_over_binding_failure(self) -> None:
        stale = {
            "request_binding": "invalid",
            "review_state": "stale",
            "repo": "owner/repo",
            "pr": 12,
        }
        with mock.patch.object(cli, "check_automated_review", return_value=stale), mock.patch.object(
            cli.time, "sleep"
        ) as sleep:
            payload, exit_code = cli.wait_for_automated_review(
                "owner/repo", 12, "codex", None, 120, 1, 2, self.canonical_receipt("a" * 40)
            )

        self.assertEqual(exit_code, 3)
        self.assertEqual(payload["review_state"], "stale")
        sleep.assert_not_called()

    def test_check_maps_api_failures_to_exit_four(self) -> None:
        stdout = io.StringIO()
        failure = cli.ReviewError("API unavailable")
        with mock.patch.object(cli, "check_automated_review", side_effect=failure), contextlib.redirect_stdout(stdout):
            code = cli.main(
                ["--json", "check", "--provider", "codex", "--repo", "owner/repo", "--pr", "12"]
            )

        self.assertEqual(code, 4)
        self.assertEqual(json.loads(stdout.getvalue())["error"]["code"], "api_error")


class ReviewMutationAuthorityTests(unittest.TestCase):
    HEAD = "b" * 40
    REQUEST_KEY = "request-1"
    REQUEST_FINGERPRINT = "a" * 64

    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.addCleanup(self.directory.cleanup)
        self.cache_patch = mock.patch.object(
            cli, "_reservation_cache_root", return_value=self.root / "consumed"
        )
        self.cache_patch.start()
        self.addCleanup(self.cache_patch.stop)
        self.head_patch = mock.patch.object(cli, "_verify_pr_head")
        self.head_patch.start()
        self.addCleanup(self.head_patch.stop)

    def thread(self, *, head: str = HEAD, resolved: bool = False) -> dict[str, object]:
        return {
            "thread_id": "PRRT_thread_55",
            "is_resolved": resolved,
            "is_outdated": False,
            "viewer_can_resolve": True,
            "repository": "owner/repo",
            "pr_number": 12,
            "pr_state": "open",
            "head_sha": head,
            "comments": [
                {"id": "PRRC_finding_55", "databaseId": 55},
                {"id": "PRRC_reply_56", "databaseId": 56},
            ],
        }

    def packet_file(
        self,
        kind: str,
        *,
        body: str = "evidence body",
        head: str = HEAD,
        reply_receipt_fingerprint: str | None = None,
    ) -> tuple[Path, dict[str, object], str | None]:
        request_key = self.REQUEST_KEY
        request_fingerprint = self.REQUEST_FINGERPRINT
        thread_id: str | None = None
        thread_fingerprint: str | None = None
        finding_comment_id: int | None = None
        body_fingerprint: str | None = None
        marked_body: str | None = None
        if kind == "review-request":
            plan = build_request("codex", "owner/repo", 12, head, request_key)
            request_fingerprint = plan.request_fingerprint
            operation_id = operation_id_for_request(
                "owner/repo", 12, head, request_key, request_fingerprint
            )
            body_fingerprint = plan.body_fingerprint
        else:
            thread_id = "PRRT_thread_55" if kind in {"review-reply", "review-resolution"} else None
            finding_comment_id = 55 if thread_id else None
            if thread_id:
                thread_fingerprint = thread_identity_fingerprint(
                    "owner/repo",
                    12,
                    head,
                    thread_id,
                    [
                        {"node_id": "PRRC_finding_55", "comment_id": 55},
                        {"node_id": "PRRC_reply_56", "comment_id": 56},
                    ],
                )
            source_fingerprint = (
                reply_receipt_fingerprint
                if kind == "review-resolution"
                else text_fingerprint(body)
            )
            operation_id = operation_id_for_mutation(
                kind,
                "owner/repo",
                12,
                head,
                request_fingerprint=request_fingerprint,
                thread_id=thread_id,
                finding_comment_id=finding_comment_id,
                reply_receipt_fingerprint=(
                    source_fingerprint if kind == "review-resolution" else None
                ),
            )
            if kind != "review-resolution":
                marked_body = add_operation_marker(body, operation_id)
                body_fingerprint = text_fingerprint(marked_body)
        packet = build_reservation(
            mutation_kind=kind,
            repository="owner/repo",
            pr_number=12,
            head_sha=head,
            task_key="task-1",
            delivery_key="delivery-1",
            operation_id=operation_id,
            request_key=request_key,
            request_fingerprint=request_fingerprint,
            thread_id=thread_id,
            thread_fingerprint=thread_fingerprint,
            finding_comment_id=finding_comment_id,
            body_fingerprint=body_fingerprint,
            reply_receipt_fingerprint=(
                reply_receipt_fingerprint if kind == "review-resolution" else None
            ),
            expected_generation=1,
            expected_state_fingerprint="c" * 64,
            expected_claim_fingerprint="d" * 64,
            expected_task_state="review-polling",
        )
        path = self.root / f"{kind}.json"
        path.write_text(json.dumps(packet), encoding="utf-8")
        return path, packet, marked_body

    def test_all_review_mutations_fail_closed_without_reservation(self) -> None:
        body = ProviderText("body", b"body", "body")
        with self.assertRaises(cli.ReviewError) as request:
            cli.request_automated_review(
                "owner/repo", 12, "codex", self.HEAD, self.REQUEST_KEY,
                True, None, None,
            )
        self.assertEqual(request.exception.code, "reservation_required")

        with self.assertRaises(cli.ReviewError) as warning:
            cli.post_conversation_comment(
                "owner/repo", 12, body, True, None, self.HEAD,
                self.REQUEST_KEY, self.REQUEST_FINGERPRINT, None,
            )
        self.assertEqual(warning.exception.code, "reservation_required")

        parent = {
            "id": 55,
            "node_id": "PRRC_finding_55",
            "pull_request_url": "https://api.github.com/repos/owner/repo/pulls/12",
            "html_url": "https://github.com/owner/repo/pull/12#discussion_r55",
            "created_at": "2026-07-20T12:00:00Z",
            "in_reply_to_id": None,
            "commit_id": self.HEAD,
        }
        with mock.patch.object(cli, "_verify_pr_head"), \
             mock.patch.object(cli, "_api_object", return_value=parent), \
             mock.patch.object(cli, "_finding_thread", return_value=self.thread()), \
             self.assertRaises(cli.ReviewError) as reply:
            cli.reply_to_review_comment(
                "owner/repo", 12, self.HEAD, 55, body, True, None,
                self.REQUEST_KEY, self.REQUEST_FINGERPRINT, None,
            )
        self.assertEqual(reply.exception.code, "reservation_required")

        saved = {
            "repository": "owner/repo",
            "pr_number": 12,
            "reply_head_sha": self.HEAD,
            "thread_id": "PRRT_thread_55",
            "finding_comment_id": 55,
            "identity_fingerprint": "e" * 64,
        }
        with mock.patch.object(cli, "_validate_reply_remote", return_value=(saved, self.thread())), \
             self.assertRaises(cli.ReviewError) as resolve:
            cli.resolve_review_thread(
                "owner/repo", 12, self.HEAD, saved, True, None,
                self.REQUEST_KEY, self.REQUEST_FINGERPRINT, None,
            )
        self.assertEqual(resolve.exception.code, "reservation_required")

    def test_reconciliation_with_absent_marker_root_never_enters_transport(self) -> None:
        body = ProviderText("body", b"evidence body", "evidence body")
        request_file, request_packet, _ = self.packet_file("review-request")
        warning_file, _, _ = self.packet_file("review-warning")
        reply_file, _, _ = self.packet_file("review-reply")
        saved = {
            "repository": "owner/repo", "pr_number": 12,
            "finding_head_sha": self.HEAD, "reply_head_sha": self.HEAD,
            "thread_id": "PRRT_thread_55", "finding_comment_id": 55,
            "identity_fingerprint": "e" * 64,
        }
        resolve_file, _, _ = self.packet_file(
            "review-resolution", reply_receipt_fingerprint=saved["identity_fingerprint"],
        )
        parent = {
            "id": 55, "node_id": "PRRC_finding_55",
            "pull_request_url": "https://api.github.com/repos/owner/repo/pulls/12",
            "html_url": "https://github.com/owner/repo/pull/12#discussion_r55",
            "created_at": "2026-07-20T12:00:00Z", "in_reply_to_id": None,
            "commit_id": self.HEAD,
        }
        with mock.patch.object(cli, "api_request") as post, \
             mock.patch.object(cli, "graphql_request") as graphql, \
             mock.patch.object(cli, "_api_object", return_value=parent), \
             mock.patch.object(cli, "_finding_thread", return_value=self.thread()), \
             mock.patch.object(cli, "_validate_reply_remote", return_value=(saved, self.thread())):
            calls = (
                lambda: cli.request_automated_review(
                    "owner/repo", 12, "codex", self.HEAD, self.REQUEST_KEY, False, None,
                    str(request_file), reconcile_consumed=True,
                ),
                lambda: cli.post_conversation_comment(
                    "owner/repo", 12, body, False, None, self.HEAD,
                    self.REQUEST_KEY, self.REQUEST_FINGERPRINT,
                    str(warning_file), reconcile_consumed=True,
                ),
                lambda: cli.reply_to_review_comment(
                    "owner/repo", 12, self.HEAD, 55, body, False, None,
                    self.REQUEST_KEY, self.REQUEST_FINGERPRINT,
                    str(reply_file), reconcile_consumed=True,
                ),
                lambda: cli.resolve_review_thread(
                    "owner/repo", 12, self.HEAD, saved, False, None,
                    self.REQUEST_KEY, self.REQUEST_FINGERPRINT,
                    str(resolve_file), reconcile_consumed=True,
                ),
            )
            for call in calls:
                with self.assertRaises(cli.ReviewError) as rejected:
                    call()
                self.assertEqual(rejected.exception.code, "reservation_not_consumed")
            post.assert_not_called()
            graphql.assert_not_called()

    def test_owned_reply_rejects_stale_thread_identity_before_post(self) -> None:
        body = ProviderText("body", b"evidence body", "evidence body")
        reply_file, _, _ = self.packet_file("review-reply")
        parent = {
            "id": 55, "node_id": "PRRC_finding_55",
            "pull_request_url": "https://api.github.com/repos/owner/repo/pulls/12",
            "html_url": "https://github.com/owner/repo/pull/12#discussion_r55",
            "created_at": "2026-07-20T12:00:00Z", "in_reply_to_id": None,
            "commit_id": self.HEAD,
        }
        thread = self.thread()
        exact_fingerprint = cli._exact_thread_fingerprint(thread, "owner/repo", 12, self.HEAD)
        cases = (
            ("PRRT_stale", exact_fingerprint),
            (str(thread["thread_id"]), "f" * 64),
        )
        for expected_thread_id, expected_thread_fingerprint in cases:
            with self.subTest(
                expected_thread_id=expected_thread_id,
                expected_thread_fingerprint=expected_thread_fingerprint,
            ), mock.patch.object(cli, "_api_object", return_value=parent), \
                 mock.patch.object(cli, "_finding_thread", return_value=thread), \
                 mock.patch.object(cli, "api_request") as post, \
                 self.assertRaises(cli.ReviewError) as rejected:
                cli.reply_to_review_comment(
                    "owner/repo", 12, self.HEAD, 55, body, False, None,
                    self.REQUEST_KEY, self.REQUEST_FINGERPRINT,
                    str(reply_file), expected_thread_id=expected_thread_id,
                    expected_thread_fingerprint=expected_thread_fingerprint,
                )
            self.assertEqual(rejected.exception.code, "review_thread_mismatch")
            post.assert_not_called()

    def test_typed_prepare_and_validate_surface_writes_one_immutable_packet(self) -> None:
        output = self.root / "prepared.json"
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = cli.main([
                "--json", "prepare", "--mutation-kind", "review-request",
                "--repo", "owner/repo", "--allow-non-project", "--pr", "12",
                "--head", self.HEAD, "--task-key", "task-1",
                "--delivery-key", "delivery-1", "--request-key", self.REQUEST_KEY,
                "--expected-generation", "1", "--expected-state-fingerprint", "c" * 64,
                "--expected-claim-fingerprint", "d" * 64,
                "--expected-task-state", "review-polling", "--output-file", str(output),
            ])
        self.assertEqual(code, 0)
        packet = json.loads(output.read_text(encoding="utf-8"))
        self.assertNotIn("attempt_state", packet)
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = cli.main(["--json", "validate", "--reservation-file", str(output)])
        self.assertEqual(code, 0)
        validated = json.loads(stdout.getvalue())
        self.assertEqual(validated["data"]["reservation"], packet)

    def test_g_has_no_external_skill_authority_verifier(self) -> None:
        self.assertFalse(hasattr(cli, "_verify_started_ledger_authority"))
        self.assertFalse(hasattr(cli, "_ledger_cache_script"))

    def test_request_consumes_before_post_and_never_retries_after_crash(self) -> None:
        path, packet, _ = self.packet_file("review-request")
        plan = build_request("codex", "owner/repo", 12, self.HEAD, self.REQUEST_KEY)
        posted = mock.Mock()

        def crash_after_consumption(*_args: object, **_kwargs: object) -> object:
            consumed = list((self.root / "consumed").glob("*.consumed.json"))
            self.assertEqual(len(consumed), 1)
            raise RuntimeError("simulated crash before provider response")

        common = (
            mock.patch.object(cli, "_verify_pr_head"),
            mock.patch.object(cli, "gh_api_paginated_list", return_value=[]),
            mock.patch.object(cli, "require_worktree", return_value=None),
            mock.patch.object(cli, "_viewer_login", return_value="agent"),
            mock.patch.object(cli, "api_request", side_effect=crash_after_consumption),
        )
        with common[0], common[1], common[2], common[3], common[4] as mutation:
            with self.assertRaises(RuntimeError):
                cli.request_automated_review(
                    "owner/repo", 12, "codex", self.HEAD, self.REQUEST_KEY,
                    False, None, str(path),
                )
            self.assertEqual(mutation.call_count, 1)
            with self.assertRaises(cli.ReviewError) as replay:
                cli.request_automated_review(
                    "owner/repo", 12, "codex", self.HEAD, self.REQUEST_KEY,
                    False, None, str(path),
                )
        self.assertEqual(replay.exception.code, "request_unknown")
        self.assertEqual(replay.exception.details["recovery"], "needs-owner")
        self.assertEqual(packet["body_fingerprint"], plan.body_fingerprint)
        posted.assert_not_called()

    def test_request_post_ambiguity_is_not_retried(self) -> None:
        path, _, _ = self.packet_file("review-request")
        api = mock.Mock(return_value=Result(0, "not-json", ""))
        existing = mock.Mock(side_effect=[[], []])
        with mock.patch.object(cli, "_verify_pr_head"), \
             mock.patch.object(cli, "gh_api_paginated_list", existing), \
             mock.patch.object(cli, "require_worktree", return_value=None), \
             mock.patch.object(cli, "_viewer_login", return_value="agent"), \
             mock.patch.object(cli, "api_request", api), \
             self.assertRaises(cli.ReviewError) as first:
            cli.request_automated_review(
                "owner/repo", 12, "codex", self.HEAD, self.REQUEST_KEY,
                False, None, str(path),
            )
        self.assertEqual(first.exception.code, "request_unknown")
        self.assertEqual(api.call_count, 1)
        self.assertEqual(existing.call_count, 2)
        with mock.patch.object(cli, "_verify_pr_head"), \
             mock.patch.object(cli, "gh_api_paginated_list", return_value=[]), \
             mock.patch.object(cli, "require_worktree", return_value=None), \
             mock.patch.object(cli, "_viewer_login", return_value="agent"), \
             self.assertRaises(cli.ReviewError) as replay:
            cli.request_automated_review(
                "owner/repo", 12, "codex", self.HEAD, self.REQUEST_KEY,
                False, None, str(path),
            )
        self.assertEqual(replay.exception.code, "request_unknown")
        self.assertEqual(replay.exception.details["recovery"], "needs-owner")
        self.assertEqual(api.call_count, 1)

    def test_warning_post_consumes_before_post_and_replays_fail_closed(self) -> None:
        body = "timeout warning"
        path, packet, marked_body = self.packet_file("review-warning", body=body)
        item = {
            "id": 71,
            "html_url": "https://github.com/owner/repo/pull/12#issuecomment-71",
            "issue_url": "https://api.github.com/repos/owner/repo/issues/12",
            "user": {"login": "agent"},
            "body": marked_body,
            "created_at": "2026-07-20T12:00:00Z",
        }
        result = Result(0, json.dumps(item), "")
        clock = mock.patch.object(cli, "datetime")
        clock_value = clock.start()
        self.addCleanup(clock.stop)
        clock_value.now.return_value = datetime(2026, 7, 20, 12, 0, 0, tzinfo=timezone.utc)
        with mock.patch.object(cli, "_verify_pr_target", return_value={"number": 12}), \
             mock.patch.object(cli, "require_worktree", return_value=None), \
             mock.patch.object(cli, "_viewer_login", return_value="agent"), \
             mock.patch.object(cli, "api_request", return_value=result) as api, \
             mock.patch.object(cli, "gh_api_paginated_list", return_value=[item]):
            action = cli.post_conversation_comment(
                "owner/repo", 12, ProviderText("body", body.encode(), body), False, None,
                self.HEAD, self.REQUEST_KEY, self.REQUEST_FINGERPRINT, str(path),
            )
            self.assertEqual(action["status"], "posted")
            recovered = cli.post_conversation_comment(
                "owner/repo", 12, ProviderText("body", body.encode(), body), False, None,
                self.HEAD, self.REQUEST_KEY, self.REQUEST_FINGERPRINT, str(path),
            )
        self.assertEqual(recovered["status"], "recovered")
        self.assertEqual(api.call_count, 1)
        self.assertEqual(action["text"]["sha256"], text_fingerprint(marked_body or ""))

    def test_reply_ambiguity_is_not_retried_and_marker_is_exact(self) -> None:
        body = "evidence body"
        path, packet, marked_body = self.packet_file("review-reply", body=body)
        parent = {
            "id": 55,
            "node_id": "PRRC_finding_55",
            "pull_request_url": "https://api.github.com/repos/owner/repo/pulls/12",
            "html_url": "https://github.com/owner/repo/pull/12#discussion_r55",
            "created_at": "2026-07-20T12:00:00Z",
            "in_reply_to_id": None,
            "commit_id": self.HEAD,
        }
        api = mock.Mock(return_value=Result(0, "not-json", ""))
        read_back = mock.Mock(return_value=[])
        provider_body = ProviderText("body", body.encode(), body)
        with mock.patch.object(cli, "_verify_pr_head"), \
             mock.patch.object(cli, "_api_object", return_value=parent), \
             mock.patch.object(cli, "_finding_thread", return_value=self.thread()), \
             mock.patch.object(cli, "_review_thread_context", return_value=self.thread()), \
             mock.patch.object(cli, "require_worktree", return_value=None), \
             mock.patch.object(cli, "_viewer_login", return_value="agent"), \
             mock.patch.object(cli, "api_request", api), \
             mock.patch.object(cli, "gh_api_paginated_list", read_back), \
             self.assertRaises(cli.ReviewError) as first:
            cli.reply_to_review_comment(
                "owner/repo", 12, self.HEAD, 55, provider_body, False, None,
                self.REQUEST_KEY, self.REQUEST_FINGERPRINT, str(path),
            )
        self.assertEqual(first.exception.code, "provider_write_ambiguous")
        self.assertEqual(api.call_count, 1)
        self.assertEqual(read_back.call_count, 1)
        self.assertEqual(packet["body_fingerprint"], text_fingerprint(marked_body or ""))
        self.assertIn(packet["operation_id"], marked_body or "")
        with mock.patch.object(cli, "_verify_pr_head"), \
             mock.patch.object(cli, "_api_object", return_value=parent), \
             mock.patch.object(cli, "_finding_thread", return_value=self.thread()), \
             mock.patch.object(cli, "_review_thread_context", return_value=self.thread()), \
             mock.patch.object(cli, "require_worktree", return_value=None), \
             mock.patch.object(cli, "_viewer_login", return_value="agent"), \
             mock.patch.object(cli, "gh_api_paginated_list", return_value=[]), \
             self.assertRaises(cli.ReviewError) as replay:
            cli.reply_to_review_comment(
                "owner/repo", 12, self.HEAD, 55, provider_body, False, None,
                self.REQUEST_KEY, self.REQUEST_FINGERPRINT, str(path),
            )
        self.assertEqual(replay.exception.code, "provider_recovery_ambiguous")
        self.assertEqual(replay.exception.details["recovery"], "needs-owner")
        self.assertEqual(api.call_count, 1)

        recovered_item = {
            "id": 57,
            "node_id": "PRRC_reply_57",
            "pull_request_url": "https://api.github.com/repos/owner/repo/pulls/12",
            "html_url": "https://github.com/owner/repo/pull/12#discussion_r57",
            "created_at": "2026-07-20T12:02:00Z",
            "in_reply_to_id": 55,
            "user": {"login": "agent"},
            "body": marked_body,
        }
        recovery_thread = {
            **self.thread(),
            "comments": [
                *self.thread()["comments"],
                {"id": "PRRC_reply_57", "databaseId": 57},
            ],
        }
        with mock.patch.object(cli, "_verify_pr_head"), \
             mock.patch.object(cli, "_api_object", return_value=parent), \
             mock.patch.object(cli, "_finding_thread", return_value=self.thread()), \
             mock.patch.object(cli, "_review_thread_context", return_value=recovery_thread), \
             mock.patch.object(cli, "require_worktree", return_value=None), \
             mock.patch.object(cli, "_viewer_login", return_value="agent"), \
             mock.patch.object(cli, "gh_api_paginated_list", return_value=[recovered_item]):
            recovered = cli.reply_to_review_comment(
                "owner/repo", 12, self.HEAD, 55, provider_body, False, None,
                self.REQUEST_KEY, self.REQUEST_FINGERPRINT, str(path),
            )
        self.assertEqual(recovered["status"], "recovered")
        self.assertEqual(recovered["reply"]["reply_comment_id"], 57)
        self.assertEqual(api.call_count, 1)

    def test_resolution_reservation_uses_thread_readback_without_comment_marker(self) -> None:
        reply_fingerprint = "e" * 64
        path, packet, _ = self.packet_file(
            "review-resolution", reply_receipt_fingerprint=reply_fingerprint
        )
        saved = {
            "repository": "owner/repo",
            "pr_number": 12,
            "reply_head_sha": self.HEAD,
            "thread_id": "PRRT_thread_55",
            "finding_comment_id": 55,
            "identity_fingerprint": reply_fingerprint,
        }
        with mock.patch.object(cli, "_validate_reply_remote", return_value=(saved, self.thread())), \
             mock.patch.object(cli, "require_worktree", return_value=None):
            action = cli.resolve_review_thread(
                "owner/repo", 12, self.HEAD, saved, True, None,
                self.REQUEST_KEY, self.REQUEST_FINGERPRINT, str(path),
            )
        self.assertEqual(action["status"], "dry-run")
        self.assertNotIn("operation_id=", json.dumps(action))
        self.assertNotIn(packet["operation_id"], json.dumps(action))
        self.assertFalse(list((self.root / "consumed").glob("*.consumed.json")))

    def test_resolution_reconciles_consumed_thread_without_graphql_retry(self) -> None:
        finding = {
            "id": 55,
            "node_id": "PRRC_finding_55",
            "html_url": "https://github.com/owner/repo/pull/12#discussion_r55",
            "created_at": "2026-07-20T12:00:00Z",
        }
        reply = {
            "id": 56,
            "node_id": "PRRC_reply_56",
            "user": {"login": "agent"},
            "html_url": "https://github.com/owner/repo/pull/12#discussion_r56",
            "created_at": "2026-07-20T12:01:00Z",
        }
        saved = build_reply_receipt(
            repository="owner/repo",
            pr_number=12,
            finding_head_sha=self.HEAD,
            reply_head_sha=self.HEAD,
            thread_id="PRRT_thread_55",
            finding=finding,
            reply=reply,
            body_fingerprint="f" * 64,
            status="replied",
        )
        path, packet, _ = self.packet_file(
            "review-resolution",
            reply_receipt_fingerprint=saved["identity_fingerprint"],
        )
        thread = self.thread(resolved=True)
        cli._consume_reservation(packet, str(path))
        with mock.patch.object(cli, "_validate_reply_remote", return_value=(saved, thread)), \
             mock.patch.object(cli, "_review_thread_context", return_value=thread), \
             mock.patch.object(cli, "require_worktree", return_value=None), \
             mock.patch.object(cli, "graphql_request") as graphql:
            action = cli.resolve_review_thread(
                "owner/repo", 12, self.HEAD, saved, False, None,
                self.REQUEST_KEY, self.REQUEST_FINGERPRINT, str(path),
            )
        self.assertEqual(action["status"], "recovered")
        self.assertTrue(action["transport"]["recovered"])
        self.assertTrue(action["mutation_may_have_applied"])
        graphql.assert_not_called()


if __name__ == "__main__":
    unittest.main()
