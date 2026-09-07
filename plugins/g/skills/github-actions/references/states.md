# GitHub Actions Evidence States

Check/run lifecycle, conclusions, and `gh pr checks` buckets are external
provider facts, not persisted G workflow state. Preserve their native spelling;
G assigns no replacement result enum.

- Queued, waiting, requested, and in-progress work is pending evidence, not a
  pass. A completed run still needs its conclusion inspected.
- Failure, error, timeout, cancellation, and required action must remain
  distinguishable; skipped or neutral work is not proof that tests passed.
- A successful conclusion applies only to that check and SHA. Mixed results
  must retain failures and pending work instead of collapsing to success.
- A complete, successful read with no checks means none were reported. Failed,
  inaccessible, truncated, or unfamiliar results leave the relevant conclusion
  unknown.

Transitions are observed by rereading the provider. A rerun may introduce a new
attempt; a new commit changes the target. Do not carry a previous target's
conclusion forward as current evidence. Unknown provider values remain visible
and unresolved rather than being mapped to success.
