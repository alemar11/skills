#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: check_docs_script_refs.sh [--skill-dir <path>]

Validate script references and documented flags for this GitHub skill package:
1) every scripts/<name> or scripts/<name>.<ext> reference in docs points to an existing file
2) every referenced script is executable as documented
3) every --flag listed in any references/**/script-summary.md appears in script --help output
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

SCRIPT_SUMMARY_FILES=()
while IFS= read -r summary_file; do
  SCRIPT_SUMMARY_FILES+=("$summary_file")
done < <(find "$SKILL_DIR/references" -type f -name 'script-summary.md' | sort)

if [[ "${#SCRIPT_SUMMARY_FILES[@]}" -eq 0 ]]; then
  echo "Missing script summary files under: $SKILL_DIR/references" >&2
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
    grep -oE 'scripts/[A-Za-z0-9._-]+(/[A-Za-z0-9._-]+)*(\.(sh|py))?' "$doc" >>"$DOC_REFS" || true
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
>"$SUMMARY_ENTRIES"
for summary_file in "${SCRIPT_SUMMARY_FILES[@]}"; do
  awk '
  {
    line = $0
    while (match(line, /`scripts\/[A-Za-z0-9._-]+(\/[A-Za-z0-9._-]+)*(\.(sh|py))?[^`]*`/)) {
      print substr(line, RSTART + 1, RLENGTH - 2)
      line = substr(line, RSTART + RLENGTH)
    }
  }
  ' "$summary_file" >>"$SUMMARY_ENTRIES"
done
sort -u "$SUMMARY_ENTRIES" -o "$SUMMARY_ENTRIES"

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

  help_cmd=("$script_abs")
  include_root_help=0
  read -r -a entry_parts <<<"$entry"
  if [[ "${#entry_parts[@]}" -gt 1 ]]; then
    for ((i=1; i<${#entry_parts[@]}; i++)); do
      token="${entry_parts[$i]}"
      if [[ "$token" == "--json" && "${#help_cmd[@]}" -eq 1 ]]; then
        include_root_help=1
        continue
      fi
      if [[ "$token" == --* || "$token" == "["* || "$token" == "<"* ]]; then
        break
      fi
      help_cmd+=("$token")
    done
  fi
  help_cmd+=(--help)

  if [[ "$script_abs" == *.py ]]; then
    help_output="$(python3 "${help_cmd[@]}" 2>&1 || true)"
  elif [[ "$script_abs" == *.sh ]]; then
    help_output="$(bash "${help_cmd[@]}" 2>&1 || true)"
  else
    help_output="$("${help_cmd[@]}" 2>&1 || true)"
  fi

  if [[ "$include_root_help" -eq 1 ]]; then
    root_help="$("$script_abs" --help 2>&1 || true)"
    help_output="$root_help
$help_output"
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
