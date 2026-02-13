#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: issues_suggest_labels.sh --repo <owner/repo> --title <text> [--body <text>] [--max-suggestions N] [--min-score <float>] [--allow-new-label] [--new-label-color <rrggbb>] [--new-label-description <text>] [--json]
  --repo            required: owner/repo
  --title           required
  --body            optional
  --max-suggestions maximum suggestions to return (default: 5)
  --min-score       minimum score to keep (default: 0.20)
  --allow-new-label if set, propose and create reusable repo-level fallback labels
  --new-label-color default color when creating fallback labels (optional, hex without #)
  --new-label-description default description when creating fallback labels (optional)
  --json            emit JSON output
USAGE
}

REPO=""
TITLE=""
BODY=""
MAX_SUGGESTIONS=5
MIN_SCORE=0.2
OUTPUT_JSON=0
ALLOW_NEW_LABELS=0
NEW_LABEL_COLOR=""
NEW_LABEL_DESCRIPTION=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      REPO="${2:-}"
      if [[ -z "$REPO" ]]; then
        echo "Missing value for --repo" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --title)
      TITLE="${2:-}"
      if [[ -z "$TITLE" ]]; then
        echo "Missing value for --title" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --body)
      BODY="${2:-}"
      if [[ -z "$BODY" ]]; then
        echo "Missing value for --body" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --max-suggestions)
      MAX_SUGGESTIONS="${2:-}"
      if [[ -z "$MAX_SUGGESTIONS" || ! "$MAX_SUGGESTIONS" =~ ^[1-9][0-9]*$ ]]; then
        echo "Invalid --max-suggestions '$MAX_SUGGESTIONS'. It must be a positive integer." >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --min-score)
      MIN_SCORE="${2:-}"
      if [[ -z "$MIN_SCORE" ]] || ! [[ "$MIN_SCORE" =~ ^0(\.[0-9]+)?$|^1(\.0+)?$ ]]; then
        echo "Invalid --min-score '$MIN_SCORE'. Use 0..1." >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --allow-new-label)
      ALLOW_NEW_LABELS=1
      shift
      ;;
    --new-label-color)
      NEW_LABEL_COLOR="${2:-}"
      if [[ -z "$NEW_LABEL_COLOR" ]] || ! [[ "$NEW_LABEL_COLOR" =~ ^[a-fA-F0-9]{6}$ ]]; then
        echo "Invalid --new-label-color '$NEW_LABEL_COLOR'. Use 6-char hex (for example, a2eeef)." >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --new-label-description)
      NEW_LABEL_DESCRIPTION="${2:-}"
      shift 2
      ;;
    --json)
      OUTPUT_JSON=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 64
      ;;
  esac
done

if [[ -z "$REPO" ]]; then
  echo "Missing required --repo" >&2
  usage >&2
  exit 64
fi
if [[ -z "$TITLE" ]]; then
  echo "Missing required --title" >&2
  usage >&2
  exit 64
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/github_lib.sh"
github_require_repo_reference "$REPO"
TARGET_REPO="$REPO"

if ! LABELS_JSON="$(gh label list --repo "$TARGET_REPO" --json name,description 2>/tmp/issues-suggest-labels.err)"; then
  ERR="$(cat /tmp/issues-suggest-labels.err)"
  echo "Error: unable to list labels for $TARGET_REPO." >&2
  if [[ -n "$ERR" ]]; then
    echo "$ERR" >&2
  fi
  exit 1
fi

python3 - "$REPO" "$TITLE" "$BODY" "$MAX_SUGGESTIONS" "$MIN_SCORE" "$OUTPUT_JSON" "$ALLOW_NEW_LABELS" "$NEW_LABEL_COLOR" "$NEW_LABEL_DESCRIPTION" <<'PY'
import json
import re
import sys
import subprocess

repo = sys.argv[1]
title = (sys.argv[2] or "").strip()
body = (sys.argv[3] or "").strip()
max_suggestions = int(sys.argv[4])
min_score = float(sys.argv[5])
output_json = bool(int(sys.argv[6]))
allow_new_labels = bool(int(sys.argv[7]))
new_label_color = (sys.argv[8] or "").strip()
new_label_description = (sys.argv[9] or "").strip()

try:
    labels_payload = sys.stdin.read().strip()
    labels = json.loads(labels_payload)
