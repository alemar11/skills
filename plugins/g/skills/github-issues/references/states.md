# GitHub Issues State Contract

This reference owns transient dependency, classification, and taxonomy results.
No local workflow state is persisted. GitHub assignments, catalogs, issue
lifecycle, and relationships remain external provider state; temporary body
files are transport artifacts. `mutation_mode` and `issue_operation` belong to
the shared [G options](../../../references/options.md). Branch selection is
derived from the request, not stored configuration.

## Native dependency result

| Value | Meaning | Terminal |
| --- | --- | --- |
| `verified` | The authorized mutation completed and both reciprocal reads prove the requested edge state. | Yes |
| `no-op` | Both pre-reads already proved the exact requested edge state, so no mutation was attempted. | Yes |
| `failed` | GitHub definitively rejected the mutation. | Yes |
| `unavailable` | Capability, authentication, access, or target resolution prevented an operation attempt. | Yes |
| `unknown` | The mutation may have happened or reciprocal readback remains inconclusive after one bounded reread. | Yes |

Return exactly one value per native dependency invocation. Never replay an ambiguous mutation to
change `unknown`; the composing caller decides whether any non-success value
blocks its wider workflow.

## Classification Dispositions

`classification_disposition` is transient derived state.

| Value | Meaning |
| --- | --- |
| `complete-match` | Every requested classification dimension has one clear supported result. |
| `partial-match` | At least one label or type is clear, while another requested dimension is ambiguous, unavailable, or blocked. |
| `no-confident-match` | The relevant catalogs are readable, but no exact candidate is sufficiently supported. |
| `no-available-metadata` | The relevant catalogs were read successfully and contain no assignable classification values. |
| `metadata-unavailable` | A usable classification catalog could not be proven because capability, access, or provider reads are indeterminate. |

## Application Statuses

`application_status` is transient execution state.

| Value | Meaning |
| --- | --- |
| `not-applicable` | No safe metadata proposal exists, so no mutation can be previewed or applied. |
| `previewed` | At least one exact change was proposed and no mutation was attempted. |
| `unchanged` | The supported proposal already matches the issue, so no mutation was needed. |
| `applied` | Independent readback proves every attempted label and type change. |
| `partially-applied` | Independent readback proves at least one attempted change and at least one requested change remains unapplied. |
| `failed` | Independent readback proves that none of the attempted changes reached the issue. |

Do not persist or reuse either transient value across invocations. An uncertain
write has no terminal `application_status` until the exact issue is read back
and reconciled.

`application_status` applies only to issue classification.

## Taxonomy Dispositions

`taxonomy_disposition` is transient derived state used only for
taxonomy proposals.

| Value | Meaning |
| --- | --- |
| `proposal-ready` | At least one new label or issue-type definition is supported by recurring evidence and passes the gap and overlap checks. |
| `no-taxonomy-gap` | The examined evidence is adequately represented by the current taxonomy, so no addition is proposed. |
| `insufficient-evidence` | The visible corpus, repository evidence, or organization scope cannot justify a stable new taxonomy entry. |
| `metadata-unavailable` | No requested proposal dimension has a catalog complete enough for reliable collision and gap checks. A usable dimension may still yield `proposal-ready` while another is reported unavailable. |

Taxonomy proposals and dispositions are never persisted or treated as provider
state. This mode has no `application_status` because it performs no mutation.
