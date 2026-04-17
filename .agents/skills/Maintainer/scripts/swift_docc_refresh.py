#!/usr/bin/env python3
from __future__ import annotations

import argparse
import io
import json
import shutil
import tarfile
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_REPO = "swiftlang/swift-docc"
DEFAULT_REF = "main"
SOURCE_SUBPATH = Path("Sources/docc/DocCDocumentation.docc")
OFFICIAL_BASE_URL = "https://www.swift.org/documentation/docc"
USER_AGENT = "maintainer-swift-docc-refresh"

REPO_ROOT = Path(__file__).resolve().parents[4]
SKILL_DIR = REPO_ROOT / "skills" / "swift-docc"
ASSETS_DIR = SKILL_DIR / "assets"
ASSET_DOCC_DIR = ASSETS_DIR / "DocCDocumentation.docc"
ASSET_MANIFEST_PATH = ASSETS_DIR / "manifest.json"
REFERENCES_DIR = SKILL_DIR / "references"
CATALOG_PATH = REFERENCES_DIR / "catalog.json"
SOURCE_MAP_PATH = REFERENCES_DIR / "source-map.md"
LEGACY_OFFICIAL_DIR = REFERENCES_DIR / "official"
LEGACY_UPSTREAM_DIR = REFERENCES_DIR / "upstream"
LEGACY_MANIFEST_PATH = REFERENCES_DIR / "source-manifest.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Refresh the bundled Swift-DocC asset tree from Maintainer."
    )
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--ref", default=DEFAULT_REF)
    parser.add_argument(
        "--check-stale",
        action="store_true",
        help="Report whether the bundled DocC tree is stale without changing files.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force a bundled-asset refresh even if the manifest matches upstream.",
    )
    return parser.parse_args()


def load_catalog() -> dict:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def load_manifest() -> dict | None:
    if not ASSET_MANIFEST_PATH.exists():
        return None
    return json.loads(ASSET_MANIFEST_PATH.read_text(encoding="utf-8"))


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def download_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def resolve_commit(repo: str, ref: str) -> str:
    payload = fetch_json(
        f"https://api.github.com/repos/{repo}/commits/{urllib.parse.quote(ref, safe='')}"
    )
    return payload["sha"]


def download_archive(repo: str, ref: str, destination: Path) -> Path:
    archive_bytes = download_bytes(f"https://api.github.com/repos/{repo}/tarball/{ref}")
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as archive:
        archive.extractall(destination)
    extracted = [child for child in destination.iterdir() if child.is_dir()]
    if len(extracted) != 1:
        raise RuntimeError(f"Expected exactly one extracted root, found {len(extracted)}")
    return extracted[0]


def asset_link(asset_path: str) -> str:
    return f"../{urllib.parse.quote(asset_path, safe='/')}"


def render_source_map(catalog: dict) -> str:
    topics = {topic["id"]: topic for topic in catalog["topics"]}
    lines = [
        "# Source Map",
        "",
        "Task-language routing for the `swift-docc` skill.",
        "",
        "| Question | Summary | Local source |",
        "| --- | --- | --- |",
    ]
    for intent in catalog["intents"]:
        primary = topics[intent["primary_topic_id"]]
        summary = f"[Summary]({intent['summary_page']})"
        local = f"[Local source]({asset_link(primary['asset_path'])})"
        lines.append(f"| {intent['question']} | {summary} | {local} |")
    lines.append("")
    return "\n".join(lines)


def asset_stale_reasons(manifest: dict | None, repo: str, ref: str, latest_commit: str) -> list[str]:
    reasons: list[str] = []
    if not ASSET_DOCC_DIR.exists():
        reasons.append("Bundled DocCDocumentation.docc tree is missing.")
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


def clean_generated_output() -> None:
    for path in [ASSET_DOCC_DIR, LEGACY_OFFICIAL_DIR, LEGACY_UPSTREAM_DIR]:
        if path.exists():
            shutil.rmtree(path)
    for path in [ASSET_MANIFEST_PATH, SOURCE_MAP_PATH, LEGACY_MANIFEST_PATH]:
        if path.exists():
            path.unlink()


def refresh_assets(catalog: dict, repo: str, ref: str) -> int:
    with tempfile.TemporaryDirectory() as temp_dir:
        extracted_root = download_archive(repo, ref, Path(temp_dir))
        upstream_root = extracted_root / SOURCE_SUBPATH
        if not upstream_root.exists():
            raise FileNotFoundError(f"Missing upstream DocCDocumentation.docc at {upstream_root}")
        ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copytree(upstream_root, ASSET_DOCC_DIR)

    for topic in catalog["topics"]:
        asset_path = SKILL_DIR / topic["asset_path"]
        if not asset_path.exists():
            raise FileNotFoundError(
                f"Missing bundled asset for topic {topic['id']}: {asset_path}"
            )

    return sum(1 for path in ASSET_DOCC_DIR.rglob("*") if path.is_file())


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
    catalog = load_catalog()
    latest_commit = resolve_commit(args.repo, args.ref)
    manifest = load_manifest()
    reasons = asset_stale_reasons(manifest, args.repo, args.ref, latest_commit)

    if args.check_stale:
        status = "STALE" if reasons else "FRESH"
        print(f"swift-docc bundled assets status: {status}")
        print(f"- Skill dir: {SKILL_DIR}")
        print(f"- Upstream: {args.repo}@{args.ref} ({latest_commit})")
        if manifest and manifest.get("resolved_commit"):
            print(f"- Local manifest commit: {manifest['resolved_commit']}")
        if reasons:
            for reason in reasons:
                print(f"- {reason}")
        return 0

    source_map_text = render_source_map(catalog)
    if args.force or reasons:
        clean_generated_output()
        asset_file_count = refresh_assets(catalog, args.repo, args.ref)
        SOURCE_MAP_PATH.write_text(source_map_text, encoding="utf-8")
        write_manifest(args.repo, args.ref, latest_commit)
        print("Bundled Swift-DocC assets refreshed.")
        print(f"- Asset root: {ASSET_DOCC_DIR}")
        print(f"- Asset files: {asset_file_count}")
        print(f"- Source map: {SOURCE_MAP_PATH}")
        print(f"- Manifest: {ASSET_MANIFEST_PATH}")
        print(f"- Upstream: {args.repo}@{args.ref} ({latest_commit})")
        return 0

    SOURCE_MAP_PATH.write_text(source_map_text, encoding="utf-8")
    print("Bundled Swift-DocC assets already up to date.")
    print(f"- Manifest: {ASSET_MANIFEST_PATH}")
    print(f"- Upstream: {args.repo}@{args.ref} ({latest_commit})")
    print(f"- Source map regenerated: {SOURCE_MAP_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