except json.JSONDecodeError:
    print("Error: failed to parse labels JSON from gh.", file=sys.stderr)
    raise SystemExit(1)

if not isinstance(labels, list):
    print("Error: unexpected labels JSON shape.", file=sys.stderr)
    raise SystemExit(1)

token_re = re.compile(r"[a-z0-9]+")
ALIASES = {
    "docs": ["docs", "documentation", "doc", "readme"],
    "documentation": ["documentation", "docs", "doc", "reference"],
    "bug": ["bug", "error", "defect", "regression"],
    "enhancement": ["enhancement", "feature", "improve", "improvement"],
    "tests": ["test", "tests", "ci", "coverage", "pytest", "unittest", "unit"],
    "test": ["test", "tests", "ci", "coverage", "unit"],
    "build": ["build", "builds", "make", "package", "compile"],
    "ci": ["ci", "pipeline", "workflow", "build"],
    "chore": ["chore", "maintenance", "housekeeping", "cleanup"],
}

REUSABLE_FALLBACK_LABELS = {
    "bug": [
        "bug",
        "bugs",
        "error",
        "crash",
        "fault",
        "issue",
        "fail",
        "failure",
    ],
    "enhancement": [
        "enhancement",
        "enhance",
        "feature",
        "improve",
        "improvement",
    ],
    "documentation": [
        "documentation",
        "docs",
        "readme",
        "typo",
        "doc",
        "docstring",
    ],
    "tests": [
        "test",
        "tests",
        "pytest",
        "unittest",
        "coverage",
        "ci",
        "unit",
    ],
    "build": [
        "build",
        "builds",
        "pipeline",
        "compile",
        "package",
        "make",
    ],
    "dependencies": [
        "dependency",
        "dependencies",
        "upgrade",
        "version",
        "package",
        "npm",
        "pip",
    ],
    "chore": [
        "chore",
        "cleanup",
        "housekeeping",
        "maintenance",
    ],
}

FALLBACK_LABEL_COLORS = {
    "bug": "d73a4a",
    "enhancement": "a2eeef",
    "documentation": "0075ca",
    "tests": "fbca04",
    "build": "0052cc",
    "dependencies": "5319e7",
    "chore": "bfd4f2",
}

def tokens(text: str) -> list[str]:
    return token_re.findall((text or "").lower())


def overlap_ratio(base: list[str], other: list[str]) -> float:
    base_set = set(base)
    if not base_set:
        return 0.0
    other_set = set(other)
    return len(base_set & other_set) / len(base_set)


def exact_name_match(label_name: str, source_tokens: list[str], match_weight: float) -> tuple[float, bool]:
    label_tokens = tokens(label_name)
    if not label_tokens:
        return 0.0, False
    has_match = all(token in source_tokens for token in label_tokens)
    return (match_weight, has_match) if has_match else (0.0, False)


title_tokens = tokens(title)
body_tokens = tokens(body)
combined_tokens = list(dict.fromkeys(title_tokens + body_tokens))

results = []
for item in labels:
    name = (item.get("name") or "").strip()
    if not name:
        continue

    description = (item.get("description") or "").strip()
    norm_name = name.lower()

    title_match, from_title = exact_name_match(norm_name, title_tokens, 0.60)
    body_match, from_body = exact_name_match(norm_name, body_tokens, 0.35)
    desc_overlap = overlap_ratio(tokens(description), combined_tokens)
    desc_score = min(0.20, desc_overlap * 0.20)

    alias_score = 0.0
    alias_hits = []
    for alias in ALIASES.get(norm_name, []):
        if alias in title_tokens or alias in body_tokens:
            alias_hits.append(alias)
            alias_score = min(0.25, alias_score + 0.08)

    score = min(1.0, title_match + body_match + desc_score + alias_score)
    if score < min_score:
        continue

    source = []
    reasons = []
    if from_title:
        source.append("title")
        reasons.append("label name token match in title")
    if from_body:
        source.append("body")
        reasons.append("label name token match in body")
    if desc_score > 0:
        source.append("description")
        reasons.append(f"description overlap {desc_overlap:.0%}")
    if alias_hits:
        source.append("alias")
        reasons.append("alias match: " + ", ".join(sorted(set(alias_hits))))

    if score >= 0.75:
        confidence = "high"
    elif score >= 0.45:
        confidence = "medium"
    else:
        confidence = "low"

    results.append(
        {
            "name": name,
            "score": round(score, 4),
            "reason": "; ".join(reasons) or "context token overlap",
            "source": source[0] if len(source) == 1 else "combined",
            "confidence": confidence,
        }
    )

