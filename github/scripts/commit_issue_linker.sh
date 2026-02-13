#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: commit_issue_linker.sh --message <text> [--context <text>] [--branch <name>] [--repo <path|owner/repo>] [--issue-number <n>] [--token <fixes|closes|resolves>] [--dry-run|--execute] [--json]
  --message      required: base commit message
  --context      optional additional context text
  --branch       optional branch override
  --repo         optional context path (git repo path preferred)
  --issue-number explicit issue number
  --token        one of fixes|closes|resolves (default: fixes)
  --dry-run      preview only (default)
  --execute      run git commit with proposed message
  --json         emit JSON output
USAGE
}

MESSAGE=""
CONTEXT=""
BRANCH=""
REPO=""
ISSUE_NUMBER=""
TOKEN="fixes"
DRY_RUN=1
EXECUTE=0
OUTPUT_JSON=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --message)
      MESSAGE="${2:-}"
      if [[ -z "$MESSAGE" ]]; then
        echo "Missing value for --message" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --context)
      CONTEXT="${2:-}"
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
    --repo)
      REPO="${2:-}"
      if [[ -z "$REPO" ]]; then
        echo "Missing value for --repo" >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --issue-number)
      ISSUE_NUMBER="${2:-}"
      if [[ -z "$ISSUE_NUMBER" ]]; then
        echo "Missing value for --issue-number" >&2
        usage >&2
        exit 64
      fi
      if ! [[ "$ISSUE_NUMBER" =~ ^[1-9][0-9]*$ ]]; then
        echo "Invalid --issue-number '$ISSUE_NUMBER'. It must be a positive integer." >&2
        exit 64
      fi
      shift 2
      ;;
    --token)
      TOKEN="${2:-}"
      if [[ "$TOKEN" != "fixes" && "$TOKEN" != "closes" && "$TOKEN" != "resolves" ]]; then
        echo "Invalid --token value '$TOKEN'. Use fixes, closes, or resolves." >&2
        usage >&2
        exit 64
      fi
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      EXECUTE=0
      shift
      ;;
    --execute)
      EXECUTE=1
      DRY_RUN=0
      shift
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

if [[ -z "$MESSAGE" ]]; then
  echo "Missing required --message" >&2
  usage >&2
  exit 64
fi

if [[ "$DRY_RUN" -ne 1 && "$EXECUTE" -ne 1 ]]; then
  DRY_RUN=1
fi

if [[ -d "$REPO" ]]; then
  REPO_PATH="$REPO"
elif [[ -n "$REPO" ]]; then
  REPO_PATH="."
else
  REPO_PATH="."
fi

if ! OUTPUT="$(python3 - "$MESSAGE" "$CONTEXT" "$BRANCH" "$ISSUE_NUMBER" "$TOKEN" "$EXECUTE" "$OUTPUT_JSON" "$REPO" "$REPO_PATH" 2>&1 <<'PY'
import json
import re
import subprocess
import sys


def git_command(cwd: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", cwd, *args],
        text=True,
        capture_output=True,
    )


def is_git_repo(cwd: str) -> bool:
    return git_command(cwd, "rev-parse", "--is-inside-work-tree").returncode == 0


def current_branch(cwd: str) -> str:
    result = git_command(cwd, "rev-parse", "--abbrev-ref", "HEAD")
    if result.returncode != 0:
        return ""
    return (result.stdout or "").strip()


def parse_existing_issue_links(message: str) -> list[str]:
    pattern = re.compile(r"\b(?:fixes|fix|closes|close|resolves|resolve)\s*#?(\d+)\b", re.IGNORECASE)
    return [match.group(1) for match in pattern.finditer(message or "")]


def collect_candidates(
    explicit_issue: str,
    context: str,
    branch: str,
    branch_name: str,
) -> list[dict]:
    if explicit_issue:
        return [
            {
                "number": int(explicit_issue),
                "score": 0.98,
                "source": "explicit",
                "reason": "explicit issue argument",
            }
        ]

    text_parts = [part for part in (context, branch, branch_name) if part]
    text = " ".join(text_parts).strip()
    if not text:
        return []

    patterns = [
        ("branch", re.compile(r"(?i)\b(?:issue|gh|fix|bug|feature|build|docs?|test|chore)/?(?:gh-)?(\d{1,10})\b")),
        ("hash", re.compile(r"\b#(\d{1,10})\b")),
        (
            "keyword",
            re.compile(
                r"\b(?:issue|ticket|fix|close|fixes|closes|resolves|resolve)\s*(?:number|#)?\s*(\d{1,10})\b",
                re.IGNORECASE,
            ),
        ),
    ]

    discovered: dict[str, dict] = {}
    for source, pattern in patterns:
        for match in pattern.finditer(text):
            number = match.group(1)
            score = {"branch": 0.92, "keyword": 0.80, "hash": 0.74}.get(source, 0.70)
            existing = discovered.get(number)
            if existing is None or score > existing["score"]:
                discovered[number] = {
                    "number": int(number),
                    "score": score,
                    "source": source,
                    "reason": f"matched {source} pattern",
                }

    return sorted(
        discovered.values(),
        key=lambda item: (-item["score"], item["number"]),
    )


