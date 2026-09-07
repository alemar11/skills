---
name: okf
description: Write, scaffold, inspect, and validate Open Knowledge Format Markdown bundles with the shipped CLI.
---

# OKF

Author OKF v0.2 bundles with [writing guidance](references/writing-okf.md).
Use one concept per non-reserved Markdown file; `index.md` and `log.md` are
reserved. Preserve unknown frontmatter and never invent source facts.

Use offset-aware ISO 8601 datetimes for timestamp fields, `generated.at` for
generation time, and `sources` for provenance. Log headings remain dates.
Optional provenance, trust, lifecycle, and computation fields are not required
for conformance. Read [the specification](assets/spec.md) for exact field
semantics or Attested Computation.

Run `<skill-root>/scripts/okf validate <bundle>` after writing; add `--json`
before `validate` for machine-readable results. Read
[validation](references/validation.md) for conformance options or warnings,
and [examples](references/examples.md) when a concrete format is needed.
Use `--json doctor` for runtime problems. Without PyYAML, the CLI uses a limited
parser and reports that limitation.

Deliver the changed paths or requested content, targeted OKF version,
validation result, and remaining warnings. Broken links are warnings unless
strict link validation was requested.
