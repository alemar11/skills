# GitHub Skill Learn

Use this reference when repeated runtime GitHub work uncovers a pattern that
may deserve promotion into a durable script, routing rule, or reference update.

## Improve an existing script when
- The repeated workflow already overlaps a current helper in this GitHub skill
  package or one of its companion GitHub skill packages.
- The gap is about CLI flag drift, repo resolution, preflight, retries, output shape, or another natural extension of the current helper.
- Extending the helper keeps its interface focused instead of turning it into a generic catch-all wrapper.
- The new behavior can be explained briefly in `--help` and validated with the same script-level checks already used by this skill.

## Propose a new script when
- The same repository-scoped GitHub workflow is repeated across multiple sessions.
- The workflow is generic to GitHub repositories rather than tied to one repo's labels, branch naming, or org policy.
- A helper would materially improve speed, safety, or reuse compared with replaying raw `gh` commands by hand.
- No existing script is a clean fit without blurring its responsibility.
- The script can expose a small, explicit interface and use the shared repo-resolution and preflight conventions when they apply.

## Promote to `SKILL.md` or runtime references when
- The learning changes command routing, the fast helper pick, or another runtime decision point.
- Users need the correction before they choose between raw `gh` and a helper script.
- The workflow should become part of the standard runtime path for future runs.

## Keep as maintainer-only guidance when
- The lesson is about repo upkeep, metadata sync, executable bits, release hygiene, or docs validation.
- The behavior is useful for maintaining this skill package but not for solving runtime GitHub tasks.
- The change belongs in maintainer docs or tests, not the runtime skill surface.

## Keep out entirely when
- The pattern is repo-specific, org-specific, preview-only, or too unstable to canonize yet.
- The wrapper would add little value beyond a single obvious `gh` command.
- The lesson is better kept in session memory until it proves durable.

## Packaging rules
- Prefer improving an existing helper before adding a new one.
- Keep helpers repository-scoped; do not expand this runtime skill toward organization-level mutations.
- Favor explicit flags, predictable output, and one clear job per script.
- When cross-repo or non-project use is valid, support `--repo` and `--allow-non-project` consistently with the rest of the skill.
- Document every promoted helper in `references/script-summary.md`.
- Update the owning skill's `SKILL.md` only when the promoted learning changes
  the runtime decision flow or the preferred fast path.

## Current promoted learnings
- Release creation now uses dedicated planning, notes-generation, and
  release-creation helpers with explicit notes strategy handling in
  `github-releases`.
- `gh pr edit` may require `read:project`; `scripts/prs_update.sh` should stay the fallback for title/body/base-only updates when that scope is missing.
- Generic Actions triage is not always PR-based; keep that split in
  `github-ci` and reserve `gh pr checks` for PR-associated runs.
- Repo resolution from git remotes must strip the trailing `.git`, and shared repo normalization should live in shared helpers rather than diverging per script.
- Label helper scripts must stay aligned with live `gh --help` behavior.
- `commit_issue_linker.sh` should preserve worker exit codes and treat an existing close token as safe to execute.
- New helper proposals should first answer: can an existing script absorb this cleanly, or is a new focused helper the better reusable match?
