# G

G is the repository-local Git and GitHub workflow plugin. It uses direct Git
for local repository work, authenticated `gh` directly or through its bundled
G CLI for GitHub provider operations, and the official `github/gh-stack`
extension for stacked pull requests. It has no GitHub connector dependency.

## Bundled skills

| Skill | Purpose |
| --- | --- |
| `g:git-commit` | Create or push explicitly staged regular and targeted commits without opening a pull request. |
| `g:github-repository-triage` | Inspect issue and pull-request queues read-only. |
| `g:github-issues` | Manage issue lifecycle, classify labels and types, and propose taxonomy. |
| `g:github-projects` | Manage GitHub Projects, fields, items, links, templates, and lifecycle. |
| `g:github-investigation` | Investigate issues, pull requests, root causes, and fix quality from repository evidence. |
| `g:github-actions` | Inspect, diagnose, or explicitly repair GitHub Actions failures. |
| `g:github-delivery-status` | Inspect exact-head provider delivery readiness without mutation. |
| `g:github-review-threads` | Inspect review feedback and explicitly reply to or resolve selected threads. |
| `g:github-releases` | Inspect, plan, publish, and validate releases, tags, notes, assets, and packages. |
| `g:github-stars` | Manage the authenticated user's stars and star lists. |
| `g:send` | Commit, push, and open or update one pull request with explicit scope. |
| `g:github-stack` | Manage stacked branches and dependent pull requests with the G stack wrapper. |
| `g:versioning` | Apply the shared version, tag, release-line, and approval-gated release-tag conventions. |
| `g:audit` | Monitor active tasks using G skills and return a prioritized read-only report. |

## Runtime and development

- `.codex-plugin/plugin.json` owns plugin identity, version, discovery metadata,
  and bundled-skill exposure.
- `scripts/g` is the shipped shared CLI artifact. Maintenance source and tests
  live under `projects/g/`; normal skill execution never runs that source tree.
- `.agents/plugins/marketplace.json` registers this source as the local
  `alemar11` marketplace entry.
- Keep the manifest, maintenance package, Python package version, tests, and
  rebuilt artifact aligned. Follow [AGENTS.md](AGENTS.md) and
  [projects/g/AGENTS.md](projects/g/AGENTS.md) for maintenance and validation.
- Treat installed cache copies as verification surfaces, never editable
  sources.
