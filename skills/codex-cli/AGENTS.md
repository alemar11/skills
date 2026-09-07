# Codex CLI Maintenance

skills/codex-cli/ owns the generic one-shot Codex CLI launcher. Runtime
behavior belongs in SKILL.md, references/model-policy.md, and the shipped
scripts/codex-cli artifact.

## Owned surfaces

- scripts/codex-cli is the supported executable and the single CLI version
  source of truth.
- tests/ protects prompt transport, model aliases, reasoning resolution,
  command construction, and safe dry-run behavior.
- references/model-policy.md owns the Sol/Terra/Luna matrix and task-profile
  resolution. Do not duplicate or silently alter that matrix in unrelated
  skills.
- codex-cli owns execution transport and result reporting only. Review
  semantics remain with callers such as `se:implement`.

## Validation

The shipped launcher requires Python 3.10 or newer. Run the focused unittest
suite from the repository root, then verify the shipped artifact with --help,
--version, --json doctor, and a dry-run fixture.
A live Codex run is not required for the offline contract tests and must not
be used to bypass an unavailable or unauthorized runtime.

Keep the launcher standard-library-only and use semantic versioning: major
for breaking invocation/result changes, minor for capabilities, patch for fixes.
