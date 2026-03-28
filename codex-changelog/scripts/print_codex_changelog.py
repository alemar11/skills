#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser

GITHUB_RELEASE_API_BASE = "https://api.github.com/repos/openai/codex/releases/tags/"
APP_CHANGELOG_URL = "https://developers.openai.com/codex/changelog"
APP_CHANGELOG_FILTER_URL = f"{APP_CHANGELOG_URL}?type=codex-app"
APP_BUNDLE_ID = "com.openai.codex"


@dataclass
class SectionResult:
    title: str
    body: str
    ok: bool


@dataclass
class AppChangelogEntry:
    entry_id: str
    topics: tuple[str, ...]
    date: str
    title: str
    version: str | None
    body_text: str

    @property
    def source_url(self) -> str:
        if not self.entry_id:
            return APP_CHANGELOG_FILTER_URL
        return f"{APP_CHANGELOG_URL}#{self.entry_id}"


class CodexAppEntriesParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.entries: list[AppChangelogEntry] = []
        self._current_entry: dict[str, object] | None = None
        self._entry_li_depth = 0
        self._in_time = False
        self._in_title = False
        self._in_article = False
        self._article_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key: value or "" for key, value in attrs}
        if self._current_entry is None and tag == "li":
            topics = tuple(
                topic.strip()
                for topic in attrs_dict.get("data-codex-topics", "").split()
                if topic.strip()
            )
            if "codex-app" not in topics:
                return
            self._current_entry = {
                "entry_id": attrs_dict.get("id", ""),
                "topics": topics,
                "date_parts": [],
                "title_parts": [],
                "body_html_parts": [],
            }
            self._entry_li_depth = 1
            return

        if self._current_entry is None:
            return

        if tag == "li":
            self._entry_li_depth += 1

        if tag == "time":
            self._in_time = True
            return
        if tag == "h3":
            self._in_title = True
            return
        if tag == "article":
            self._in_article = True
            self._article_depth = 1
            return

        if self._in_article:
            self._article_depth += 1
            self._body_html_parts.append(self.get_starttag_text())

    def handle_endtag(self, tag: str) -> None:
        if self._current_entry is None:
            return

        if tag == "time":
            self._in_time = False
        elif tag == "h3":
            self._in_title = False
        elif self._in_article:
            if tag == "article" and self._article_depth == 1:
                self._in_article = False
                self._article_depth = 0
            else:
                self._body_html_parts.append(f"</{tag}>")
                self._article_depth -= 1

        if tag == "li":
            self._entry_li_depth -= 1
        if tag == "li" and self._entry_li_depth == 0:
            self._finalize_entry()

    def handle_startendtag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if self._current_entry is not None and self._in_article:
            attrs_string = "".join(
                f' {key}="{value or ""}"' for key, value in attrs
            )
            self._body_html_parts.append(f"<{tag}{attrs_string}/>")

    def handle_data(self, data: str) -> None:
        if self._current_entry is None:
            return
        if self._in_time:
            self._date_parts.append(data)
        if self._in_title:
            self._title_parts.append(data)
        if self._in_article:
            self._body_html_parts.append(data)

    def handle_entityref(self, name: str) -> None:
        self.handle_data(unescape(f"&{name};"))

    def handle_charref(self, name: str) -> None:
        self.handle_data(unescape(f"&#{name};"))

    @property
    def _date_parts(self) -> list[str]:
        assert self._current_entry is not None
        return self._current_entry["date_parts"]  # type: ignore[return-value]

    @property
    def _title_parts(self) -> list[str]:
        assert self._current_entry is not None
        return self._current_entry["title_parts"]  # type: ignore[return-value]

    @property
    def _body_html_parts(self) -> list[str]:
        assert self._current_entry is not None
        return self._current_entry["body_html_parts"]  # type: ignore[return-value]

    def _finalize_entry(self) -> None:
        assert self._current_entry is not None
        title = normalize_space("".join(self._title_parts))
        version_match = re.search(r"\b(\d+\.\d+(?:\.\d+)*)\b", title)
        entry = AppChangelogEntry(
            entry_id=str(self._current_entry["entry_id"]),
            topics=tuple(self._current_entry["topics"]),  # type: ignore[arg-type]
            date=normalize_space("".join(self._date_parts)),
            title=title,
            version=version_match.group(1) if version_match else None,
            body_text=html_to_text("".join(self._body_html_parts)),
        )
        self.entries.append(entry)
        self._current_entry = None
        self._entry_li_depth = 0
        self._in_time = False
        self._in_title = False
        self._in_article = False
        self._article_depth = 0


class HtmlToTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._in_pre = False
        self._code_depth = 0
        self._list_depth = 0

    def text(self) -> str:
        text = "".join(self._parts)
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._ensure_blank_line()
        elif tag in {"p", "div", "section", "details", "summary"}:
            self._ensure_blank_line()
        elif tag in {"ul", "ol"}:
            self._ensure_blank_line()
            self._list_depth += 1
        elif tag == "li":
            self._ensure_newline()
            self._parts.append("- ")
        elif tag == "br":
            self._ensure_newline()
        elif tag == "pre":
            self._ensure_blank_line()
            self._parts.append("```\n")
            self._in_pre = True
        elif tag == "code":
            if self._in_pre:
                return
            self._code_depth += 1
            self._parts.append("`")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._ensure_blank_line()
        elif tag in {"p", "div", "section", "details", "summary"}:
            self._ensure_blank_line()
        elif tag in {"ul", "ol"}:
            self._list_depth = max(0, self._list_depth - 1)
            self._ensure_blank_line()
        elif tag == "li":
            self._ensure_newline()
        elif tag == "pre":
            if self._parts and not self._parts[-1].endswith("\n"):
                self._parts.append("\n")
            self._parts.append("```")
            self._ensure_blank_line()
            self._in_pre = False
        elif tag == "code" and self._code_depth > 0:
            self._parts.append("`")
            self._code_depth -= 1

    def handle_data(self, data: str) -> None:
        if not data:
            return
        if self._in_pre:
            self._parts.append(data)
            return
        text = normalize_space(data)
        if not text:
            return
        if self._needs_space_before(text):
            self._parts.append(" ")
        self._parts.append(text)

    def _ensure_newline(self) -> None:
        if not self._parts:
            return
        if not self._parts[-1].endswith("\n"):
            self._parts.append("\n")

    def _ensure_blank_line(self) -> None:
        if not self._parts:
            return
        text = "".join(self._parts)
        if text.endswith("\n\n"):
            return
        if text.endswith("\n"):
            self._parts.append("\n")
        else:
            self._parts.append("\n\n")

    def _needs_space_before(self, text: str) -> bool:
        if not self._parts:
            return False
        previous = self._parts[-1]
        if not previous:
            return False
        last_char = previous[-1]
        if last_char.isspace() or last_char in "([{/`":
            return False
        if text[0] in ".,;:!?)]}/":
            return False
        return True


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def html_to_text(fragment: str) -> str:
    parser = HtmlToTextParser()
    parser.feed(fragment)
    parser.close()
    return parser.text()


