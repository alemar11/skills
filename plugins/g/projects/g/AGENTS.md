# G CLI Maintenance

This project is maintenance-only source for the plugin-shared `scripts/g` artifact. Normal skill execution must run the shipped artifact from the plugin root and must not execute modules from `projects/g/`.

## Runtime and boundaries

- Requires Python 3.11 or newer and uses only the standard library.
- Uses direct `git` for local repository state and authenticated `gh` for
  GitHub operations.
- The `attachment upload` domain is the single narrow exception that sends
  opaque binary data directly to GitHub's upload host. It resolves repository
  identity and authentication through `gh`, returns only the stable attachment
  URL and file proof, and never publishes or edits issue or pull-request text.
- The `stack` domain wraps only the official `github/gh-stack` CLI extension;
  `stack ensure --install` is the sole explicit extension-install path and
  never installs an agent skill.
- The subprocess relies on the caller's authenticated `gh` session and does
  not own or persist GitHub credentials.
- Reads and `doctor` never write config or caches. GitHub writes remain explicit named commands with dry-run support where applicable.
- Avoid heuristic provider-failure classification based on ad hoc lists of stderr substrings. Prefer structured results, stable typed errors, and fail closed when authentication or network state cannot be proven. (Codex learning)
- Treat the shipped CLI as production code: keep control flow simple, avoid speculative recovery logic, preserve secret-safe diagnostics, and require executable regression tests plus rebuilt-artifact smoke checks for behavior changes. (Codex learning)

## Source ownership

- Keep cross-domain repository parsing and deterministic fingerprints in
  `repository.py` and `integrity.py`. Domain modules may re-export these
  helpers for compatibility but must not duplicate their implementations.
- Keep `stars.py` and `reviews.py` as stable command façades. Put
  provider transport, parsing/rendering, state validation, and command
  behavior in their adjacent focused modules.
- For reviews, keep provider reads in `review_provider.py`, observation in
  `review_observation.py`, mutations in `review_actions.py`, durable operation
  orchestration in `review_operations.py`, and CLI parsing/dispatch in
  `review_parser.py` and `review_cli.py`. Typed wire contracts remain in their
  existing `review_*` protocol modules.
- Preserve dependency injection through the public façades where compatibility
  tests patch provider behavior. New domain logic should accept an explicit
  backend instead of importing a façade and creating a cycle.

## Build and test

- Run `python3 -m unittest discover -s tests -v` from this directory.
- Run `scripts/build-artifact` to produce `../../scripts/g` as an executable Python zipapp.
- Run `scripts/reinstall-local` only when intentionally testing the versioned
  source through the configured `alemar11` marketplace and installed cache.
- Verify the shipped artifact with `--help`, `--version`, `--json doctor`, and a safe dry-run or read-only command.
- Include `--json stack ensure` in read-only smoke checks; do not install the
  extension as part of tests or artifact builds.
- Stack subprocess smoke tests must use a fake `gh` and assert exact arguments,
  inherited working directory, and non-interactive environment; never use a
  real extension installation as test setup.
- Do not run from `build/`; it is intermediate output.

## Versioning

`pyproject.toml` is the CLI version source of truth. Keep it aligned with the owning plugin manifest. Any runtime change requires a semver bump, rebuilt artifact, tests, and shipped-artifact smoke checks.
