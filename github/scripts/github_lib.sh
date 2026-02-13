#!/usr/bin/env bash
set -euo pipefail

github_require_repo_reference() {
  local repo="${1:-}"
  if [[ -z "$repo" || "$repo" != */* || "$repo" == */ || "$repo" == */*/* ]]; then
    echo "Invalid --repo value '$repo'. Use owner/repo." >&2
    exit 64
  fi
}

github_require_issue_number() {
  local issue="${1:-}"
  if ! [[ "$issue" =~ ^[1-9][0-9]*$ ]]; then
    echo "Invalid --issue value '$issue'. It must be a positive integer." >&2
    exit 64
  fi
}

github_require_pr_number() {
  local pr="${1:-}"
  if ! [[ "$pr" =~ ^[1-9][0-9]*$ ]]; then
    echo "Invalid --pr value '$pr'. It must be a positive integer." >&2
    exit 64
  fi
}

github_require_positive_int() {
  local field="${1:-}"
  local value="${2:-}"
  if ! [[ "$value" =~ ^[1-9][0-9]*$ ]]; then
    echo "Invalid --$field value '$value'. It must be a positive integer." >&2
    exit 64
  fi
}

github_require_allowed_value() {
  local field="${1:-}"
  local value="${2:-}"
  shift 2
  local allowed
  for allowed in "$@"; do
    if [[ "$value" == "$allowed" ]]; then
      return 0
    fi
  done
  local joined
  joined="$(printf '%s, ' "$@")"
  joined="${joined%, }"
  echo "Invalid --$field value '$value'. Use $joined." >&2
  exit 64
}

github_normalize_hex_color() {
  local color="${1:-}"
  if [[ -z "$color" ]]; then
    return 0
  fi

  local normalized="${color#\#}"
  if ! [[ "$normalized" =~ ^[A-Fa-f0-9]{6}$ ]]; then
    echo "Invalid --color value '$color'. Use six hex digits, e.g. 1F9D55." >&2
    exit 64
  fi

  echo "$normalized"
}

github_resolve_repo() {
  local script_dir="${1:-}"
  local repo_ref="${2:-}"
  local allow_non_project="${3:-0}"

  local -a preflight_cmd=("$script_dir/preflight_gh.sh")
  local -a resolve_cmd=("$script_dir/issue_resolve_repo.sh")

  if [[ "$allow_non_project" -eq 1 ]]; then
    preflight_cmd+=(--allow-non-project)
    resolve_cmd+=(--allow-non-project)
  fi

  if [[ -n "$repo_ref" ]]; then
    resolve_cmd+=(--repo "$repo_ref")
  fi

  "${preflight_cmd[@]}" >&2
  "${resolve_cmd[@]}"
}