def run_command(args: list[str]) -> str:
    try:
        return subprocess.check_output(args, text=True).strip()
    except Exception as exc:
        joined = " ".join(args)
        raise RuntimeError(f"Failed to run '{joined}'.") from exc


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "codex-version-changelog",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_text(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/html,application/xhtml+xml",
            "User-Agent": "codex-version-changelog",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8")


def get_codex_cli_version() -> str:
    output = run_command(["codex", "--version"])
    match = re.search(r"(\d+\.\d+\.\d+(?:[-+][0-9A-Za-z_.]+)?)", output)
    if not match:
        raise RuntimeError(f"Unable to parse Codex CLI version from: {output}")
    version = match.group(1)
    if version.startswith("v"):
        version = version[1:]
    return version


def find_codex_app_path() -> str:
    try:
        output = run_command(
            ["mdfind", f"kMDItemCFBundleIdentifier == '{APP_BUNDLE_ID}'"]
        )
        for line in output.splitlines():
            path = line.strip()
            if path.endswith(".app") and os.path.exists(path):
                return path
    except RuntimeError:
        pass

    fallback_paths = [
        "/Applications/Codex.app",
        os.path.expanduser("~/Applications/Codex.app"),
    ]
    for path in fallback_paths:
        if os.path.exists(path):
            return path

    raise RuntimeError("Unable to locate the Codex app on this machine.")


def get_codex_app_version() -> tuple[str, str]:
    app_path = find_codex_app_path()
    plist_path = os.path.join(app_path, "Contents", "Info.plist")
    if not os.path.exists(plist_path):
        raise RuntimeError(f"Missing Info.plist for Codex app at: {app_path}")

    try:
        version = run_command(
            ["plutil", "-extract", "CFBundleShortVersionString", "raw", plist_path]
        )
    except RuntimeError as exc:
        raise RuntimeError(
            f"Unable to read Codex app version from: {plist_path}"
        ) from exc

    if not version:
        raise RuntimeError(f"Codex app version was empty in: {plist_path}")
    return version, app_path


def fetch_github_release(tag: str) -> dict:
    return fetch_json(f"{GITHUB_RELEASE_API_BASE}{tag}")


def fetch_codex_app_entries() -> list[AppChangelogEntry]:
    parser = CodexAppEntriesParser()
    parser.feed(fetch_text(APP_CHANGELOG_URL))
    parser.close()
    desktop_entries = [
        entry
        for entry in parser.entries
        if entry.title.lower().startswith("codex app") and entry.version
    ]
    return desktop_entries


def app_version_candidates(version: str) -> list[str]:
    candidates: list[str] = []
    for candidate in (version, ".".join(version.split(".")[:2])):
        if candidate and candidate not in candidates:
            candidates.append(candidate)
    return candidates


def format_section(title: str, body: str) -> str:
    divider = "=" * len(title)
    return f"{title}\n{divider}\n{body.strip()}"


def build_cli_section() -> SectionResult:
    try:
        version = get_codex_cli_version()
    except RuntimeError as exc:
        return SectionResult("Codex CLI", str(exc), ok=False)

    tags_to_try = [f"rust-v{version}", f"v{version}", version]
    release = None
    last_error = None

    for tag in tags_to_try:
        try:
            release = fetch_github_release(tag)
            break
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                last_error = exc
                continue
            return SectionResult(
                "Codex CLI",
                f"GitHub API error for tag {tag}: {exc}",
                ok=False,
            )
        except Exception as exc:
            return SectionResult(
                "Codex CLI",
                f"Failed to fetch GitHub release for tag {tag}: {exc}",
                ok=False,
            )

    if release is None:
        detail = f" ({last_error})" if last_error is not None else ""
        return SectionResult(
            "Codex CLI",
            "No matching GitHub release found for tags: "
            + ", ".join(tags_to_try)
            + detail,
            ok=False,
        )

    lines = [
        f"Installed version: {version}",
        f"Release: {release.get('name') or release.get('tag_name') or '(unknown)'}",
        f"Published: {release.get('published_at') or '(unknown)'}",
        f"Source: {release.get('html_url') or '(unknown)'}",
        "",
        release.get("body") or "(no changelog body)",
    ]
    return SectionResult("Codex CLI", "\n".join(lines), ok=True)


def build_app_section() -> SectionResult:
    version = None
    app_path = None
    version_error = None

    try:
        version, app_path = get_codex_app_version()
    except RuntimeError as exc:
        version_error = str(exc)

    try:
        entries = fetch_codex_app_entries()
    except Exception as exc:
        message_lines = []
        if version is not None:
            message_lines.append(f"Installed version: {version}")
            if app_path is not None:
                message_lines.append(f"App path: {app_path}")
        elif version_error is not None:
            message_lines.append(version_error)
        message_lines.append(f"Failed to fetch Codex App changelog page: {exc}")
        return SectionResult("Codex App", "\n".join(message_lines), ok=False)

    if version is None:
        lines = []
        if version_error is not None:
            lines.append(version_error)
        if not entries:
            lines.append("No desktop Codex App entries were found on the changelog page.")
            return SectionResult("Codex App", "\n".join(lines), ok=False)

        latest = entries[0]
        lines.extend(
            [
                f"Latest available app changelog: {latest.version} ({latest.date})",
                f"Source: {latest.source_url}",
                "",
                latest.body_text or "(no changelog body)",
            ]
        )
        return SectionResult("Codex App", "\n".join(lines), ok=True)

    attempted_versions = app_version_candidates(version)
    matching_entry = next(
        (
            entry
            for candidate in attempted_versions
            for entry in entries
            if entry.version == candidate
        ),
        None,
    )

    if matching_entry is not None:
        lines = [
            f"Installed version: {version}",
            f"App path: {app_path}",
            f"Matched changelog version: {matching_entry.version}",
            f"Published: {matching_entry.date or '(unknown)'}",
            f"Source: {matching_entry.source_url}",
            "",
            matching_entry.body_text or "(no changelog body)",
        ]
        return SectionResult("Codex App", "\n".join(lines), ok=True)

    lines = [
        f"Installed version: {version}",
        f"App path: {app_path}",
        "No exact Codex App changelog entry matched the installed app version.",
        f"Attempted versions: {', '.join(attempted_versions)}",
    ]
    if entries:
        latest = entries[0]
        lines.extend(
            [
                f"Latest available app changelog: {latest.version} ({latest.date})",
                f"Source: {latest.source_url}",
                "",
                latest.body_text or "(no changelog body)",
            ]
        )
        return SectionResult("Codex App", "\n".join(lines), ok=True)

    lines.append("No desktop Codex App entries were found on the changelog page.")
    return SectionResult("Codex App", "\n".join(lines), ok=False)


def main() -> int:
    cli_section = build_cli_section()
    app_section = build_app_section()

    print(format_section(cli_section.title, cli_section.body))
    print()
    print(format_section(app_section.title, app_section.body))

    return 0 if cli_section.ok or app_section.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
