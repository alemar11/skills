#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: check_docs_script_refs.sh [--skill-dir <path>]

Validate script references and documented flags for this GitHub skill package:
1) every scripts/<name>.<ext> reference in docs points to an existing file
2) every referenced script is executable as documented
3) every --flag listed in references/script-summary.md appears in script --help output
EOF
}

SKILL_DIR=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skill-dir)
      SKILL_DIR="${2:-}"
      if [[ -z "$SKILL_DIR" ]]; then
        echo "Missing value for --skill-dir" >&2
        usage >&2
        exit 64
      fi
      shift 2
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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -z "$SKILL_DIR" ]]; then
  SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
fi

SCRIPT_SUMMARY="$SKILL_DIR/references/script-summary.md"
if [[ ! -f "$SCRIPT_SUMMARY" ]]; then
  echo "Missing script summary: $SCRIPT_SUMMARY" >&2
  exit 2
fi

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

DOC_FILES=("$SKILL_DIR/SKILL.md")
while IFS= read -r md_file; do
  DOC_FILES+=("$md_file")
done < <(find "$SKILL_DIR/references" -type f -name '*.md' | sort)

DOC_REFS="$TMP_DIR/doc_script_refs.txt"
>"$DOC_REFS"
for doc in "${DOC_FILES[@]}"; do
  if [[ -f "$doc" ]]; then
    grep -oE 'scripts/[A-Za-z0-9._/-]+\.(sh|py)' "$doc" >>"$DOC_REFS" || true
  fi
done

sort -u "$DOC_REFS" -o "$DOC_REFS"

ERRORS=0

while IFS= read -r script_ref; do
  [[ -z "$script_ref" ]] && continue
  if [[ ! -f "$SKILL_DIR/$script_ref" ]]; then
    echo "Missing script reference: $script_ref" >&2
    ERRORS=$((ERRORS + 1))
    continue
  fi
  if [[ ! -x "$SKILL_DIR/$script_ref" ]]; then
    echo "Referenced script is not executable: $script_ref" >&2
    ERRORS=$((ERRORS + 1))
  fi
done <"$DOC_REFS"

SUMMARY_ENTRIES="$TMP_DIR/summary_entries.txt"
awk '
{
  line = $0
  while (match(line, /`scripts\/[^`]+\.(sh|py)[^`]*`/)) {
    print substr(line, RSTART + 1, RLENGTH - 2)
    line = substr(line, RSTART + RLENGTH)
  }
}
' "$SCRIPT_SUMMARY" | sort -u >"$SUMMARY_ENTRIES"

while IFS= read -r entry; do
  [[ -z "$entry" ]] && continue
  script_ref="${entry%% *}"
  script_abs="$SKILL_DIR/$script_ref"

  if [[ ! -f "$script_abs" ]]; then
    echo "Missing script from script-summary.md: $script_ref" >&2
    ERRORS=$((ERRORS + 1))
    continue
  fi
  if [[ ! -x "$script_abs" ]]; then
    echo "Script from script-summary.md is not executable: $script_ref" >&2
    ERRORS=$((ERRORS + 1))
  fi

  flags_file="$TMP_DIR/flags.txt"
  printf '%s\n' "$entry" | grep -oE -- '--[A-Za-z0-9-]+' | sort -u >"$flags_file" || true

  if [[ "$script_abs" == *.py ]]; then
    help_output="$(python3 "$script_abs" --help 2>&1 || true)"
  else
    help_output="$(bash "$script_abs" --help 2>&1 || true)"
  fi

  while IFS= read -r flag; do
    [[ -z "$flag" ]] && continue
    if ! grep -Fq -- "$flag" <<<"$help_output"; then
      echo "Documented flag not found in --help: $script_ref $flag" >&2
      ERRORS=$((ERRORS + 1))
    fi
  done <"$flags_file"
done <"$SUMMARY_ENTRIES"

if [[ "$ERRORS" -gt 0 ]]; then
  echo "Doc/script consistency check failed with $ERRORS issue(s)." >&2
  exit 1
fi

echo "Doc/script consistency check passed."
