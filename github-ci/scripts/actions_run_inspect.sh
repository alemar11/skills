#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  actions_run_inspect.sh [--repo <owner/repo>] [--branch <branch>] [--commit <sha>] [--workflow <name>] [--event <event>] [--status <status>] [--limit N] [--all] [--allow-non-project]
  actions_run_inspect.sh --run-id <id> [--repo <owner/repo>] [--job-id <id>] [--artifact-name <name>] [--download-dir <path>] [--summary-only] [--allow-non-project]
  actions_run_inspect.sh --job-id <id> [--repo <owner/repo>] [--allow-non-project]

Mode 1: list recent workflow runs with optional filters.
Mode 2: inspect one run, print summary metadata, optionally show failed log lines,
        optionally show one job log, and optionally download one artifact.
Mode 3: inspect one job log directly when only the job ID is known.
EOF
}

REPO=""
RUN_ID=""
JOB_ID=""
ARTIFACT_NAME=""
DOWNLOAD_DIR="."
BRANCH=""
COMMIT=""
WORKFLOW=""
EVENT=""
STATUS=""
LIMIT=10
INCLUDE_DISABLED=0
SUMMARY_ONLY=0
ALLOW_NON_PROJECT=0

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
    --run-id)
      RUN_ID="${2:-}"
      if [[ -z "$RUN_ID" ]]; then
        echo "Missing value for --run-id" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --job-id)
      JOB_ID="${2:-}"
      if [[ -z "$JOB_ID" ]]; then
        echo "Missing value for --job-id" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --artifact-name)
      ARTIFACT_NAME="${2:-}"
      if [[ -z "$ARTIFACT_NAME" ]]; then
        echo "Missing value for --artifact-name" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --download-dir)
      DOWNLOAD_DIR="${2:-}"
      if [[ -z "$DOWNLOAD_DIR" ]]; then
        echo "Missing value for --download-dir" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --branch)
      BRANCH="${2:-}"
      if [[ -z "$BRANCH" ]]; then
        echo "Missing value for --branch" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --commit)
      COMMIT="${2:-}"
      if [[ -z "$COMMIT" ]]; then
        echo "Missing value for --commit" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --workflow)
      WORKFLOW="${2:-}"
      if [[ -z "$WORKFLOW" ]]; then
        echo "Missing value for --workflow" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --event)
      EVENT="${2:-}"
      if [[ -z "$EVENT" ]]; then
        echo "Missing value for --event" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --status)
      STATUS="${2:-}"
      if [[ -z "$STATUS" ]]; then
        echo "Missing value for --status" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --limit)
      LIMIT="${2:-}"
      if [[ -z "$LIMIT" ]]; then
        echo "Missing value for --limit" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --all)
      INCLUDE_DISABLED=1
      shift
      ;;
    --summary-only)
      SUMMARY_ONLY=1
      shift
      ;;
    --allow-non-project)
      ALLOW_NON_PROJECT=1
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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/github_lib.sh"

if [[ -n "$REPO" ]]; then
  github_require_repo_reference "$REPO"
fi
if [[ -n "$RUN_ID" ]]; then
  github_require_positive_int "run-id" "$RUN_ID"
fi
if [[ -n "$JOB_ID" ]]; then
  github_require_positive_int "job-id" "$JOB_ID"
fi
github_require_positive_int "limit" "$LIMIT"

if [[ -n "$ARTIFACT_NAME" && -z "$RUN_ID" ]]; then
  echo "--artifact-name requires --run-id." >&2
  exit 64
fi

TARGET_REPO="$(github_resolve_repo "$SCRIPT_DIR" "$REPO" "$ALLOW_NON_PROJECT")"

if [[ -z "$RUN_ID" && -z "$JOB_ID" ]]; then
  CMD=(
    gh run list
    --repo "$TARGET_REPO"
    -L "$LIMIT"
    --json databaseId,workflowName,status,conclusion,headBranch,headSha,displayTitle,event,url
  )
  if [[ "$INCLUDE_DISABLED" -eq 1 ]]; then
    CMD+=(--all)
  fi
  if [[ -n "$BRANCH" ]]; then
    CMD+=(--branch "$BRANCH")
  fi
  if [[ -n "$COMMIT" ]]; then
    CMD+=(--commit "$COMMIT")
  fi
  if [[ -n "$WORKFLOW" ]]; then
    CMD+=(--workflow "$WORKFLOW")
  fi
  if [[ -n "$EVENT" ]]; then
    CMD+=(--event "$EVENT")
  fi
  if [[ -n "$STATUS" ]]; then
    CMD+=(--status "$STATUS")
  fi
  "${CMD[@]}"
  exit 0
fi

if [[ -z "$RUN_ID" ]]; then
  gh run view --repo "$TARGET_REPO" --job "$JOB_ID" --log
  exit 0
fi

gh run view "$RUN_ID" --repo "$TARGET_REPO" \
  --json databaseId,workflowName,status,conclusion,headBranch,headSha,displayTitle,url,event,createdAt,updatedAt

LOG_EXIT_STATUS=0
FALLBACK_REQUESTED=0
FALLBACK_SUCCEEDED=0
if [[ "$SUMMARY_ONLY" -eq 0 ]]; then
  echo
  set +e
  LOG_OUTPUT="$(gh run view "$RUN_ID" --repo "$TARGET_REPO" --log-failed 2>&1)"
  LOG_EXIT_STATUS=$?
  set -e
  if [[ "$LOG_EXIT_STATUS" -eq 0 ]]; then
    printf '%s\n' "$LOG_OUTPUT"
  else
    echo "Warning: gh run view --log-failed failed; continuing with explicit fallback steps if provided." >&2
    printf '%s\n' "$LOG_OUTPUT" >&2
  fi
fi

JOB_EXIT_STATUS=0
if [[ -n "$JOB_ID" ]]; then
  FALLBACK_REQUESTED=1
  echo
  set +e
  JOB_OUTPUT="$(gh run view --repo "$TARGET_REPO" --job "$JOB_ID" --log 2>&1)"
  JOB_EXIT_STATUS=$?
  set -e
  if [[ "$JOB_EXIT_STATUS" -eq 0 ]]; then
    printf '%s\n' "$JOB_OUTPUT"
    FALLBACK_SUCCEEDED=1
  else
    printf '%s\n' "$JOB_OUTPUT" >&2
  fi
fi

if [[ -n "$ARTIFACT_NAME" ]]; then
  FALLBACK_REQUESTED=1
  mkdir -p "$DOWNLOAD_DIR"
  echo
  gh run download "$RUN_ID" --repo "$TARGET_REPO" -n "$ARTIFACT_NAME" -D "$DOWNLOAD_DIR"
  FALLBACK_SUCCEEDED=1
fi

if [[ "$LOG_EXIT_STATUS" -ne 0 && "$FALLBACK_REQUESTED" -eq 1 && "$FALLBACK_SUCCEEDED" -eq 1 ]]; then
  LOG_EXIT_STATUS=0
fi
if [[ "$LOG_EXIT_STATUS" -ne 0 ]]; then
  exit "$LOG_EXIT_STATUS"
fi
if [[ "$JOB_EXIT_STATUS" -ne 0 ]]; then
  exit "$JOB_EXIT_STATUS"
fi
