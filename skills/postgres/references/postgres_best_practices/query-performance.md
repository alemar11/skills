# Query Performance Best Practices

These rules are vendor-neutral and verified against PostgreSQL documentation.

## 1) Index real filter and join paths
Create indexes for columns used by high-frequency `WHERE`, `JOIN`, and sort predicates.

```sql
create index orders_customer_id_idx on orders (customer_id);

select * from orders where customer_id = 123;
select c.name, o.total
from customers c
join orders o on o.customer_id = c.id;
```

## 2) Design multicolumn indexes from query shape
Put equality predicates first, then range/sort columns (leftmost-prefix behavior).

```sql
create index orders_status_created_idx on orders (status, created_at);

select * from orders
where status = 'pending' and created_at >= now() - interval '7 days';
```

## 3) Use `INCLUDE` when index-only scans are realistic
For read-heavy lookups, include projected columns that are not search keys.

```sql
create index users_email_cover_idx on users (email) include (name, created_at);

select email, name, created_at
from users
where email = 'a@example.com';
```

## 4) Use partial indexes for stable predicates
If queries consistently filter a subset (for example active rows), index only that subset.

```sql
create index users_active_email_idx on users (email)
where deleted_at is null;
```

## 5) Match index type to operators
- B-tree: equality/range/order.
- GIN: arrays, JSONB containment, full-text.
- GiST: ranges/geometry/nearest-neighbor patterns.
- BRIN: very large, naturally ordered tables.

```sql
create index posts_tags_gin_idx on posts using gin (tags);
create index events_created_brin_idx on events using brin (created_at);
```

## 6) Validate with `EXPLAIN (ANALYZE, BUFFERS)`
Do not assume an index helped; verify actual row counts, access paths, and buffer behavior.

```sql
explain (analyze, buffers)
select * from orders where customer_id = 123 and status = 'pending';
```

## 7) Use extended statistics for correlated predicates
When filters on multiple columns are correlated, create extended statistics and run `ANALYZE` so row estimates are more accurate.

```sql
create statistics orders_status_region_stats (dependencies, ndistinct, mcv)
on status, region_id
from orders;

analyze orders;
```

## Verification References
- https://www.postgresql.org/docs/current/indexes-intro.html
- https://www.postgresql.org/docs/current/indexes-multicolumn.html
- https://www.postgresql.org/docs/current/indexes-index-only-scans.html
- https://www.postgresql.org/docs/current/indexes-partial.html
- https://www.postgresql.org/docs/current/indexes-types.html
- https://www.postgresql.org/docs/current/using-explain.html
- https://www.postgresql.org/docs/current/planner-stats.html
- https://www.postgresql.org/docs/current/sql-createstatistics.html
