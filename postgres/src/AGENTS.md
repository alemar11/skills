# Postgres Rust CLI

This `src/` tree is the maintenance-only implementation behind the public
runtime entrypoint at `postgres/scripts/postgres`.

## Runtime surface

- Normal usage must go through `../scripts/postgres`.
- Do not tell normal skill users to run `cargo`, `rustc`, or binaries from
  `target/` directly.
- `Cargo.toml` is the single source of truth for the CLI version.

## Build and test

- Build: `cargo build --release --manifest-path postgres/Cargo.toml --target-dir postgres/.build/postgres-target`
- Rebuild runtime binary:
  `cargo build --release --manifest-path postgres/Cargo.toml --target-dir postgres/.build/postgres-target && cp postgres/.build/postgres-target/release/postgres postgres/scripts/postgres && chmod +x postgres/scripts/postgres`
- Run tests: `cargo test --manifest-path postgres/Cargo.toml`
- Verify help: `postgres/scripts/postgres --help`
- Verify version: `postgres/scripts/postgres --version`
- Verify JSON doctor: `DB_PROJECT_ROOT=/path/to/repo postgres/scripts/postgres --json doctor`

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
- If a feature needs PostgreSQL client tools, route it through the managed
  tool backend instead of restoring a Homebrew-first assumption.
- Rebuild `../scripts/postgres` after any change that affects runtime behavior
  or operator-facing output, then verify through that shipped artifact rather
  than `.build/` or `target/` binaries.
