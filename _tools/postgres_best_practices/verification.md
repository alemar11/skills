# Verification Matrix

This matrix documents how the regenerated best practices were validated.

## Scope
- Source pool: the top 5 `postgres` skills from `https://skills.sh` (snapshot in `top-postgres-skills.md`).
- Validation requirement: keep only generic PostgreSQL guidance and verify against official PostgreSQL docs.

## Rule Areas and Verification

| Area | Verified Against | Notes |
| --- | --- | --- |
| Index selection, multicolumn, partial, index-only scans | `indexes-*`, `using-explain` docs | Kept generic; removed provider-specific performance claims. |
| Connection behavior and limits | `runtime-config-connection`, `runtime-config-client`, `monitoring-stats` | Pooling retained as general pattern; no provider-only ports/services. |
| Roles, grants, RLS policies | `user-manag`, `sql-grant`, `sql-revoke`, `ddl-rowsecurity`, `sql-createpolicy` | Removed provider-specific auth helpers (for example `auth.uid()`). |
| Constraints, keys, partitioning, data types | `ddl-constraints`, `sql-createtable`, `datatype`, `ddl-partitioning` | Reworded strict “always/never” statements into conditional guidance. |
| Locking and concurrency | `mvcc`, `explicit-locking`, `sql-select#for-update-share`, advisory lock functions | Preserved `SKIP LOCKED` and advisory-lock usage patterns. |
| Data access patterns | `sql-copy`, `sql-insert`, `queries-limit`, `sql-prepare` | Preserved keyset pagination and `ON CONFLICT` upsert. |
| Monitoring and maintenance | `using-explain`, `pgstatstatements`, `routine-vacuuming`, `monitoring-*` | Focused on measurable diagnostics over fixed config recipes. |
| Advanced features | `textsearch-intro`, `datatype-json#json-indexing`, `pgtrgm`, `rangetypes`, generated columns docs | Kept portable feature usage; removed vendor platform APIs. |

## Exclusion Policy Applied
- Excluded vendor-platform workflows and SDK/API guidance (for example Neon platform APIs, Supabase-specific auth functions).
- Excluded opinionated numeric defaults not universally valid (`max_connections=...`, fixed memory formulas).
- Excluded non-portable extension assumptions unless clearly optional and PostgreSQL-native-compatible.
