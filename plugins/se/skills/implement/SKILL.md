---
name: implement
description: "Implement selected local work without orchestration or PR publication. Use se:deliver-features for reviewed PR delivery of saved SE specs."
---

# Implement

Implement exactly the user-selected spec, ticket, or directly described unit of
work in the current repository.

Use this for an actual implementation request with selected work. For a selected spec task, read its main spec and detailed task contract. Route
explicit reviewed PR delivery of complete saved SE specs to `se:deliver-features`; do not select this
skill merely because the word "implement" appears in discussion or another
skill's instructions.

Use test-driven development where practical, especially at pre-agreed seams.

Run checks that cover the changed behavior and any repository-required gates.
Broaden validation only for unresolved risks or failures.

Use an independent review for substantial or risky changes when available.

Commit only the files required for the selected work to the current branch.
Preserve unrelated work, and do not push, publish a pull request, merge,
deploy, or close issues unless the caller explicitly authorizes that next
step.
