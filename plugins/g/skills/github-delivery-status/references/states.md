# Delivery Status Interpretation

This reference owns the normalized delivery dispositions and attribution.
They are transient observations, with no persisted workflow state. GitHub
identity, lifecycle, HEAD, checks, reviews, rules, protection, and automation
remain external authoritative state; preserve their native values. A later
read can change any disposition and must establish its own evidence.

## Canonical dispositions

| Disposition | Meaning |
| --- | --- |
| `ready` | Open, non-draft PR; exact-head evidence is complete; GitHub can construct the merge and observed required gates are satisfied. |
| `ready-with-manual-action` | The ready conditions hold except that an active restricted-update rule leaves the branch update to an eligible human or provider actor. |
| `pending` | GitHub is calculating mergeability, or a required check/review is not yet complete. |
| `blocked` | A verified required gate fails, the PR is draft/not open, the candidate HEAD is stale, or strict policy requires a branch update. |
| `conflicting` | GitHub reports `CONFLICTING` mergeability or `DIRTY` merge state. |
| `unknown` | Evidence is unfamiliar, contradictory, incomplete, or cannot explain a provider block safely. |

An independently proven blocker or conflict can be reported despite unrelated
missing evidence; disclose those limits. Missing evidence, unfamiliar values,
or unresolved contradictions must never produce either ready disposition.
Do not confuse GitHub's literal `UNKNOWN` mergeability/merge-state value
(calculation pending) with a new, unrecognized enum (unknown interpretation).

## Required checks and reviews

Combine active rules and classic protection into effective requirements.
Retain each required check's name and any positive `integration_id` or
`app_id`; legacy name-only contexts must not weaken an app-specific requirement.
Distinct source-specific requirements remain distinct. Match app requirements
to `CheckRun.checkSuite.app.databaseId`, never a same-name foreign app or an
unattributed commit status. With no app requirement, evaluate every same-name
check run and commit status; a passing one does not erase a failing one.

For each required context:

- No matching result is pending only after the check inventory is complete.
- A completed check run passes on `SUCCESS`, `NEUTRAL`, or `SKIPPED`; it fails
  on `ACTION_REQUIRED`, `CANCELLED`, `FAILURE`, `STALE`, `STARTUP_FAILURE`, or
  `TIMED_OUT`. Recognized non-completed statuses are pending; unfamiliar
  statuses or conclusions are unknown.
- Commit statuses pass on `SUCCESS`, are pending on `EXPECTED`/`PENDING`, and
  fail on `ERROR`/`FAILURE`. Preserve unfamiliar values as unknown.
- Any required failure blocks; otherwise a pending required result is pending.
  Unknown required results preclude readiness. Non-required failures alone
  do not prove a blocked required gate.

Apply review count, code-owner, last-push approval, and conversation-resolution
requirements from active pull-request rules and classic protection. Use the
provider review decision for aggregate approval validity, including stale
approval rules; do not infer approval from raw review counts. Required
`CHANGES_REQUESTED` blocks; required `REVIEW_REQUIRED` or no approval yet is
pending. Unknown decisions are unknown. Required unresolved threads block;
otherwise unresolved comments remain findings without inventing a gate.

## Merge-state attribution

After identity/lifecycle, completeness, checks, and reviews are reconciled:

- `CLEAN` or `HAS_HOOKS` with `MERGEABLE` permits ready attribution only when
  required policy is understood and satisfied.
- `UNSTABLE` can be ready when every required gate passes: a non-required
  status failure is not a required-check blocker.
- `BEHIND` blocks when active strict status-check policy or classic protection's
  strict setting requires an up-to-date HEAD; otherwise it can be ready.
- `DRAFT` blocks. `UNKNOWN` calculation is pending. A recognized conflict is
  conflicting. Preserve other unfamiliar provider values as unknown.
- `BLOCKED` becomes `ready-with-manual-action` only with `MERGEABLE`, complete
  required-gate evidence, no failing/pending gates, and an active `update`
  restriction explaining the remaining boundary. Visible bypass actors are
  evidence about eligibility, not authority to act or proof that the viewer
  can bypass.

For restricted-update attribution, active `pull_request` and
`required_status_checks` rules must be accounted for. Rules for `creation`,
`deletion`, `non_fast_forward`, and `copilot_code_review` do not explain an
ordinary forward PR merge block. Any other rule needs verified applicability
and satisfaction; an unknown rule or unattributed block remains unknown.
Never infer that a hidden policy requirement is satisfied from green checks.

## Attribution and completeness

| Attribution | Meaning |
| --- | --- |
| `verified` | A ready, manual-action, blocked, or conflicting conclusion is fully supported without classification warnings. |
| `partial` | Pending/unknown interpretation, missing evidence, or warnings limit attribution. Collection can be complete while interpretation is partial. |

Record missing pages and unavailable surfaces individually. Inaccessible
active rules or ambiguous classic protection prevent verified readiness.
An inaccessible optional ruleset detail need not erase complete active-rule
parameters, but it cannot supply missing bypass or attribution evidence.
Missing review/check data is not an empty list; unavailable automation is not
proof it is disabled. Keep repository auto-merge capability, PR auto-merge
request, and queue entry outside the disposition: they neither authorize a
write nor independently block readiness.

A successful provider read can yield a non-ready disposition. A failed read
is an evidence failure; no command-specific JSON envelope or exit-code contract
is owned here.

For unfamiliar policy, consult GitHub's
[active branch rules](https://docs.github.com/en/rest/repos/rules),
[branch protection](https://docs.github.com/en/rest/branches/branch-protection),
and [ruleset rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets).
