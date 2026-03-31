# GitHub Releases script summary

Use this as the authoritative script catalog referenced by
`github-releases/SKILL.md`.

## Fast helper picks

- Use `scripts/release_plan.sh` to resolve the default branch, target branch,
  target commit, and previous published release tag.
- Use `scripts/release_notes_generate.sh` for inferred notes drafts.
- Use `scripts/release_create.sh` for the release mutation step.

## Repository setup and preflight

- `scripts/check_gh_installed.sh [--min-version <version>]`: Validate that `gh` is installed and meets a minimum version.
- `scripts/check_gh_authenticated.sh [--host github.com]`: Verify active GitHub CLI authentication.
- `scripts/preflight_gh.sh [--host github.com] [--min-version <version>] [--expect-repo <owner/repo>] [--allow-non-project]`: Run prerequisite checks before other `gh` operations.
- `scripts/check_docs_script_refs.sh [--skill-dir <path>]`: Verify docs reference existing scripts and documented flags are present in `--help` output.
- `scripts/issue_resolve_repo.sh [--repo <owner/repo>] [--allow-non-project]`: Resolve the target repository, defaulting to current git project.

## Release scripts

- `scripts/release_plan.sh [--repo <owner/repo>] [--target-branch <branch>] [--allow-non-project]`: Resolve the default branch, chosen target branch, target HEAD commit, and latest published release tag before creating a release.
- `scripts/release_notes_generate.sh --tag <tag> --target-ref <branch-or-sha> [--repo <owner/repo>] [--previous-tag <tag>] [--workdir <path>] [--title-file <path>] [--notes-file <path>] [--allow-non-project]`: Generate draft release title and notes through GitHub's release-notes API.
- `scripts/release_create.sh --tag <tag> --target-ref <branch-or-sha> --notes-mode <infer|blank|user> [--repo <owner/repo>] [--title <text>|--title-file <path>] [--notes-file <path>|--notes-text <text>] [--previous-tag <tag>] [--allow-non-project]`: Create a release with an explicit target and explicit notes strategy. This helper refuses to run without `--notes-mode`.
