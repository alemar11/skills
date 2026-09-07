# SE Context

Repository context: [`../../CONTEXT.md`](../../CONTEXT.md)

Scope: `plugins/se/`

## Project Purpose Delta

SE is the repository's graph-first software-delivery plugin. Its bundled Learn,
Grilling, Study, Idea, Spec, Adversarial Review, Delivery Features,
Implement, and Audit skills have distinct runtime contracts, while `AGENTS.md`
and `README.md` define package maintenance ownership and routing.

Spec owns one coherent spec and actionable task plan, saved to GitHub or one
Markdown file. Delivery owns task-to-PR grouping and integration, with task
prerequisites independent of Git topology. The Spec content contract is at
[`specification.md`](skills/spec/references/specification.md).

Study, Spec, and Delivery share subordinate role definitions in
[`subagents.md`](references/subagents.md). Their callers own delegation and
lifecycle. Delivery coordinates in the current task, publishes ready PRs after
local and explicitly requested hosted review, and releases claims on verified
safe pauses. Delivery owns progress separately from semantic spec content.
