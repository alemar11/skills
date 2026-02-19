# Monitoring and Diagnostics Best Practices

Use these checks continuously in production, not only during incidents.

## 1) Start with `EXPLAIN (ANALYZE, BUFFERS)`
Use measured execution plans to diagnose slow SQL before changing indexes/config.

```sql
explain (analyze, buffers)
select * from orders where customer_id = 123 and status = 'pending';
```

## 2) Track workload with `pg_stat_statements`
Identify expensive/frequent query fingerprints and prioritize by total impact.

```sql
create extension if not exists pg_stat_statements;

select query, calls, mean_exec_time, total_exec_time
from pg_stat_statements
order by total_exec_time desc
limit 20;
```

## 3) Monitor autovacuum/analyze health
Watch stale stats and dead tuples to avoid planner drift and table bloat.

```sql
select relname, n_live_tup, n_dead_tup, last_autovacuum, last_autoanalyze
from pg_stat_user_tables
order by n_dead_tup desc;
```

## 4) Inspect lock and activity views
Find long transactions, blocked sessions, and lock chains early.

```sql
select pid, state, wait_event_type, wait_event, now() - xact_start as xact_age
from pg_stat_activity
where state <> 'idle';
```

## 5) Review index usage and churn periodically
Remove unused indexes and validate index effectiveness over time.

```sql
select schemaname, relname as table_name, indexrelname as index_name, idx_scan
from pg_stat_user_indexes
order by idx_scan asc;
```

## 6) Enable slow-query and lock-wait logging
Capture slow SQL and lock waits in logs so intermittent production issues are diagnosable.

```sql
alter system set log_min_duration_statement = '250ms';
alter system set log_lock_waits = on;
alter system set deadlock_timeout = '200ms';
select pg_reload_conf();
```

## Verification References
- https://www.postgresql.org/docs/current/using-explain.html
- https://www.postgresql.org/docs/current/pgstatstatements.html
- https://www.postgresql.org/docs/current/routine-vacuuming.html
- https://www.postgresql.org/docs/current/monitoring-stats.html
- https://www.postgresql.org/docs/current/monitoring-locks.html
- https://www.postgresql.org/docs/current/runtime-config-logging.html
- https://www.postgresql.org/docs/current/runtime-config-locks.html
