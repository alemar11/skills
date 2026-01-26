# Monitoring & Diagnostics Best Practices

Use built-in tools to identify slow queries and maintenance needs.

## Use EXPLAIN (ANALYZE, BUFFERS)
Inspect actual execution costs and IO behavior.

```sql
explain (analyze, buffers)
select * from orders where customer_id = 123 and status = 'pending';
```

Key signals:
- Seq Scan on large tables
- Rows Removed by Filter
- Buffers: read >> hit
- Sort Method: external merge

## Enable pg_stat_statements
Track the most expensive and frequent queries.

```sql
create extension if not exists pg_stat_statements;

select query, calls, mean_exec_time
from pg_stat_statements
order by mean_exec_time desc
limit 10;
```

## Keep statistics fresh with VACUUM and ANALYZE
Outdated stats lead to bad plans.

```sql
analyze orders;

alter table orders set (
  autovacuum_vacuum_scale_factor = 0.05,
  autovacuum_analyze_scale_factor = 0.02
);
```
