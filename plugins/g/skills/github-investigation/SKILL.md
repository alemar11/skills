---
name: github-investigation
description: "Investigate an issue, pull request, or proposed fix for root cause and fix quality."
---

# GitHub Investigation

Before any shell command that may contact GitHub or a package registry, read
and follow [Network execution](../../references/network-execution.md).

## Transport

Use authenticated `gh`, directly or through the shared CLI, for every GitHub
provider read and write.

Before the first provider-facing direct `gh` or shared CLI fallback, load
[`../../references/gh-dependency-preflight.md`](../../references/gh-dependency-preflight.md)
and require its host and authentication checks.

## Role

Give an evidence-backed judgment of the selected issue, PR, or proposed fix.
Use `g:github-repository-triage` for queues, `g:github-actions` for CI, and
`g:github-review-threads` for hosted feedback. Investigation alone authorizes
no edits, comments, closure, merge, or publication.

## Start

Resolve `<plugin-root>` as two directories above the directory containing this
`SKILL.md` before invoking the shared CLI.

Prefer exact `gh` PR or issue context plus local repository evidence over web
browsing. Use direct `gh` for provider and branch discovery:

```bash
gh issue view <number> --json number,title,state,author,body,comments,labels,updatedAt,url
gh pr view <number> --json number,title,state,author,body,comments,reviews,files,commits,statusCheckRollup,mergeStateStatus,headRefName,headRepositoryOwner,url
gh pr diff <number> --patch
git status --short --branch
git fetch origin
git log --oneline --decorate -20
```

When automated-review freshness is relevant, use the one-shot provider-neutral
check as evidence and keep analysis read-only:

```bash
<plugin-root>/scripts/g --json reviews check --provider codex --repo <owner/repo> --pr <number> --head <sha>
```

Route review work to `$g:github-review-threads` with the exact repository
and PR plus one operation per invocation: `review_operation=check|wait` for
read-only freshness, or `review_operation=reply|request|resolve` with
`mutation_mode=apply` only after the matching write is authorized. A Codex
`request` uses G's typed full-head/request-key operation and persists its
complete receipt before any wait; it has no legacy text fallback.

Read applicable repository instructions and the guidance relevant to the
selected investigation. If the repository is not checked out locally, clone or fetch it
only when the review requires code-path evidence that `gh` cannot provide.

## Review Contract

Always answer these points when they apply:

- URL/ref: issue or PR number and affected surface.
- Bug or behavior: what is being reported or changed.
- Cause: the real code path and confidence, or the exact missing evidence.
- Provenance: who or what introduced, exposed, or carried the behavior forward
  when bounded history can identify it.
- Fix quality: whether the proposed or likely fix belongs at the right
  ownership boundary.
- Refactor call: whether a slightly larger change would improve correctness,
  clarity, or future maintenance.
- Proof: tests, live repro, CI, docs, dependency source, or shipped/current
  behavior checked.
- Risk: what remains unverified or brittle.

Do not approve, comment, close, merge, push, or land unless the user explicitly
asks for that action. Route authorized GitHub issue comments, labels, type
changes, or closure through `$g:github-issues` after normalizing each
write to `mutation_mode=apply`, the exact repository and issue target, and one
canonical `issue_operation`.

## Code Reading Depth

Trace the reported behavior through the relevant ownership boundary and tests;
expand beyond the diff when needed to establish cause. Check installed
dependency contracts where behavior depends on them. Prefer current source and
executable evidence over stale comments, CI, or release reports.

## Provenance

For bug or regression reviews, include a compact provenance answer when feasible:

- Use `git log -S/-G`, `git blame`, linked PRs/issues, and tests.
- Separate original author, committer/merger, and current PR author when they
  differ.
- Phrase as `introduced by`, `made visible by`, or `carried forward by`.
- Include the canonical provenance confidence from
  [references/states.md](references/states.md).
- For features, docs, refactors, or untraceable issues, write `N/A` or say what
  evidence is missing.

## Fix Quality

Prefer a correction at the owning boundary with a regression check at the
smallest meaningful seam. Recommend a larger refactor only when it materially
improves the invariant without widening risk. Preserve public behavior unless
changing it is requested.

## Output Shapes

For PR reviews, lead with findings ordered by severity. Each finding needs a
file/line/symbol reference and concrete failure mode. If there are no blocking
correctness issues, say that clearly and list the strongest proof plus residual
risk.

For issue reviews, reconstruct the reporter's scenario, check current `main`,
reproduce or build a minimal proof when feasible, then identify the root cause
and recommended disposition.

Use this compact shape for "what is this about", "is this the best fix", or
"what did we fix":

```text
Ref: #123 / PR #456
Surface: <runtime/CLI/provider/channel/docs>
Bug: <one or two sentences>
Cause: <code path + confidence>
Provenance: <introduced/made visible/carried forward by commit/PR/date, or N/A/unknown>
Best fix: <what should change and why>
refactor_disposition: <canonical value from references/states.md>
refactor_shape: <specific shape|not-applicable>
Proof: <tests/live/CI/source/dependency docs>
Risk: <remaining uncertainty>
```

Use the canonical invocation fields from `../../references/options.md` for
routed G operations. `refactor_disposition` is a judgment returned by
this skill, not an invocation option: derive it from the review evidence and do
not ask the user to select it. Keep the explanation of why a refactor is or is
not warranted in the surrounding prose.

## References

- `references/states.md`: provenance confidence and refactor disposition.
- `../../references/options.md`: caller-selectable G invocation fields.
