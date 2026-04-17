#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import urllib.parse
from pathlib import Path


OFFICIAL_BASE_URL = "https://www.swift.org/documentation/api-design-guidelines/"
SOURCE_SUBPATH = "documentation/api-design-guidelines/index.md"
REPO_ROOT = Path(__file__).resolve().parents[4]
SKILL_DIR = REPO_ROOT / "skills" / "swift-api-design"
SKILL_PATH = SKILL_DIR / "SKILL.md"
ASSETS_DIR = SKILL_DIR / "assets"
ASSET_SOURCE_PATH = ASSETS_DIR / "api-design-guidelines.md"
ASSET_MANIFEST_PATH = ASSETS_DIR / "manifest.json"
REFERENCES_DIR = SKILL_DIR / "references"
RUNTIME_SCRIPTS_DIR = SKILL_DIR / "scripts"
SUMMARY_FILES = [
    "README.md",
    "official-guidelines.md",
    "core-principles.md",
    "naming-and-signatures.md",
    "common-api-shaping-patterns.md",
    "review-checklist.md",
]
MARKDOWN_LINK_RE = re.compile(r"(?<!\!)\[[^\]]+\]\(([^)]+)\)")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_links(markdown_path: Path) -> list[str]:
    content = markdown_path.read_text(encoding="utf-8")
    return [target.strip() for target in MARKDOWN_LINK_RE.findall(content)]


def resolve_local_link(markdown_path: Path, target: str) -> Path:
    decoded = urllib.parse.unquote(target.split("#", 1)[0])
    return (markdown_path.parent / decoded).resolve()


def main() -> int:
    errors: list[str] = []

    for required in [SKILL_PATH, ASSET_SOURCE_PATH, ASSET_MANIFEST_PATH]:
        if not required.exists():
            print(f"Missing required file: {required}")
            return 1

    manifest = load_json(ASSET_MANIFEST_PATH)

    if RUNTIME_SCRIPTS_DIR.exists():
        errors.append(f"Runtime skill should not keep a scripts directory: {RUNTIME_SCRIPTS_DIR}")

    for summary in SUMMARY_FILES:
        path = REFERENCES_DIR / summary
        if not path.exists():
            errors.append(f"Missing summary file: {path}")

    allowed_local_targets = {(REFERENCES_DIR / summary).resolve() for summary in SUMMARY_FILES}
    allowed_local_targets.add(ASSET_SOURCE_PATH.resolve())
    allowed_local_targets.add(ASSET_MANIFEST_PATH.resolve())

    for summary in SUMMARY_FILES:
        path = REFERENCES_DIR / summary
        if not path.exists():
            continue
        for link in iter_links(path):
            if not link or link.startswith("#"):
                continue
            if link.startswith(("http://", "https://")):
                errors.append(f"Summary file {path.name} should not link to external URL: {link}")
                continue
            target = resolve_local_link(path, link)
            if target not in allowed_local_targets:
                errors.append(f"Summary file {path.name} links to undeclared local target: {link}")
            elif not target.exists():
                errors.append(f"Broken local link in summary file {path.name}: {link}")

    forbidden_runtime_markers = [
        ".agents/skills/Maintainer",
        "python3 .agents/skills/Maintainer/scripts/swift_api_design_refresh.py",
        "python3 .agents/skills/Maintainer/scripts/swift_api_design_check.py",
    ]
    for path in [SKILL_PATH, REFERENCES_DIR / "README.md"]:
        content = path.read_text(encoding="utf-8")
        for marker in forbidden_runtime_markers:
            if marker in content:
                errors.append(f"Runtime skill doc {path} should not reference maintainer internals: {marker}")

    expected_manifest = {
        "source_subpath": SOURCE_SUBPATH,
        "official_base_url": OFFICIAL_BASE_URL,
    }
    expected_manifest_keys = {
        "repo",
        "ref",
        "resolved_commit",
        "source_subpath",
        "downloaded_at",
        "official_base_url",
    }
    extra_manifest_keys = set(manifest).difference(expected_manifest_keys)
    if extra_manifest_keys:
        errors.append(
            f"Manifest should only keep the bare minimum keys, found extras: {sorted(extra_manifest_keys)!r}"
        )
    for key, expected_value in expected_manifest.items():
        if manifest.get(key) != expected_value:
            errors.append(
                f"Manifest {key} mismatch: expected {expected_value!r}, got {manifest.get(key)!r}"
            )
    for key in ["repo", "ref", "resolved_commit", "downloaded_at"]:
        if not manifest.get(key):
            errors.append(f"Manifest missing required value for {key!r}.")

    if errors:
        print("Swift API Design reference validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Swift API Design reference validation passed.")
    print(f"- Asset file: {ASSET_SOURCE_PATH}")
    print(f"- Summary files: {', '.join(SUMMARY_FILES)}")
    print(f"- Manifest: {ASSET_MANIFEST_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
