# Query Performance Best Practices

Focus on indexes and query patterns that avoid full table scans and unnecessary heap lookups.

## Add indexes on WHERE and JOIN columns
Unindexed filters and joins force sequential scans as tables grow.

```sql
-- Good: index the foreign key side used in WHERE/JOIN
create index orders_customer_id_idx on orders (customer_id);

select * from orders where customer_id = 123;
select c.name, o.total
from customers c
join orders o on o.customer_id = c.id;
```

## Create composite indexes for multi-column queries
Use one multi-column index that matches your common filter order.

```sql
-- Equality columns first, range columns last
create index orders_status_created_idx on orders (status, created_at);

select * from orders where status = 'pending' and created_at > '2024-01-01';
```

## Use covering indexes to enable index-only scans
Include non-filter columns so Postgres can satisfy the query from the index alone.

```sql
create index users_email_idx on users (email) include (name, created_at);
select email, name, created_at from users where email = 'user@example.com';
```

## Choose the right index type
Match index type to operator class and data shape.

```sql
-- B-tree: equality/range
create index users_created_idx on users (created_at);

-- GIN: arrays, JSONB, full-text
create index posts_tags_idx on posts using gin (tags);

-- BRIN: large time-series tables
create index events_time_idx on events using brin (created_at);
```

## Use partial indexes for filtered queries
Index only the rows you actually query.

```sql
create index users_active_email_idx on users (email)
where deleted_at is null;

select * from users
where email = 'user@example.com' and deleted_at is null;
```
