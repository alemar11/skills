#!/usr/bin/env python3
"""Benchmark local skills against upstream skill repositories.

Fetches upstream skills (default: openai/skills + anthropics/skills), analyzes
SKILL.md structure, audits local skills (including hidden .agents paths), and
writes actionable proposal artifacts.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

DEFAULT_REPOS = ["openai/skills", "anthropics/skills"]
DEFAULT_OUTPUT_DIR = ".agents/skills/tools/artifacts/openai-skill-benchmark"


@dataclass
class SkillMetrics:
    has_frontmatter: bool
    has_required_frontmatter: bool
    frontmatter_name: str
    frontmatter_description: str
    headings: list[str]
    line_count: int
    word_count: int
    has_workflow_section: bool
    has_trigger_section: bool
    has_guardrails_section: bool


def detect_repo_root(script_path: Path) -> Path:
    script_dir = script_path.resolve().parent
    try:
        output = subprocess.check_output(
            ["git", "-C", str(script_dir), "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        if output:
            return Path(output)
    except Exception:
        pass

    return script_dir.parents[3]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark local skills against upstream repositories")
    parser.add_argument("--ref", default="main", help="Git ref to analyze (default: main)")
    parser.add_argument(
        "--scope",
        choices=["both", "system", "curated"],
        default="both",
        help="Scope for repos using .system/.curated layout (default: both)",
    )
    parser.add_argument(
        "--repo",
        action="append",
        default=None,
        help="Upstream repo in owner/repo format; repeatable. Default: openai/skills + anthropics/skills",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory for artifacts (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json", "both"],
        default="both",
        help="Console output format (artifacts are always written)",
    )
    return parser.parse_args()


def normalize_repo_args(raw_repos: list[str] | None) -> list[str]:
    if not raw_repos:
        return DEFAULT_REPOS.copy()

    repos: list[str] = []
    for raw in raw_repos:
        for item in raw.split(","):
            repo = item.strip()
            if repo and repo not in repos:
                repos.append(repo)

    return repos or DEFAULT_REPOS.copy()


def api_get_json(url: str, token: str | None) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "skills-benchmark-agent",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def api_get_text(url: str, token: str | None) -> str:
    headers = {"User-Agent": "skills-benchmark-agent"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def github_recursive_tree(repo: str, ref: str, token: str | None) -> list[dict[str, Any]]:
    ref_encoded = urllib.parse.quote(ref, safe="")
    url = f"https://api.github.com/repos/{repo}/git/trees/{ref_encoded}?recursive=1"
    payload = api_get_json(url, token)
    if isinstance(payload, dict):
        tree = payload.get("tree", [])
        if isinstance(tree, list):
            return tree
    return []


def strip_quotes(value: str) -> str:
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def normalize_heading(raw: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", " ", raw.lower()).strip()
    return re.sub(r"\s+", " ", normalized)


def parse_skill_markdown(content: str) -> SkillMetrics:
    has_frontmatter = False
    frontmatter: dict[str, str] = {}
    headings: list[str] = []

    frontmatter_match = re.match(r"\A---\n(.*?)\n---\n", content, flags=re.DOTALL)
    if frontmatter_match:
        has_frontmatter = True
        fm_text = frontmatter_match.group(1)
        for line in fm_text.splitlines():
            if not line.strip() or line.startswith(" ") or line.startswith("\t"):
                continue
            m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
            if m:
                frontmatter[m.group(1)] = strip_quotes(m.group(2))

    for line in content.splitlines():
        m = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if m:
            headings.append(m.group(2).strip())

    normalized_headings = [normalize_heading(h) for h in headings if h.strip()]

    def has_section(candidates: tuple[str, ...]) -> bool:
        return any(candidate in heading for heading in normalized_headings for candidate in candidates)

    words = re.findall(r"[A-Za-z0-9_]+", content)
    name = frontmatter.get("name", "").strip()
    description = frontmatter.get("description", "").strip()

    return SkillMetrics(
        has_frontmatter=has_frontmatter,
        has_required_frontmatter=bool(name and description),
        frontmatter_name=name,
        frontmatter_description=description,
        headings=headings,
        line_count=len(content.splitlines()),
        word_count=len(words),
        has_workflow_section=has_section(("workflow", "quick flow", "process", "steps", "execution flow")),
        has_trigger_section=has_section(("trigger", "when to use", "activation")),
        has_guardrails_section=has_section(("guardrail", "safety", "rules")),
    )


def extract_upstream_skill_roots(tree: list[dict[str, Any]], scope: str) -> list[tuple[str, str]]:
    tree_paths = {entry.get("path", ""): entry.get("type", "") for entry in tree}
    has_openai_layout = any(path.startswith("skills/.system/") for path in tree_paths) or any(
        path.startswith("skills/.curated/") for path in tree_paths
    )

    roots: list[tuple[str, str]] = []
    if has_openai_layout:
        allow_system = scope in {"both", "system"}
        allow_curated = scope in {"both", "curated"}
        pattern = re.compile(r"^skills/(\.[^/]+)/([^/]+)$")
        for path, entry_type in tree_paths.items():
            if entry_type != "tree":
                continue
            m = pattern.match(path)
            if not m:
                continue
            bucket = m.group(1)
            if bucket == ".system" and not allow_system:
                continue
            if bucket == ".curated" and not allow_curated:
                continue
            roots.append((bucket.lstrip("."), path))
    else:
        pattern = re.compile(r"^skills/([^/]+)$")
        for path, entry_type in tree_paths.items():
            if entry_type != "tree":
                continue
            if pattern.match(path):
                roots.append(("all", path))

    roots.sort(key=lambda item: item[1])
    return roots


def collect_upstream_inventory(
    repos: list[str], ref: str, scope: str, token: str | None
) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []

    for repo in repos:
        try:
            tree = github_recursive_tree(repo, ref, token)
        except urllib.error.HTTPError as exc:
            errors.append(f"{repo}: failed to fetch repository tree ({exc.code})")
            continue
        except Exception as exc:
            errors.append(f"{repo}: failed to fetch repository tree ({exc})")
            continue

        if not tree:
            errors.append(f"{repo}: repository tree is empty or unavailable")
            continue

        path_to_type = {entry.get("path", ""): entry.get("type", "") for entry in tree}
        roots = extract_upstream_skill_roots(tree, scope)
        if not roots:
            errors.append(f"{repo}: no skill roots detected for scope `{scope}`")
            continue

        for scope_bucket, skill_root in roots:
            children: set[str] = set()
            prefix = f"{skill_root}/"
            for path in path_to_type:
                if not path.startswith(prefix):
                    continue
                remainder = path[len(prefix) :]
                first = remainder.split("/", 1)[0]
                if first:
                    children.add(first)

            skill_md_rel = f"{skill_root}/SKILL.md"
            has_skill_md = path_to_type.get(skill_md_rel) == "blob"
            metrics: SkillMetrics | None = None
            if has_skill_md:
                raw_path = urllib.parse.quote(skill_md_rel, safe="/")
                raw_ref = urllib.parse.quote(ref, safe="")
                raw_url = f"https://raw.githubusercontent.com/{repo}/{raw_ref}/{raw_path}"
                try:
                    metrics = parse_skill_markdown(api_get_text(raw_url, token))
                except urllib.error.HTTPError as exc:
                    errors.append(f"{repo}:{skill_md_rel}: failed to fetch SKILL.md ({exc.code})")
                except Exception as exc:
                    errors.append(f"{repo}:{skill_md_rel}: failed to fetch SKILL.md ({exc})")

            records.append(
                {
                    "baseline_repo": repo,
                    "scope_bucket": scope_bucket,
                    "skill_name": Path(skill_root).name,
                    "skill_path": skill_root,
                    "has_skill_md": has_skill_md,
                    "has_agents_dir": "agents" in children,
                    "has_references_dir": "references" in children,
                    "has_scripts_dir": "scripts" in children,
                    "has_assets_dir": "assets" in children,
                    "skill_md": asdict(metrics) if metrics else None,
                }
            )

    return records, errors


def collect_local_inventory(repo_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    for current_root, dirnames, filenames in os.walk(repo_root, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in {".git", ".cache", "__pycache__"}]
        if "SKILL.md" not in filenames:
            continue

        skill_root = Path(current_root)
        skill_md_path = skill_root / "SKILL.md"
        rel_skill_md = skill_md_path.relative_to(repo_root).as_posix()
        rel_root = skill_root.relative_to(repo_root).as_posix()
        parts = skill_md_path.relative_to(repo_root).parts

        visibility = "other"
        if len(parts) == 2 and parts[1] == "SKILL.md" and not parts[0].startswith("."):
            visibility = "top-level"
        elif len(parts) >= 4 and parts[0] == ".agents" and parts[1] == "skills":
            visibility = "project"

        metrics = parse_skill_markdown(skill_md_path.read_text(encoding="utf-8"))

        records.append(
            {
                "skill_root": rel_root,
                "skill_md_path": rel_skill_md,
                "visibility": visibility,
                "has_agents_openai_yaml": (skill_root / "agents" / "openai.yaml").exists(),
                "has_references_dir": (skill_root / "references").is_dir(),
                "has_scripts_dir": (skill_root / "scripts").is_dir(),
                "has_assets_dir": (skill_root / "assets").is_dir(),
                "skill_md": asdict(metrics),
            }
        )

    records.sort(key=lambda item: item["skill_md_path"])
    return records


def summarize_upstream(records: list[dict[str, Any]]) -> dict[str, Any]:
    skills_with_md = [r for r in records if r.get("skill_md")]
    summary: dict[str, Any] = {
        "total_skills": len(records),
        "skills_with_skill_md": len(skills_with_md),
        "repos": sorted({r["baseline_repo"] for r in records}),
    }

    if not skills_with_md:
        summary.update(
            {
                "section_frequency": {},
                "line_count_median": None,
                "line_count_p75": None,
                "agents_dir_ratio": 0.0,
                "workflow_section_ratio": 0.0,
                "trigger_section_ratio": 0.0,
            }
        )
        return summary

    section_counter: Counter[str] = Counter()
    line_counts: list[int] = []
    workflow_count = 0
    trigger_count = 0
    agents_count = 0

    for skill in skills_with_md:
        metrics = skill["skill_md"]
        line_counts.append(metrics["line_count"])
        if metrics["has_workflow_section"]:
            workflow_count += 1
        if metrics["has_trigger_section"]:
            trigger_count += 1
        if skill["has_agents_dir"]:
            agents_count += 1

        section_counter.update({normalize_heading(h) for h in metrics["headings"] if h.strip()})

    def ratio(value: int, total: int) -> float:
        return round((value / total) if total else 0.0, 4)

    sorted_lines = sorted(line_counts)
    p75_index = min(len(sorted_lines) - 1, int(len(sorted_lines) * 0.75))

    summary.update(
        {
            "section_frequency": dict(section_counter.most_common(20)),
            "line_count_median": int(statistics.median(line_counts)),
            "line_count_p75": int(sorted_lines[p75_index]),
            "agents_dir_ratio": ratio(agents_count, len(skills_with_md)),
            "workflow_section_ratio": ratio(workflow_count, len(skills_with_md)),
            "trigger_section_ratio": ratio(trigger_count, len(skills_with_md)),
        }
    )
    return summary


def scan_command_coverage(repo_root: Path) -> bool:
    """True when legacy rg globs likely miss hidden project skills."""
    targets = [
        repo_root / ".agents" / "skills" / "tools" / "references" / "metadata-sync.md",
        repo_root / ".agents" / "skills" / "tools" / "references" / "doc-consistency.md",
        repo_root / ".agents" / "skills" / "tools" / "references" / "release-checklist.md",
    ]
    legacy = "rg --files -g '*/SKILL.md'"
    for target in targets:
        if target.exists() and legacy in target.read_text(encoding="utf-8"):
            return True
    return False


def build_proposals(
    local_inventory: list[dict[str, Any]], upstream_summary: dict[str, Any], repo_root: Path
) -> list[dict[str, Any]]:
    proposals: list[dict[str, Any]] = []
    pid = 1

    workflow_ratio = upstream_summary.get("workflow_section_ratio", 0.0)
    trigger_ratio = upstream_summary.get("trigger_section_ratio", 0.0)
    agents_ratio = upstream_summary.get("agents_dir_ratio", 0.0)

    for record in local_inventory:
        metrics = record["skill_md"]
        target = record["skill_md_path"]
        skill_root = record["skill_root"]

        def add(severity: str, title: str, recommendation: str, rationale: str) -> None:
            nonlocal pid
            proposals.append(
                {
                    "id": f"P{pid:03d}",
                    "severity": severity,
                    "title": title,
                    "target": target,
                    "skill_root": skill_root,
                    "recommendation": recommendation,
                    "rationale": rationale,
                }
            )
            pid += 1

        if not metrics["has_frontmatter"]:
            add(
                "high",
                "Missing YAML frontmatter",
                "Add YAML frontmatter with `name` and `description` at the top of SKILL.md.",
                "Upstream skills consistently rely on frontmatter-driven trigger metadata.",
            )
            continue

        if not metrics["has_required_frontmatter"]:
            add(
                "high",
                "Missing required frontmatter keys",
                "Ensure both `name` and `description` are present and non-empty in frontmatter.",
                "`name` and `description` are required fundamentals for skill triggering.",
            )

        if not metrics["has_workflow_section"] and workflow_ratio >= 0.4:
            add(
                "medium",
                "Workflow guidance can be clearer",
                "Add a dedicated `## Workflow` (or equivalent step-by-step section).",
                f"Workflow-like sections appear in {workflow_ratio:.0%} of upstream sampled skills.",
            )

        if not metrics["has_trigger_section"] and trigger_ratio >= 0.3:
            add(
                "medium",
                "Trigger guidance may be underspecified",
                "Add a `## Trigger rules` or `## When to use` section clarifying activation criteria.",
                f"Trigger-oriented sections appear in {trigger_ratio:.0%} of upstream sampled skills.",
            )

        if metrics["line_count"] > 500 and not record["has_references_dir"]:
            add(
                "medium",
                "Large SKILL.md without references split",
                "Move detailed content into `references/` and keep SKILL.md focused on routing/workflow.",
                "Progressive disclosure improves maintainability for long skills.",
            )

        if metrics["line_count"] > 700:
            add(
                "low",
                "Very long SKILL.md",
                "Review whether advanced variants/examples can be moved to references.",
                "Large instruction surfaces increase maintenance cost.",
            )

        if not record["has_agents_openai_yaml"] and agents_ratio >= 0.6:
            add(
                "low",
                "Missing agents/openai.yaml metadata",
                "Consider adding `agents/openai.yaml` to keep UI metadata explicit and synced.",
                f"Skill metadata directories appear in {agents_ratio:.0%} of upstream sampled skills.",
            )

    if scan_command_coverage(repo_root):
        proposals.append(
            {
                "id": f"P{pid:03d}",
                "severity": "medium",
                "title": "Hidden project skills may be skipped by audit commands",
                "target": ".agents/skills/tools/references/*.md",
                "skill_root": ".agents/skills/tools",
                "recommendation": "Use `find`-based skill discovery that includes hidden `.agents/skills/*` paths.",
                "rationale": "Glob-based `rg` patterns can omit hidden project skills and reduce audit coverage.",
            }
        )

    return proposals


def compare_severity_key(proposal: dict[str, Any]) -> tuple[int, str]:
    rank = {"high": 0, "medium": 1, "low": 2}
    return rank.get(proposal["severity"], 3), proposal["id"]


def build_markdown_report(
    upstream_inventory: list[dict[str, Any]],
    local_inventory: list[dict[str, Any]],
    upstream_summary: dict[str, Any],
    proposals: list[dict[str, Any]],
    errors: list[str],
    configured_repos: list[str],
) -> str:
    result = "PASS"
    if not upstream_inventory:
        result = "FAIL"
    elif not proposals:
        result = "PASS (NOOP)"

    lines: list[str] = [
        "# Skill Benchmark Report",
        "",
        f"- Result: `{result}`",
        f"- Upstream skills analyzed: `{upstream_summary.get('skills_with_skill_md', 0)}/{upstream_summary.get('total_skills', 0)}`",
        f"- Local skills analyzed: `{len(local_inventory)}`",
        f"- Upstream repos: `{', '.join(configured_repos)}`",
        "",
        "## Baseline Patterns",
        f"- Workflow section ratio (upstream): `{upstream_summary.get('workflow_section_ratio', 0.0):.0%}`",
        f"- Trigger section ratio (upstream): `{upstream_summary.get('trigger_section_ratio', 0.0):.0%}`",
        f"- `agents/` dir ratio (upstream): `{upstream_summary.get('agents_dir_ratio', 0.0):.0%}`",
        f"- Median SKILL.md length (upstream): `{upstream_summary.get('line_count_median')}` lines",
        "",
    ]

    if errors:
        lines.append("## Fetch/Analysis Notes")
        lines.extend([f"- WARN: {err}" for err in errors])
        lines.append("")

    lines.append("## Findings")
    if result == "FAIL":
        lines.append("- Upstream baseline fetch failed. Retry later or provide `GH_TOKEN`/`GITHUB_TOKEN` to increase API limits.")
    elif not proposals:
        lines.append("- No meaningful structure updates were identified. `PASS (NOOP)`.")
    else:
        for proposal in sorted(proposals, key=compare_severity_key):
            lines.append(f"- [{proposal['severity'].upper()}] {proposal['title']} -> `{proposal['target']}`")
            lines.append(f"  - Recommendation: {proposal['recommendation']}")
            lines.append(f"  - Rationale: {proposal['rationale']}")
    lines.append("")

    lines.append("## Top Upstream Sections")
    section_frequency = upstream_summary.get("section_frequency", {})
    if not section_frequency:
        lines.append("- No section data available.")
    else:
        for section, count in list(section_frequency.items())[:10]:
            lines.append(f"- `{section}`: {count}")

    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    script_path = Path(__file__)
    repo_root = detect_repo_root(script_path)
    output_dir = (repo_root / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    repos = normalize_repo_args(args.repo)

    upstream_inventory, upstream_errors = collect_upstream_inventory(
        repos=repos,
        ref=args.ref,
        scope=args.scope,
        token=token,
    )
    local_inventory = collect_local_inventory(repo_root)
    upstream_summary = summarize_upstream(upstream_inventory)
    proposals = build_proposals(local_inventory, upstream_summary, repo_root)

    result = "PASS"
    if not upstream_inventory:
        result = "FAIL"
    elif not proposals:
        result = "PASS (NOOP)"

    payload = {
        "result": result,
        "config": {
            "repos": repos,
            "ref": args.ref,
            "scope": args.scope,
            "output_dir": str(output_dir.relative_to(repo_root)),
        },
        "summary": {
            "upstream": upstream_summary,
            "local_skill_count": len(local_inventory),
            "proposal_count": len(proposals),
            "errors": upstream_errors,
        },
    }

    (output_dir / "upstream_inventory.json").write_text(
        json.dumps(upstream_inventory, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (output_dir / "local_inventory.json").write_text(
        json.dumps(local_inventory, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (output_dir / "proposals.json").write_text(
        json.dumps({"result": result, "proposals": proposals}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    report = build_markdown_report(
        upstream_inventory=upstream_inventory,
        local_inventory=local_inventory,
        upstream_summary=upstream_summary,
        proposals=proposals,
        errors=upstream_errors,
        configured_repos=repos,
    )
    (output_dir / "comparison_report.md").write_text(report, encoding="utf-8")

    if args.format in {"json", "both"}:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    if args.format in {"markdown", "both"}:
        print("\n# Comparison report")
        print(report)

    if result == "FAIL":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
