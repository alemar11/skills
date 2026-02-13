#!/usr/bin/env bash
set -euo pipefail

SEARCH_URL="${PG_DOCS_SEARCH_URL:-https://www.postgresql.org/search/}"
DEFAULT_LIMIT=10
MAX_LIMIT=20
MAX_TIME="${PG_DOCS_SEARCH_MAX_TIME:-30}"

usage() {
  cat <<'EOF'
Usage: search_postgres_docs.sh "<query>" [limit]

Search official PostgreSQL documentation pages at runtime.
This helper is standalone and should be used only when the user explicitly asks
for official PostgreSQL docs lookup/verification.

Arguments:
  query   Required search string.
  limit   Optional max number of results (default: 10, max: 20).

Exit codes:
  0  Success (including no docs/current matches)
  1  Usage or dependency error
  2  Runtime lookup/parsing error

Examples:
  ./scripts/search_postgres_docs.sh "vacuum autovacuum" 5
  ./scripts/search_postgres_docs.sh "row level security policies"
EOF
}

require_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Error: required command not found: $cmd" >&2
    exit 1
  fi
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -lt 1 || $# -gt 2 ]]; then
  usage >&2
  exit 1
fi

query="$1"
limit="${2:-$DEFAULT_LIMIT}"

if [[ -z "$query" ]]; then
  echo "Error: query must not be empty." >&2
  usage >&2
  exit 1
fi

if ! [[ "$limit" =~ ^[0-9]+$ ]]; then
  echo "Error: limit must be a positive integer." >&2
  usage >&2
  exit 1
fi

if (( limit < 1 || limit > MAX_LIMIT )); then
  echo "Error: limit must be between 1 and ${MAX_LIMIT}." >&2
  usage >&2
  exit 1
fi

require_cmd curl
require_cmd python3

tmp_html="$(mktemp)"
trap 'rm -f "$tmp_html"' EXIT

if ! curl \
  --fail \
  --silent \
  --show-error \
  --location \
  --retry 3 \
  --retry-delay 2 \
  --retry-connrefused \
  --max-time "$MAX_TIME" \
  --get \
  --data-urlencode "q=$query" \
  "$SEARCH_URL" \
  -o "$tmp_html"; then
  echo "Error: failed to query official PostgreSQL search endpoint: $SEARCH_URL" >&2
  exit 2
fi

if ! python3 - "$tmp_html" "$query" "$limit" <<'PY'; then
import html
import pathlib
import re
import sys

html_path, query, limit_raw = sys.argv[1:4]
limit = int(limit_raw)

try:
    raw = pathlib.Path(html_path).read_text(encoding="utf-8", errors="ignore")
except Exception as exc:
    raise SystemExit(f"Error: unable to read search response: {exc}")

if "<title>PostgreSQL: Search results" not in raw:
    raise SystemExit(
        "Error: unexpected search response from postgresql.org; cannot parse results."
    )

pattern = re.compile(
    r"\n\s*\d+\.\s*<a href=\"([^\"]+)\">(.+?)</a>\s*\[[^\]]+\]<br/>\s*<div>(.*?)</div>",
    re.S,
)
matches = pattern.findall(raw)
if not matches:
    if "returned no hits" in raw.lower():
        print(
            f'No matches found in official PostgreSQL current docs for query: "{query}".'
        )
        sys.exit(0)
    raise SystemExit("Error: could not parse search result entries from response.")

results = []
seen = set()

for url, title, snippet in matches:
    if not url.startswith("https://www.postgresql.org/docs/current/"):
        continue
    if url in seen:
        continue
    seen.add(url)

    clean_title = html.unescape(re.sub(r"<[^>]+>", "", title))
    clean_title = " ".join(clean_title.split())

    clean_snippet = html.unescape(re.sub(r"<[^>]+>", "", snippet))
    clean_snippet = " ".join(clean_snippet.split())
    if not clean_snippet:
        clean_snippet = "(no snippet)"

    results.append((clean_title, url, clean_snippet))
    if len(results) >= limit:
        break

if not results:
    print(
        f'No matches found in official PostgreSQL current docs for query: "{query}".'
    )
    sys.exit(0)

for idx, (title, url, snippet) in enumerate(results, start=1):
    print(f"{idx}. {title}")
    print(f"   {url}")
    print(f"   Snippet: {snippet}")
PY
  echo "Error: failed to parse PostgreSQL documentation search results." >&2
  exit 2
fi
