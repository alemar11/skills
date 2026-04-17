# Postgres Rust CLI

This `projects/postgres/` directory is the maintenance/build project behind the
public runtime entrypoint at `skills/postgres/scripts/postgres`.

## Runtime surface

- Normal usage must go through the shipped artifact at `../../scripts/postgres`.
- Do not tell normal skill users to run `cargo`, `rustc`, or binaries from
  `target/` directly.
- `Cargo.toml` is the single source of truth for the CLI version.
- Canonical persisted config lives at `<project-root>/.skills/postgres/config.toml`.

## Build and test

- Build: `cargo build --release --manifest-path skills/postgres/projects/postgres/Cargo.toml`
- Rebuild runtime binary:
  `cargo build --release --manifest-path skills/postgres/projects/postgres/Cargo.toml && cp skills/postgres/projects/postgres/target/release/postgres skills/postgres/scripts/postgres && chmod +x skills/postgres/scripts/postgres`
- Run tests: `cargo test --manifest-path skills/postgres/projects/postgres/Cargo.toml`
- Verify help: `skills/postgres/scripts/postgres --help`
- Verify version: `skills/postgres/scripts/postgres --version`
- Verify JSON doctor: `DB_PROJECT_ROOT=/path/to/repo skills/postgres/scripts/postgres --json doctor`

## Semver policy

- Patch: backward-compatible fixes, doc-aligned runtime cleanups, and internal
  maintenance changes that do not change the CLI contract.
- Minor: backward-compatible command, flag, or JSON-output additions.
- Major: breaking command renames/removals, incompatible flag changes, or
  breaking JSON-contract changes.

## Safe maintenance

- Keep the CLI contract stable around the top-level nouns:
  `doctor`, `profile`, `query`, `activity`, `schema`, `dump`, `migration`,
  and `docs`.
- Prefer adding behavior in Rust over reintroducing per-task shell wrappers.
- Keep config migration one-way from legacy `postgres.toml` to canonical
  `config.toml`; do not reintroduce writes to the legacy path.
- If a feature needs PostgreSQL client tools, route it through the managed
  tool backend only. Do not restore PATH probing or persisted binary-dir
  config.
- Rebuild `../../scripts/postgres` after any change that affects runtime
  behavior or operator-facing output, then verify through that shipped artifact
  rather than `target/` binaries.
- Keep project-local generated state scoped to `projects/postgres/.gitignore`.
- Delete stale pre-`skills/` layout artifacts if they
  reappear, including `skills/postgres/.build/`, `skills/postgres/target/`, `skills/postgres/src/`,
  and root-level Cargo files.
