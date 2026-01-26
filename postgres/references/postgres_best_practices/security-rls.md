# Security & RLS Best Practices

Secure data access at the database layer and minimize privilege scope.

## Apply the principle of least privilege
Create roles with only the permissions required for their tasks.

```sql
create role app_readonly nologin;
grant usage on schema public to app_readonly;
grant select on public.products to app_readonly;

create role app_writer nologin;
grant usage on schema public to app_writer;
grant select, insert, update on public.orders to app_writer;

grant app_writer to app_user;
```

## Enable Row Level Security (RLS) for multi-tenant data
RLS enforces tenant isolation in the database, not just in application code.

```sql
alter table orders enable row level security;

create policy orders_user_policy on orders
  for all
  using (user_id = current_setting('app.current_user_id')::bigint);

alter table orders force row level security;

set app.current_user_id = '123';
select * from orders; -- Only orders for user 123
```

## Optimize RLS policy performance
Avoid per-row function calls and ensure indexed columns are used.

```sql
-- Evaluate the user context once
create policy orders_policy on orders
  using ((select current_setting('app.current_user_id')::bigint) = user_id);

-- Index columns referenced by policies
create index orders_user_id_idx on orders (user_id);
```

For complex checks, consider `security definer` helper functions that do indexed lookups, but keep them minimal and carefully audited.
