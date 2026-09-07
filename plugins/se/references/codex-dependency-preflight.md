# SE G Dependency Preflight

This reference owns the fail-closed availability gate for every SE handoff to
the G-owned GitHub workflows. It is a runtime prerequisite, not a plugin
installation or maintenance procedure.

This gate is surface-agnostic. It must not classify App versus CLI or infer a
surface from any dependency result. A consumer that separately needs surface
classification must use the
[Codex runtime surface contract](codex-runtime-surface.md); passing or failing
this gate never changes that authoritative result.

## When to run

For Learn, do not load this gate: Learn has no hosted dependency. Idea runs it
before its first hosted read/write on the publish branch; Idea preview remains
local. Spec runs it before any hosted source read or GitHub save. A local
source preview or Markdown save needs no G workflow. A Markdown destination or
preview does not waive the gate for an explicitly admitted hosted source read.

Delivery Features always publishes through G, even when its selected spec was
saved as Markdown. Run the gate before its first authoritative GitHub repository,
issue, PR, review, CI, or relation read. Passing establishes availability for
the next focused handoff; it does not broaden source or mutation authority.
Review PR runs this gate before hosted access. Its default invocation authorizes
requesting and waiting for a missing explicit review; audit-only scope remains
read-only. It does not authorize or own any other hosted action. Explicit SE
invocation authorizes only the writes required by its selected workflow and
consistent with caller constraints.

Deliver runs this gate before hosted access in the orchestrator and each worker.
Require only G workflows used by the selected source reads, local Git,
publication/readiness, required CI, and optional stacks or requested reviews.
A missing optional review workflow does not block ordinary Deliver. Explicit
no-push constraints remove publication authority, not permission for admitted
read-only source/CI inspection. Deliver's ready transition is explicitly owned by its entrypoint and uses G's
network/gh preflight with the supported GitHub CLI operation, because Send
excludes readiness. This admitted operation is not a fallback for missing G
publication or CI workflows. This does not change Deliver Features' gates.

## Required evidence

Establish all of the following from the current host:

- the Codex runtime can resolve the exact G plugin identity;
- the exact repo-local G plugin identity `g@alemar11` is the one being
  resolved;
- that plugin is installed and enabled;
- its declared source root is present and internally consistent;
- every bundled G workflow required by the invoking SE path is present and
  resolvable;
- the explicit handoff is exposed to and reachable from the current session
  without using a compatibility alias.

Installed and enabled state plus source resolvability are necessary local
evidence, not proof of current-session reachability. Do not infer full
availability from those facts alone, a display name, an installed cache
directory, historical task output, or an unrelated GitHub connector. Do not
require source and installed versions to match as part of this gate. When local
checks pass but the current session cannot reach the explicit handoff, report
`codex-dependency-unresolved`.

Idea and Spec hosted operations require `$g:github-issues` for issue
lifecycle and relationships. Optional classification uses that skill's
classification branch; classification failure never blocks semantic save.
Spec's approved delivery-marker creation, application or revocation uses the
same issue lifecycle owner. A required marker failure leaves that authorization
change incomplete even when semantic save succeeded.

Review PR requires only the hosted review owner's inspection, request, wait and
reconciliation operations. It does not use publication, local Git, issue, stack,
CI, finding-repair, reply/resolution, or merge-policy workflows.

For Delivery Features, the required workflow set includes the G
owners needed by the selected publication, review, CI, issue, local Git, and
stack paths. The delivery-status workflow plus branch-protection, ruleset,
mergeability-policy, merge-queue, auto-merge, and provider-policy inspection
are not required and must not be added to the dependency gate. A generic
GitHub read or raw provider call is not a substitute for the focused typed
workflow that owns the evidence being collected.

## Blocking outcomes

Fail closed before hosted access and report the observed evidence using one of
these lower-kebab outcomes:

- `codex-runtime-error`: the host capability inspection cannot be trusted;
- `plugin-missing`: the exact G plugin is not installed;
- `plugin-disabled`: the exact plugin exists but is disabled;
- `skill-unresolvable`: the plugin root or a required G workflow is missing or
  malformed;
- `codex-dependency-unresolved`: the explicit G handoff fails after local
  availability checks pass.

Never install, enable, refresh, remove, or substitute the dependency. A manual
remediation suggestion may be reported, but it is outside this workflow's
authority. Never fall back to direct provider calls.