results.sort(key=lambda item: (-item["score"], item["name"].lower()))
results = results[:max_suggestions]

fallback_new_labels = []
existing_names = {item.get("name", "").strip().lower() for item in labels if item.get("name")}
all_tokens = set(combined_tokens)

def create_label(label_name: str, color: str, description: str) -> tuple[bool, str]:
    cmd = [
        "gh",
        "label",
        "create",
        label_name,
        "--repo",
        repo,
        "--color",
        color,
    ]
    if description:
        cmd.extend(["--description", description])
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        reason = (proc.stderr or proc.stdout or "").strip()
        return False, reason or "gh label create failed"
    return True, ""


if not results:
    for label_name, label_tokens in REUSABLE_FALLBACK_LABELS.items():
        normalized_label = label_name.lower()
        if normalized_label in existing_names:
            continue
        alias_hits = [token for token in label_tokens if token in all_tokens]
        if not alias_hits:
            continue

        if any(char.isspace() for char in normalized_label):
            continue

        score = min(
            1.0,
            0.50
            + min(0.10 * len(alias_hits), 0.30)
            + min(0.05 * len(label_name), 0.10),
        )
        if score < max(min_score, 0.30):
            continue

        if score >= 0.75:
            confidence = "high"
        elif score >= 0.45:
            confidence = "medium"
        else:
            confidence = "low"

        candidate = {
            "name": label_name,
            "score": round(score, 4),
            "reason": "reusable fallback keyword match: " + ", ".join(sorted(set(alias_hits))),
            "source": "reusable_fallback",
            "confidence": confidence,
            "created": False,
            "creation_error": "",
        }

        if allow_new_labels:
            effective_color = (
                new_label_color
                if new_label_color
                else FALLBACK_LABEL_COLORS.get(normalized_label, "a2eeef")
            )
            created, reason = create_label(
                label_name,
                effective_color,
                new_label_description
                or f"Reusable label for {normalized_label}-related issues.",
            )
            candidate["created"] = created
            candidate["creation_error"] = reason
            candidate["source"] = "created_label" if created else "fallback_label_create_failed"

        fallback_new_labels.append(candidate)

fallback_new_labels.sort(key=lambda item: (-item["score"], item["name"].lower()))
fallback_new_labels = fallback_new_labels[:max_suggestions]

suggestion_source = "existing_labels"
effective_suggestions = results
if not results:
    effective_suggestions = fallback_new_labels
    if fallback_new_labels:
        suggestion_source = "new_labels"

if output_json:
    print(
        json.dumps(
            {
                "repo": repo,
                "count": len(effective_suggestions),
                "suggestions": effective_suggestions,
                "suggestion_source": suggestion_source,
                "existing_suggestions": results,
                "fallback_suggestions": fallback_new_labels,
                "filters": {
                    "max_suggestions": max_suggestions,
                    "min_score": min_score,
                    "allow_new_labels": allow_new_labels,
                },
            },
            indent=2,
        )
    )
    raise SystemExit(0)

if not effective_suggestions:
    print(f"No labels passed min score {min_score:.2f} and no reusable fallback matches were found.")
    raise SystemExit(0)

if suggestion_source == "existing_labels":
    print(f"Found {len(effective_suggestions)} suggestion(s) from existing labels:")
else:
    print(f"No strong existing match; found {len(effective_suggestions)} reusable fallback suggestion(s):")

for suggestion in effective_suggestions:
    created_note = ""
    if suggestion["source"] in {"created_label", "fallback_label_create_failed"}:
        created_note = " [created]" if suggestion["source"] == "created_label" else " [create failed]"
    print(
        f"- {suggestion['name']}: "
        f"{suggestion['score']:.2f} [{suggestion['confidence']}] ({suggestion['source']}){created_note}"
    )
    print(f"  {suggestion['reason']}")
    if suggestion.get("creation_error"):
        print(f"  note: {suggestion['creation_error']}")
PY
