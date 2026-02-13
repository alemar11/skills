#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: issues_suggest_labels.sh --repo <owner/repo> --title <text> [--body <text>] [--max-suggestions N] [--min-score <float>] [--json]
  --repo            required: owner/repo
  --title           required
  --body            optional
  --max-suggestions maximum suggestions to return (default: 5)
  --min-score       minimum score to keep (default: 0.20)
  --json            emit JSON output
USAGE
}

REPO=""
TITLE=""
BODY=""
MAX_SUGGESTIONS=5
MIN_SCORE=0.2
OUTPUT_JSON=0

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

python3 - "$REPO" "$TITLE" "$BODY" "$MAX_SUGGESTIONS" "$MIN_SCORE" "$OUTPUT_JSON" <<'PY'
import json
import re
import sys

repo = sys.argv[1]
title = (sys.argv[2] or "").strip()
body = (sys.argv[3] or "").strip()
max_suggestions = int(sys.argv[4])
min_score = float(sys.argv[5])
output_json = bool(int(sys.argv[6]))

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

if output_json:
    print(
        json.dumps(
            {
                "repo": repo,
                "count": len(results),
                "suggestions": results,
                "filters": {
                    "max_suggestions": max_suggestions,
                    "min_score": min_score,
                },
            },
            indent=2,
        )
    )
    raise SystemExit(0)

if not results:
    print(f"No labels passed min score {min_score:.2f}.")
    raise SystemExit(0)

print(f"Found {len(results)} suggestion(s):")
for suggestion in results:
    print(
        f"- {suggestion['name']}: "
        f"{suggestion['score']:.2f} [{suggestion['confidence']}] ({suggestion['source']})"
    )
    print(f"  {suggestion['reason']}")
PY
