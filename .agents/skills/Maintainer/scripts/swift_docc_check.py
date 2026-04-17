#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import urllib.parse
from pathlib import Path


OFFICIAL_BASE_URL = "https://www.swift.org/documentation/docc"
SOURCE_SUBPATH = "Sources/docc/DocCDocumentation.docc"
REPO_ROOT = Path(__file__).resolve().parents[4]
SKILL_DIR = REPO_ROOT / "skills" / "swift-docc"
SKILL_PATH = SKILL_DIR / "SKILL.md"
ASSETS_DIR = SKILL_DIR / "assets"
ASSET_DOCC_DIR = ASSETS_DIR / "DocCDocumentation.docc"
ASSET_MANIFEST_PATH = ASSETS_DIR / "manifest.json"
REFERENCES_DIR = SKILL_DIR / "references"
CATALOG_PATH = REFERENCES_DIR / "catalog.json"
SOURCE_MAP_PATH = REFERENCES_DIR / "source-map.md"
LEGACY_OFFICIAL_DIR = REFERENCES_DIR / "official"
LEGACY_UPSTREAM_DIR = REFERENCES_DIR / "upstream"
LEGACY_MANIFEST_PATH = REFERENCES_DIR / "source-manifest.json"
RUNTIME_SCRIPTS_DIR = SKILL_DIR / "scripts"
SUMMARY_FILES = [
    "README.md",
    "document-a-swift-package.md",
    "document-public-symbols.md",
    "document-api-lifecycle-and-behavior.md",
    "add-a-docc-catalog.md",
    "preview-and-publish.md",
    "tutorial-workflow.md",
    "start-here.md",
    "symbol-docs.md",
    "articles-and-structure.md",
    "linking.md",
    "formatting-and-assets.md",
    "tutorials.md",
    "publishing-and-customization.md",
    "directive-map.md",
    "source-map.md",
]
REMOVED_V2_FILES = [
    "essentials.md",
    "content.md",
    "formatting.md",
    "distribution.md",
    "reference-syntax.md",
]
MARKDOWN_LINK_RE = re.compile(r"(?<!\!)\[[^\]]+\]\(([^)]+)\)")
EXAMPLE_URL_RE = re.compile(r"https?://(?:www\.)?example\.com/")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_links(markdown_path: Path) -> list[str]:
    content = markdown_path.read_text(encoding="utf-8")
    return [target.strip() for target in MARKDOWN_LINK_RE.findall(content)]


