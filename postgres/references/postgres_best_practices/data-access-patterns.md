# Data Access Pattern Best Practices

These patterns improve throughput and reduce avoidable database work.

## 1) Batch writes instead of row-at-a-time loops
Use multi-row `INSERT` or `COPY` for bulk ingestion.

```sql
insert into events (user_id, action)
values (1, 'click'), (1, 'view'), (2, 'click');
```

## 2) Use `ON CONFLICT` for atomic upserts
Replace check-then-insert/update races with a single SQL statement.

```sql
insert into settings (user_id, key, value)
values (123, 'theme', 'dark')
on conflict (user_id, key)
do update set value = excluded.value;
```

## 3) Prefer keyset pagination for deep paging
`OFFSET` cost grows with page depth; keyset/cursor pagination remains stable.

```sql
select * from products
where (created_at, id) > ($1, $2)
order by created_at, id
limit 50;
```

## 4) Avoid N+1 query patterns
Join or batch related lookups rather than issuing one query per row at the application layer.

```sql
select u.id, u.name, o.total
from users u
left join orders o on o.user_id = u.id
where u.active = true;
```

## 5) Use parameterized queries/prepared statements
Parameterized SQL improves safety and can reduce parse/plan overhead for repeated query shapes.

## 6) Use `RETURNING` to avoid extra round trips
When a write needs to return generated IDs or updated values, use `RETURNING` in the same statement.

```sql
insert into orders (customer_id, total)
values ($1, $2)
returning id, created_at;
```

## Verification References
- https://www.postgresql.org/docs/current/sql-copy.html
- https://www.postgresql.org/docs/current/sql-insert.html
- https://www.postgresql.org/docs/current/queries-limit.html
- https://www.postgresql.org/docs/current/sql-prepare.html
- https://www.postgresql.org/docs/current/dml-returning.html
