#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_REPO = "swiftlang/swift-org-website"
DEFAULT_REF = "main"
SOURCE_SUBPATH = Path("documentation/api-design-guidelines/index.md")
OFFICIAL_BASE_URL = "https://www.swift.org/documentation/api-design-guidelines/"
USER_AGENT = "maintainer-swift-api-design-refresh"

REPO_ROOT = Path(__file__).resolve().parents[4]
SKILL_DIR = REPO_ROOT / "skills" / "swift-api-design"
ASSETS_DIR = SKILL_DIR / "assets"
ASSET_SOURCE_PATH = ASSETS_DIR / "api-design-guidelines.md"
ASSET_MANIFEST_PATH = ASSETS_DIR / "manifest.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Refresh the bundled Swift API Design source asset from Maintainer."
    )
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--ref", default=DEFAULT_REF)
    parser.add_argument(
        "--check-stale",
        action="store_true",
        help="Report whether the bundled source asset is stale without changing files.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force a bundled-asset refresh even if the manifest matches upstream.",
    )
    return parser.parse_args()


def load_manifest() -> dict | None:
    if not ASSET_MANIFEST_PATH.exists():
        return None
    return json.loads(ASSET_MANIFEST_PATH.read_text(encoding="utf-8"))


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def download_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8")


def resolve_commit(repo: str, ref: str) -> str:
    payload = fetch_json(
        f"https://api.github.com/repos/{repo}/commits/{urllib.parse.quote(ref, safe='')}"
    )
    return payload["sha"]


def raw_source_url(repo: str, ref: str) -> str:
    owner, name = repo.split("/", 1)
    return (
        "https://raw.githubusercontent.com/"
        f"{owner}/{name}/{urllib.parse.quote(ref, safe='')}/{SOURCE_SUBPATH.as_posix()}"
    )


def asset_stale_reasons(manifest: dict | None, repo: str, ref: str, latest_commit: str) -> list[str]:
    reasons: list[str] = []
    if not ASSET_SOURCE_PATH.exists():
        reasons.append("Bundled guideline source file is missing.")
    if manifest is None:
        reasons.append("Manifest is missing.")
        return reasons

    expected = {
        "repo": repo,
        "ref": ref,
        "resolved_commit": latest_commit,
        "source_subpath": SOURCE_SUBPATH.as_posix(),
        "official_base_url": OFFICIAL_BASE_URL,
    }
    for key, expected_value in expected.items():
        if manifest.get(key) != expected_value:
            reasons.append(
                f"Manifest {key} mismatch: expected {expected_value!r}, got {manifest.get(key)!r}"
            )
    return reasons


def write_manifest(repo: str, ref: str, commit: str) -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {
        "repo": repo,
        "ref": ref,
        "resolved_commit": commit,
        "source_subpath": SOURCE_SUBPATH.as_posix(),
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "official_base_url": OFFICIAL_BASE_URL,
    }
    ASSET_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    latest_commit = resolve_commit(args.repo, args.ref)
    manifest = load_manifest()
    reasons = asset_stale_reasons(manifest, args.repo, args.ref, latest_commit)

    if args.check_stale:
        status = "STALE" if reasons else "FRESH"
        print(f"swift-api-design bundled assets status: {status}")
        print(f"- Skill dir: {SKILL_DIR}")
        print(f"- Upstream: {args.repo}@{args.ref} ({latest_commit})")
        if manifest and manifest.get("resolved_commit"):
            print(f"- Local manifest commit: {manifest['resolved_commit']}")
        if reasons:
            for reason in reasons:
                print(f"- {reason}")
        return 0

    if args.force or reasons:
        ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        ASSET_SOURCE_PATH.write_text(
            download_text(raw_source_url(args.repo, args.ref)),
            encoding="utf-8",
        )
        write_manifest(args.repo, args.ref, latest_commit)
        print("Bundled Swift API Design source refreshed.")
        print(f"- Asset file: {ASSET_SOURCE_PATH}")
        print(f"- Manifest: {ASSET_MANIFEST_PATH}")
        print(f"- Upstream: {args.repo}@{args.ref} ({latest_commit})")
        return 0

    print("Bundled Swift API Design source already up to date.")
    print(f"- Manifest: {ASSET_MANIFEST_PATH}")
    print(f"- Upstream: {args.repo}@{args.ref} ({latest_commit})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