def resolve_local_link(markdown_path: Path, target: str) -> Path:
    decoded = urllib.parse.unquote(target.split("#", 1)[0])
    return (markdown_path.parent / decoded).resolve()


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
        local = f"../{urllib.parse.quote(primary['asset_path'], safe='/')}"
        lines.append(
            f"| {intent['question']} | [Summary]({intent['summary_page']}) | [Local source]({local}) |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    errors: list[str] = []

    for required in [SKILL_PATH, CATALOG_PATH, ASSET_MANIFEST_PATH, SOURCE_MAP_PATH]:
        if not required.exists():
            print(f"Missing required file: {required}")
            return 1

    catalog = load_json(CATALOG_PATH)
    manifest = load_json(ASSET_MANIFEST_PATH)
    topics = catalog.get("topics", [])
    intents = catalog.get("intents", [])
    topic_ids = set()

    required_top_level = {"repo", "ref", "source_subpath", "topics", "intents"}
    missing_top_level = required_top_level.difference(catalog)
    if missing_top_level:
        errors.append(f"Catalog missing top-level keys: {sorted(missing_top_level)!r}")

    if not ASSET_DOCC_DIR.exists():
        errors.append(f"Missing asset DocC tree: {ASSET_DOCC_DIR}")
    if RUNTIME_SCRIPTS_DIR.exists():
        errors.append(f"Runtime skill should not keep a scripts directory: {RUNTIME_SCRIPTS_DIR}")
    if LEGACY_OFFICIAL_DIR.exists():
        errors.append(f"Legacy curated cache directory still exists: {LEGACY_OFFICIAL_DIR}")
    if LEGACY_UPSTREAM_DIR.exists():
        errors.append(f"Legacy upstream mirror directory still exists: {LEGACY_UPSTREAM_DIR}")
    if LEGACY_MANIFEST_PATH.exists():
        errors.append(f"Legacy manifest still exists: {LEGACY_MANIFEST_PATH}")

    for summary in SUMMARY_FILES:
        path = REFERENCES_DIR / summary
        if not path.exists():
            errors.append(f"Missing summary file: {path}")

    for stale in REMOVED_V2_FILES:
        path = REFERENCES_DIR / stale
        if path.exists():
            errors.append(f"Unexpected legacy v2 summary remains: {path}")

    required_topic_keys = {
        "id",
        "title",
        "category",
        "upstream_path",
        "asset_path",
        "summary_page",
    }

    for topic in topics:
        missing = required_topic_keys.difference(topic)
        if missing:
            errors.append(f"Topic {topic.get('id', '<missing-id>')} missing keys: {sorted(missing)!r}")
            continue
        if "official_url" in topic:
            errors.append(f"Topic {topic['id']} should not declare official_url.")
        if topic["id"] in topic_ids:
            errors.append(f"Duplicate topic id: {topic['id']}")
        topic_ids.add(topic["id"])
        if topic["summary_page"] not in SUMMARY_FILES:
            errors.append(
                f"Topic {topic['id']} points to unknown summary page: {topic['summary_page']!r}"
            )
        asset_path = SKILL_DIR / topic["asset_path"]
        if not asset_path.exists():
            errors.append(f"Missing local asset for topic {topic['id']}: {asset_path}")
            continue
        if topic["upstream_path"] != Path(topic["asset_path"]).relative_to("assets/DocCDocumentation.docc").as_posix():
            errors.append(
                f"Topic {topic['id']} asset_path does not align with upstream_path."
            )
        if asset_path.suffix == ".md":
            content = asset_path.read_text(encoding="utf-8")
            if EXAMPLE_URL_RE.search(content) and not topic.get("example_url", False):
                errors.append(
                    f"Placeholder example.com URL found in non-example topic asset: {topic['id']}"
                )
            for link in iter_links(asset_path):
                if link.startswith(("http://", "https://", "mailto:", "doc:")):
                    continue
                if link.startswith("#"):
                    continue
                target = resolve_local_link(asset_path, link)
                if not target.exists():
                    errors.append(f"Broken relative link in asset markdown {asset_path.name}: {link}")

    topic_lookup = {topic["id"]: topic for topic in topics}
    for intent in intents:
        for key in ["question", "summary_page", "primary_topic_id"]:
            if key not in intent:
                errors.append(f"Intent missing key {key!r}: {intent!r}")
        if intent.get("summary_page") not in SUMMARY_FILES:
            errors.append(f"Intent points to unknown summary page: {intent!r}")
        if intent.get("primary_topic_id") not in topic_lookup:
            errors.append(f"Intent references unknown topic id: {intent!r}")

    expected_source_map = render_source_map(catalog)
    if SOURCE_MAP_PATH.read_text(encoding="utf-8") != expected_source_map:
        errors.append("source-map.md is out of date with catalog.json.")

    allowed_local_targets = {(REFERENCES_DIR / summary).resolve() for summary in SUMMARY_FILES}
    allowed_local_targets.update((SKILL_DIR / topic["asset_path"]).resolve() for topic in topics)

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
        "python3 scripts/",
        "scripts/refresh_references.py",
        "scripts/check_references.py",
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
        print("Swift-DocC reference validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Swift-DocC reference validation passed.")
    print(f"- Catalog: {CATALOG_PATH}")
    print(f"- Asset root: {ASSET_DOCC_DIR}")
    print(f"- Summary files: {', '.join(SUMMARY_FILES)}")
    print(f"- Manifest: {ASSET_MANIFEST_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
