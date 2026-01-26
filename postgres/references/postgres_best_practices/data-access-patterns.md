# Data Access Pattern Best Practices

Reduce round trips and improve query efficiency at the application layer.

## Batch inserts for bulk data
Prefer multi-row INSERT or COPY for large loads.

```sql
insert into events (user_id, action) values
  (1, 'click'),
  (1, 'view'),
  (2, 'click');

-- For large imports
copy events (user_id, action) from stdin with (format csv);
```

## Eliminate N+1 queries
Fetch related data in a single query.

```sql
select u.id, u.name, o.*
from users u
left join orders o on o.user_id = u.id
where u.active = true;
```

## Use cursor-based pagination
OFFSET grows linearly with page depth; keyset pagination stays O(1).

```sql
select * from products where id > $last_id order by id limit 20;
```

## Use UPSERT for insert-or-update
Avoid race conditions with `insert ... on conflict`.

```sql
insert into settings (user_id, key, value)
values (123, 'theme', 'dark')
on conflict (user_id, key)
do update set value = excluded.value;
```
