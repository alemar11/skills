<!-- SE-owned reference derived from the durable repository-context contract. -->

# AGENTS.md Compaction

Use this reference only for an explicit AGENTS.md chain-size review or
compaction request. The workflow produces a proposal first and never writes
automatically because a threshold was crossed.

## Chain And Measurement

Identify the actual instruction chain for the affected path:

1. the optional global Codex `AGENTS.md`, reported separately and never edited
   as part of a repository-scoped operation;
2. repository-root `AGENTS.md`;
3. each nested `AGENTS.md` from root to the affected path, in load order.

Report both the repository aggregate and, when available, the effective
aggregate including the global file. Measure UTF-8 bytes deterministically by
summing each considered file's byte size; do not count a guessed separator or
present a token estimate as an exact runtime measure. If a token estimate is
available, label it explicitly as an estimate.

Use 32 KiB (32,768 bytes) as the documented local operating reference for the
aggregate, not as an official single-file limit. Classify the repository
aggregate using exact boundaries:

| Aggregate as a share of 32 KiB | Proposal |
| --- | --- |
| `< 50%` | No size-driven action. |
| `>= 50%` and `< 75%` | Propose a review if the chain mixes conditional detail with always-active rules. |
| `>= 75%` and `< 90%` | Propose moving conditional material to indexed topic files. |
| `>= 90%` | Propose urgent compaction while preserving every mandatory rule. |

Always report the files, byte counts, thresholds, and affected path. A large
on-demand `SKILL.md` is not a reason to compact `AGENTS.md`.

## Section Classification

Read Markdown headings and preserve fenced-code content as content, not as a
new heading. Classify each section before proposing a move:

- keep in `AGENTS.md`: safety, ownership, invariants, always-active rules,
  essential verification, and the minimal Code Review Rules contract;
- move to the nearest context owner's `project-context/<topic>.md`:
  conditional details, examples, rationale, long checklists, historical
  context, and operational notes;
- never move out of `AGENTS.md`: the normative invariant, consequence, and safe
  path required by `## Code Review Rules`.

Apply the [AGENTS.md editorial standard](setup-workflow.md#agentsmd-editorial-standard)
even below the size thresholds. Do not move text merely to lower the byte count.
Preserve the meaning of custom rules, comments, overrides, significant ordering,
and unrelated sections.

## Proposal Shape

For every candidate move, show:

- source file and exact section;
- proposed topic path under the owning root or first-class subproject's flat
  `project-context/` directory;
- short summary and a literal `Read when` condition;
- relative link/pointer replacement in `AGENTS.md`;
- corresponding `CONTEXT.md` index row;
- before/after blocks and any duplicate-normative-content concern.

Topic files must declare a clear title, scope, `Read when` condition, owner or
update logic, and the detailed content. The owning root or subproject
`CONTEXT.md` indexes them; it does not duplicate their body. Keep shared detail
at root and subproject-only detail under the local owner. Create the topic file
and update its index atomically when the request authorizes the compaction.
A size threshold alone never grants write authority.

## Verification

After an authorized compaction:

1. reread the complete root-to-target chain;
2. verify every relative link and every indexed file;
3. scan for duplicate normative rules across root and local `AGENTS.md`,
   `CONTEXT.md`, topic files, and ADRs;
4. confirm the exact `## Code Review Rules` section remains in the applicable
   `AGENTS.md`;
5. run `git diff --check` and report the new byte totals;
6. report retained rules, moved sections, unresolved unknowns, and any content
   deliberately left in place.