def build_decision(candidates: list[dict]) -> tuple[str, str]:
    if not candidates:
        return "", "no_candidate"
    if len(candidates) == 1:
        return str(candidates[0]["number"]), "single_candidate"
    return "", "ambiguous"


def run_commit(cwd: str, message: str) -> tuple[bool, str]:
    result = git_command(cwd, "commit", "-m", message)
    if result.returncode != 0:
        return False, (result.stderr or result.stdout or "").strip()
    return True, (result.stdout or "").strip()


message = sys.argv[1]
context = sys.argv[2]
branch = sys.argv[3]
explicit_issue = sys.argv[4]
token = (sys.argv[5] or "fixes").lower()
execute = bool(int(sys.argv[6]))
output_json = bool(int(sys.argv[7]))
repo_arg = sys.argv[8]
repo_path = sys.argv[9]

branch_name = branch
if not branch_name and repo_path and is_git_repo(repo_path):
    branch_name = current_branch(repo_path)

existing_links = parse_existing_issue_links(message)
if existing_links:
    candidate = str(existing_links[0])
    decision_state = "already_linked"
    candidates = [
        {
            "number": int(number),
            "score": 1.0,
            "source": "message",
            "reason": "existing close token",
        }
        for number in existing_links
    ]
    proposed = message
else:
    candidates = collect_candidates(explicit_issue, context, branch_name, branch_name)
    candidate, decision_state = build_decision(candidates)
    proposed = message
    if candidate:
        tokenized = f"{token} #{candidate}"
        if tokenized.lower() not in (message or "").lower():
            proposed = message
            if proposed and not proposed.endswith("\n"):
                proposed = f"{proposed}\n\n"
            proposed = f"{proposed}{token.title()} #{candidate}"

payload = {
    "decision_state": decision_state,
    "candidate": candidate,
    "token": token.title(),
    "proposed_message": proposed,
    "dry_run": not execute,
    "repo": repo_arg,
    "branch": branch_name or "",
    "candidates": candidates,
    "existing_issue_link": {
        "present": bool(existing_links),
        "numbers": sorted(set(existing_links), key=int),
    },
}

if execute:
    if decision_state != "single_candidate":
        payload["decision_state"] = "blocked"
        if output_json:
            print(json.dumps(payload, indent=2))
            raise SystemExit(2)
        print("Execution blocked: requires a single issue candidate.")
        raise SystemExit(2)

    if not is_git_repo(repo_path):
        payload["error"] = "Not inside a Git repository. Run in a repo or pass --repo as a valid path."
        if output_json:
            print(json.dumps(payload, indent=2))
            raise SystemExit(1)
        print(payload["error"])
        raise SystemExit(1)

    success, commit_output = run_commit(repo_path, proposed)
    if not success:
        payload["error"] = commit_output
        payload["commit_exit_code"] = 1
        if output_json:
            print(json.dumps(payload, indent=2))
            raise SystemExit(1)
        print(commit_output)
        raise SystemExit(1)
    payload["executed"] = True
    payload["decision_state"] = "executed"
    payload["commit_output"] = commit_output
    payload["commit_exit_code"] = 0

if output_json:
    print(json.dumps(payload, indent=2))
else:
    print(f"decision_state={payload['decision_state']}")
    print(f"candidate={payload['candidate']}")
    print(f"token={payload['token']}")
    print(f"proposed_message={payload['proposed_message']}")
    print(f"dry_run={str(payload['dry_run']).lower()}")
    if payload["candidates"]:
        print("candidates:")
        for item in payload["candidates"]:
            print(
                f"- {item['number']} score={item['score']:.2f} "
                f"source={item['source']} reason={item['reason']}"
            )
    print(
        f"existing_issue_link={'present' if payload['existing_issue_link']['present'] else 'none'}"
    )
    if payload.get("executed"):
        print("Commit executed.")
PY
)";
then
  RC=$?
  echo "$OUTPUT"
  exit "$RC"
fi

echo "$OUTPUT"
