# Star-list Membership Results

These are transient per-target helper results, not persisted workflow state.
Each attempt returns one result; a later reconciled attempt has its own result.

| `status` | Meaning |
| --- | --- |
| `noop` | The observed state already satisfies the requested membership operation. |
| `dry-run` | Reads completed; the proposed membership change was not sent. |
| `changed` | The provider accepted the membership update; independent readback is still required. |
| `error` | Target resolution, eligibility, or update failed; reconcile possible effects before retrying. |

A batch can contain both successful and failed targets. The existing helper
result keys, including `targetCount`, `successCount`, and `failureCount`, retain
their public camelCase spelling. These are execution facts, not configuration.
Direct `gh` workflows report observed evidence without this helper envelope.
