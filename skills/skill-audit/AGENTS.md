# Skill Audit Maintenance

`session-evidence` and `portfolio-health` are standalone Python standard-library
artifacts under `scripts/`. Each owns its version and the JSON envelope
`{ok, version, command, data}`. Keep flag and output documentation aligned.
Use major versions for breaking flags/fields, minor for capabilities, patch
for fixes. For helper changes, run affected tests and verify `--help`,
`--version`, `--json doctor`, and a representative offline fixture.
