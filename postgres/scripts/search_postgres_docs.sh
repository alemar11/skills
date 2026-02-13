#!/usr/bin/env bash
set -euo pipefail

SEARCH_URL="${PG_DOCS_SEARCH_URL:-https://www.postgresql.org/search/}"
CURRENT_DOCS_SCOPE="/docs/current/"
DEFAULT_LIMIT=10
MAX_LIMIT=20
MAX_TIME="${PG_DOCS_SEARCH_MAX_TIME:-30}"

usage() {
  cat <<'EOF'
Usage: search_postgres_docs.sh "<query>" [limit]

Search official PostgreSQL documentation pages at runtime.
This helper is standalone and should be used only when the user explicitly asks
for official PostgreSQL docs lookup/verification.
Results are restricted to PostgreSQL current docs (`/docs/current/`) only.

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
  --compressed \
  --max-time "$MAX_TIME" \
  --get \
  --data-urlencode "q=$query" \
  --data-urlencode "u=$CURRENT_DOCS_SCOPE" \
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

if not raw:
    raise SystemExit("Error: empty response from postgresql.org search endpoint.")

if "<title>postgresql: search results" not in raw.lower():
    raise SystemExit(
        "Error: unexpected search response from postgresql.org; cannot parse results."
    )

if "returned no hits" in raw.lower():
    print(
        f'No matches found in official PostgreSQL current docs for query: "{query}".'
    )
    sys.exit(0)

# Parse only the content area when possible to avoid unrelated links in nav/footer.
content = raw
parts = re.split(r"<!--\s*docbot goes here\s*-->", raw, maxsplit=1, flags=re.I)
if len(parts) == 2:
    content = parts[1]
content = re.split(
    r"</div>\s*<!--\s*pgContentWrap\s*-->", content, maxsplit=1, flags=re.I
)[0]

# Main parser: title link + score + snippet block for docs/current hits.
pattern = re.compile(
    r'(?:^|\n)\s*\d+\.\s*<a href="(https://www\.postgresql\.org/docs/current/[^"]+)">(.+?)</a>\s*\[[^\]]+\]\s*<br\s*/?>\s*<div>(.*?)</div>',
    re.I | re.S,
)
matches = pattern.findall(content)

# Fallback parser in case score formatting changes upstream.
if not matches:
    fallback = re.compile(
        r'(?:^|\n)\s*\d+\.\s*<a href="(https://www\.postgresql\.org/docs/current/[^"]+)">(.+?)</a>.*?<div>(.*?)</div>',
        re.I | re.S,
    )
    matches = fallback.findall(content)

if not matches:
    raise SystemExit("Error: could not parse search result entries from response.")

results = []
seen = set()

for url, title, snippet in matches:
    if url in seen:
        continue

    clean_title = html.unescape(re.sub(r"<[^>]+>", "", title))
    clean_title = " ".join(clean_title.split())
    if not clean_title or clean_title.lower().startswith("https://"):
        continue

    clean_snippet = html.unescape(re.sub(r"<[^>]+>", "", snippet))
    clean_snippet = " ".join(clean_snippet.split())
    if not clean_snippet:
        clean_snippet = "(no snippet)"

    seen.add(url)
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
