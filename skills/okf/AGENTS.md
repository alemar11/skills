# OKF Maintenance

`skills/okf/` owns the reusable OKF writer and validator, its bundled local
specification assets, and the shipped `scripts/okf` artifact. Authoring and
validation behavior belongs in `SKILL.md` and `references/`.

## Owned surfaces

- `scripts/okf` is the only public executable. Its `VERSION` is the CLI
  version source of truth; `SPEC_VERSION` identifies the OKF contract and is
  separate.
- `assets/spec.md` and `assets/manifest.json` are the bundled specification
  inputs and must remain synchronized after an approved refresh.
- `references/` owns writing, examples, and validation guidance; `tests/` owns
  executable regression coverage.

## Maintenance contract

- Official specification refreshes and integrity checks belong to the
  repository maintainer workflow; do not change bundled spec assets as an
  incidental runtime edit.
- Keep runtime OKF documentation independent from maintainer-only routing.

## Validation

- For CLI changes, run the focused unittest suite and verify the shipped
  artifact with `--help`, `--version`, `--json doctor`, and a safe offline
  scaffold or validate fixture.

Use semantic versions for the CLI: major for incompatible contracts, minor
for compatible capabilities, and patch for fixes.
