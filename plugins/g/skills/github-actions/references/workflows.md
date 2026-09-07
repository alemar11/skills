# GitHub CI Workflows

## Checks for the selected target

Resolve the exact repository and PR or commit, including the GitHub host. Use
explicit `--repo` arguments after resolution; do not let the working directory
silently select another repository.

```bash
gh pr view <number> --repo <owner/repo> --json number,url,headRefOid
gh pr checks <number> --repo <owner/repo> --json name,state,bucket,link,workflow,startedAt,completedAt
```

Keep usable check data even when the command exits nonzero: `gh pr checks`
returns 8 for pending checks, and a failure result is not automatically a
transport failure. Interpret its structured evidence before diagnosing the
command. A failed or inaccessible read never establishes an empty inventory.

For a commit target, or when the PR summary is empty or incomplete, read both
paginated check runs and commit statuses at the exact SHA:

```bash
gh api --paginate 'repos/<owner>/<repo>/commits/<sha>/check-runs?per_page=100'
gh api --paginate 'repos/<owner>/<repo>/commits/<sha>/statuses?per_page=100'
```

Preserve check identity, source, and latest result; status histories are not
additional current checks. Complete pagination before claiming no checks or
complete coverage. A bounded inspection must name its limit and unresolved
coverage. If the PR HEAD changes during collection, recollect for the new HEAD
or label the evidence as belonging to the earlier SHA.

## Runs and logs

Use the check's URL to identify its provider. Follow GitHub Actions run/job
links for Actions logs; retain external check links without treating them as
Actions jobs or inventing a GitHub log source.

```bash
gh run list --repo <owner/repo> --commit <sha> --limit 10 --json databaseId,headSha,status,conclusion,url
gh run view <run-id> --repo <owner/repo> --json headSha,status,conclusion,jobs,url
gh run view <run-id> --repo <owner/repo> --log-failed
gh run view --job <job-id> --repo <owner/repo> --log
```

Match run SHA and attempt to the inspected check. The run list is a sample,
not a complete check inventory. Fetch only the relevant job or failed-step
logs, then extract a short excerpt with enough context to identify the command
and cause. Preserve job/run URLs. If logs are pending, expired, forbidden, or
unavailable, report that evidence gap and any usable job metadata; do not
convert it into a successful check or an invented root cause.

State the diagnosis before an authorized code edit. Validate the changed
behavior locally and inspect a new remote run when available. Do not rerun,
cancel, dispatch, or publish as a side effect of inspection.

Command details: [PR checks](https://cli.github.com/manual/gh_pr_checks),
[run view](https://cli.github.com/manual/gh_run_view), and
[paginated API reads](https://cli.github.com/manual/gh_api).
