# GitHub Actions configuration preflight

Inspect repository settings read-only before authoring PR automation. The
preflight is advisory: report missing or unreadable settings while completing
the explicitly requested workflow edit.

## Repository setting

The repository setting **Actions → General → Workflow permissions → Allow
GitHub Actions to create and approve pull requests** controls PR automation.
Read it through the API below. Enabling it is a separate settings mutation;
report a disabled or inaccessible setting without changing it unless authorized.
Organization or enterprise policy may restrict it.

The official GitHub guidance is [Managing GitHub Actions settings for a
repository](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository#preventing-github-actions-from-creating-or-approving-pull-requests).

## Workflow permissions

The workflow must declare the minimum permissions needed by the job:

```yaml
permissions:
  contents: read
  pull-requests: write
```

If the Action also creates a branch or tag, use `contents: write` for the
scope that performs that operation:

```yaml
permissions:
  contents: write
  pull-requests: write
```

Prefer job-level permissions when only one job needs the write capability.
`default_workflow_permissions: write` is a repository default; it is not a
substitute for reviewing the workflow's explicit `permissions` declaration.

## Read-only settings preflight

Read the exact repository's settings with direct `gh`:

```bash
gh api 'repos/<owner>/<repo>/actions/permissions'
gh api 'repos/<owner>/<repo>/actions/permissions/workflow'
```

The first response reports whether Actions is enabled; the second reports
`default_workflow_permissions` and `can_approve_pull_request_reviews`.

The result reports the repository gate for pull-request automation, but it
cannot prove the effective `pull-requests: write` token permission of a
workflow that has not run. The workflow YAML and, when necessary, a completed
run remain authoritative for that check. A forbidden response can mean the
authenticated `gh` token lacks the required Administration read permission,
or that an account, plan, organization, or enterprise policy prevents access.
If the result is blocked or unavailable and the user asked to create the
workflow, report the warning and write the requested Action with the necessary
`permissions` block. A disabled setting requires configuration; an inaccessible
setting remains unverified. Do not claim the workflow is functional from either
result. An enabled setting still does not prove effective run-token permissions;
account for event, fork, and organization restrictions when diagnosing a run.

The [official GitHub Actions permissions REST API
documentation](https://docs.github.com/en/rest/actions/permissions?apiVersion=2022-11-28)
defines the endpoint and its response fields. These reads use the read-only
surface documented by [`gh api`](https://cli.github.com/manual/gh_api); they do
not call the corresponding `PUT` settings endpoints.

## Mutation boundary

This preflight never changes repository settings, workflow files, branches, or
tags. Changing the repository setting, adding a workflow, creating a branch,
creating a tag, or opening a pull request are separate mutations and require
explicit user authorization.
