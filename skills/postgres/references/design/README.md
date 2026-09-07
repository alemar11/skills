# Postgres Design Best Practices

This category contains generic, vendor-neutral PostgreSQL design and operations
guidance. Extension-specific guidance lives in `../extensions/`.

## First-Pass Review Checklist

Use this quick pass before a deeper schema, migration, or performance review:

- Schema shape: invariants are enforced with constraints, data types match domain semantics, nullable uniqueness is intentional, and foreign-key columns are indexed.
- Query shape: high-frequency filters, joins, sorts, and pagination paths have matching indexes and are validated with `EXPLAIN (ANALYZE, BUFFERS)`.
- Operational risk: migrations avoid long blocking locks, long transactions are visible, and destructive actions such as dropping indexes or partitions are explicitly confirmed.
- Access control: roles are least-privileged, broad `PUBLIC` grants are reviewed, RLS policy columns are indexed, and application traffic does not run as a bypass role.
- Diagnostics: slow queries, unused or invalid indexes, dead tuples, long transactions, and connection pressure have been checked before changing schema or configuration.
- Migration validation: every schema change has a pending migration, a cheap post-change verification query, and release handling through `../workflows/migration-guardrails.md`.

## Categories

- Query performance: [query-performance.md](query-performance.md)
- Connection management: [connection-management.md](connection-management.md)
- Security and RLS: [security-rls.md](security-rls.md)
- Schema design: [schema-design.md](schema-design.md)
- Concurrency and locking: [concurrency-locking.md](concurrency-locking.md)
- Data access patterns: [data-access-patterns.md](data-access-patterns.md)
- Monitoring and diagnostics: [monitoring-diagnostics.md](monitoring-diagnostics.md)
- Advanced features: [advanced-features.md](advanced-features.md)

## Usage
Use these references when writing SQL, designing schemas, reviewing migrations, or diagnosing production performance and concurrency issues.

For migration edits, read `../workflows/migration-guardrails.md`; add design
references only for the affected concern. A migration does not require every
design checklist.
