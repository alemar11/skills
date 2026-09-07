# Task Decomposition

Read when turning a spec into tasks or revising an existing task plan. The
field contract lives in [specification.md](specification.md).

Prefer a narrow, complete vertical slice with its own observable result. Size
it so a fresh implementation session can understand and validate it without
reconstructing the whole project. Do not promise a fixed token or time budget.
Use one task when that is enough; do not manufacture a minimum task count.

Recommended order explains an efficient path through the work. `blocked_by`
records only a hard prerequisite. Independent tasks may be adjacent in the
ordered list without an edge. Each edge states the capability, artifact, or
verified condition its predecessor must supply. Neither ordering nor an edge
prescribes a branch, PR, worker, or concurrency policy.

A preparatory refactor is justified when repository evidence shows it makes
the requested work safer or feasible. Give it a bounded outcome and checks that
existing behavior is preserved, and identify the later feature criteria it
enables. Avoid generic cleanup tasks.

For a broad migration that cannot be sliced vertically, use expand, migrate,
and contract stages: introduce a compatible new form, migrate bounded groups,
then remove the old form after every required migration. Prefer stages that
remain independently valid. If only an assembled integration can be validated,
name that limitation and the required integration evidence in the spec; do not
claim every intermediate stage can land independently.

For fan-in, keep independent predecessors independent. A dependent task names
all prerequisites; it must not invent an ordering edge between its predecessors
to force a linear Git stack. Review whether the prerequisite outcomes can be
combined and verified. Spec resolves semantic incompatibilities; Delivery
chooses and verifies the concrete integration strategy before starting the
dependent work.

A multi-repository task must describe completion in every repository and the
cross-repository contract or integration check. Prefer separate tasks when
their outcomes can be understood and verified independently. A repository
boundary alone does not force a split.

Explain unusual granularity or integration constraints briefly. Ask about a
split only when it changes outcome, responsibility, rollout, or another
material decision; routine decomposition does not require another approval.
